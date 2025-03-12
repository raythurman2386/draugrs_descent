"""Common UI components for game scenes.

This module provides reusable UI components to maintain consistent styling across
all game scenes.
"""

import pygame
from managers import config
from utils.logger import GameLogger

logger = GameLogger.get_logger("ui_components")


def draw_panel(surface, rect, theme="blue"):
    """Draw a standard panel with the given theme.

    Args:
        surface: pygame surface to draw on
        rect: rectangle defining the panel dimensions
        theme: UI theme name (default: "blue")

    Returns:
        The panel surface
    """
    # Get panel from assets
    from managers import game_asset_manager

    panel = game_asset_manager.get_ui_element(f"{theme}_panel.png", theme)

    # Scale panel to fit rect
    scaled_panel = pygame.transform.scale(panel, (rect.width, rect.height))

    # Draw to surface
    surface.blit(scaled_panel, rect)

    return scaled_panel


def draw_button(surface, rect, text, is_selected=False, is_disabled=False, theme="blue"):
    """Draw a standard button with text.

    Args:
        surface: pygame surface to draw on
        rect: rectangle defining the button dimensions
        text: text to display on the button
        is_selected: whether the button is selected/hovered
        is_disabled: whether the button is disabled
        theme: UI theme name (default: "blue")

    Returns:
        Tuple of (button_surface, text_rect)
    """
    from managers import game_asset_manager

    # Determine button state
    state = "disabled" if is_disabled else ("hover" if is_selected else "normal")

    # Get appropriate button image
    if state == "disabled":
        button_img = game_asset_manager.get_ui_element(f"{theme}_button_disabled.png", theme)
    elif state == "hover":
        button_img = game_asset_manager.get_ui_element(f"{theme}_button01.png", theme)
    else:
        button_img = game_asset_manager.get_ui_element(f"{theme}_button00.png", theme)

    # Scale button
    scaled_button = pygame.transform.scale(button_img, (rect.width, rect.height))

    # Draw button
    surface.blit(scaled_button, rect)

    # Determine text color
    if state == "disabled":
        text_color = config.get_color("dark_grey")
    else:
        text_color = config.get_color("white")

    # Get font and render text
    button_font = game_asset_manager.get_font("default", "ui")
    text_surf = button_font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)

    # Draw text
    surface.blit(text_surf, text_rect)

    return scaled_button, text_rect


def draw_selection_arrow(surface, target_rect, color=(255, 215, 0)):
    """Draw a selection arrow pointing to a UI element.

    Args:
        surface: pygame surface to draw on
        target_rect: rectangle of the element the arrow points to
        color: RGB color tuple for the arrow
    """
    arrow_x = target_rect.left - 20
    arrow_y = target_rect.centery
    arrow_points = [(arrow_x, arrow_y), (arrow_x + 12, arrow_y - 8), (arrow_x + 12, arrow_y + 8)]
    pygame.draw.polygon(surface, color, arrow_points)


def draw_progress_bar(
    surface,
    rect,
    value,
    max_value,
    bg_color="dark_grey",
    fill_color="gold",
    border_color="light_grey",
    border_width=1,
    radius=3,
):
    """Draw a progress bar.

    Args:
        surface: pygame surface to draw on
        rect: rectangle defining the progress bar dimensions
        value: current value
        max_value: maximum value
        bg_color: background color name
        fill_color: fill color name
        border_color: border color name
        border_width: border width in pixels
        radius: corner radius
    """
    # Draw background
    pygame.draw.rect(surface, config.get_color(bg_color), rect, 0, radius)

    # Draw fill
    if max_value > 0 and value > 0:
        fill_width = int(rect.width * (value / max_value))
        if fill_width > 0:
            fill_rect = pygame.Rect(rect.left, rect.top, fill_width, rect.height)
            pygame.draw.rect(surface, config.get_color(fill_color), fill_rect, 0, radius)

    # Draw border
    pygame.draw.rect(surface, config.get_color(border_color), rect, border_width, radius)


def draw_text_with_shadow(
    surface, text, font, color, shadow_color, position, align="left", shadow_offset=(2, 2)
):
    """Draw text with a shadow effect.

    Args:
        surface: pygame surface to draw on
        text: text to display
        font: pygame font object
        color: RGB color tuple for text
        shadow_color: RGB color tuple for shadow
        position: (x, y) position tuple
        align: text alignment ('left', 'center', 'right')
        shadow_offset: (x, y) offset for shadow

    Returns:
        The text rectangle
    """
    # Create text surfaces
    shadow_surf = font.render(text, True, shadow_color)
    text_surf = font.render(text, True, color)

    # Position shadow
    if align == "center":
        shadow_rect = shadow_surf.get_rect(
            center=(position[0] + shadow_offset[0], position[1] + shadow_offset[1])
        )
    elif align == "right":
        shadow_rect = shadow_surf.get_rect(
            topright=(position[0] + shadow_offset[0], position[1] + shadow_offset[1])
        )
    else:  # left
        shadow_rect = shadow_surf.get_rect(
            topleft=(position[0] + shadow_offset[0], position[1] + shadow_offset[1])
        )

    # Position text
    if align == "center":
        text_rect = text_surf.get_rect(center=position)
    elif align == "right":
        text_rect = text_surf.get_rect(topright=position)
    else:  # left
        text_rect = text_surf.get_rect(topleft=position)

    # Draw shadow and text
    surface.blit(shadow_surf, shadow_rect)
    surface.blit(text_surf, text_rect)

    return text_rect


def draw_info_box(
    surface, rect, border_color="blue", bg_color="dark_blue", border_width=2, radius=8
):
    """Draw an info box for displaying information.

    Args:
        surface: pygame surface to draw on
        rect: rectangle defining the box dimensions
        border_color: border color name
        bg_color: background color name
        border_width: border width in pixels
        radius: corner radius
    """
    # Draw background
    pygame.draw.rect(surface, config.get_color(bg_color), rect, 0, radius)

    # Draw border
    pygame.draw.rect(surface, config.get_color(border_color), rect, border_width, radius)


def draw_currency_display(surface, position, currency_value, currency_name="Souls", align="right"):
    """Draw a currency display with gold color and shadow.

    Args:
        surface: pygame surface to draw on
        position: (x, y) position tuple
        currency_value: amount of currency to display
        currency_name: name of the currency
        align: alignment ('left', 'center', 'right')

    Returns:
        The currency display rectangle
    """
    from managers import game_asset_manager

    # Format currency text
    currency_text = f"{currency_name}: {currency_value}"

    # Get heading font
    heading_font = game_asset_manager.get_font("default", "heading")

    # Draw with shadow
    return draw_text_with_shadow(
        surface,
        currency_text,
        heading_font,
        config.get_color("gold"),
        config.get_color("dark_blue"),
        position,
        align,
    )
