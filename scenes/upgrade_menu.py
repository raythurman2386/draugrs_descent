import os
import sys
import pygame
from utils.logger import GameLogger
from scenes.scene import Scene
from managers import config, game_asset_manager, CurrencyManager
from ui.components import (
    draw_panel,
    draw_button,
    draw_selection_arrow,
    draw_progress_bar,
    draw_text_with_shadow,
    draw_info_box,
    draw_currency_display,
)

logger = GameLogger.get_logger("upgrade_menu")


class UpgradeMenuScene(Scene):
    """Upgrade menu scene for purchasing player upgrades."""

    def __init__(self):
        """Initialize the UpgradeMenuScene."""
        super().__init__()

        # Initialize with defaults that will be set properly when render is called
        self.currency_manager = None
        self.previous_scene = None

        # Get upgrade types from config
        self.upgrade_types = list(config.get("player", "upgrades", "types", default={}).keys())

        # State
        self.in_details_view = False
        self.selected_option = 0
        self.selected_upgrade = None

        # Load UI assets
        self.ui_theme = config.get("ui", "default theme", default="blue")
        self.load_ui_assets()

        # Sound names for navigation and purchase
        self.navigate_sound = "menu_navigate"
        self.purchase_sound = "powerup"
        self.error_sound = "menu_error"

        logger.info("UpgradeMenuScene initialized")

    def load_ui_assets(self):
        """Load UI assets for the upgrade menu."""
        logger.debug(f"Loading UI assets with theme: {self.ui_theme}")

        # Get screen dimensions
        screen_width = config.get("screen", "width", default=800)
        screen_height = config.get("screen", "height", default=600)

        # Panel dimensions - make responsive to screen size
        panel_width = int(min(screen_width * 0.8, 800))
        panel_height = int(min(screen_height * 0.85, 600))

        # Center the panel
        self.panel_rect = pygame.Rect(
            (screen_width - panel_width) // 2,
            (screen_height - panel_height) // 2,
            panel_width,
            panel_height,
        )

        # Load panel background
        self.panel = game_asset_manager.get_ui_element(f"{self.ui_theme}_panel.png", self.ui_theme)
        if not self.panel:
            # Fallback to creating a simple surface
            self.panel = pygame.Surface((panel_width, panel_height))
            self.panel.fill(config.get_color("light_blue"))
        else:
            self.panel = pygame.transform.scale(self.panel, (panel_width, panel_height))

        # Load button images
        button_normal = game_asset_manager.get_ui_element(
            f"{self.ui_theme}_button00.png", self.ui_theme
        )
        button_hover = game_asset_manager.get_ui_element(
            f"{self.ui_theme}_button01.png", self.ui_theme
        )
        button_disabled = game_asset_manager.get_ui_element(
            f"{self.ui_theme}_button_disabled.png", self.ui_theme
        )

        # Handle missing button assets with fallbacks
        if not button_normal:
            button_normal = pygame.Surface((200, 50))
            button_normal.fill(config.get_color("light_blue"))

        if not button_hover:
            button_hover = pygame.Surface((200, 50))
            button_hover.fill(config.get_color("cyan"))

        if not button_disabled:
            # Create a grayscale version of the normal button for disabled state
            button_disabled = button_normal.copy()
            disabled_surface = pygame.Surface(button_disabled.get_size(), flags=pygame.SRCALPHA)
            disabled_surface.fill((100, 100, 100, 128))
            button_disabled.blit(disabled_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # Calculate button dimensions based on panel size
        button_width = int(panel_width * 0.7)
        button_height = int(panel_height * 0.08)

        # Scale buttons
        self.scaled_button_normal = pygame.transform.scale(
            button_normal, (button_width, button_height)
        )
        self.scaled_button_hover = pygame.transform.scale(
            button_hover, (button_width, button_height)
        )
        self.scaled_button_disabled = pygame.transform.scale(
            button_disabled, (button_width, button_height)
        )

        # Get font sizes proportional to screen size
        title_size = int(min(screen_height * 0.06, 48))
        heading_size = int(min(screen_height * 0.04, 32))
        button_size = int(min(screen_height * 0.035, 28))
        info_size = int(min(screen_height * 0.025, 22))
        small_size = int(min(screen_height * 0.02, 16))

        # Load fonts
        self.title_font = game_asset_manager.get_font("default", "title")
        self.heading_font = game_asset_manager.get_font("default", "heading")
        self.button_font = game_asset_manager.get_font("default", "ui")
        self.info_font = game_asset_manager.get_font("default", "info")
        self.small_font = game_asset_manager.get_font("default", "small")

        # Button spacing
        self.button_spacing = int(panel_height * 0.02)

        logger.debug("Upgrade menu UI assets loaded")

    def set_currency_manager(self, currency_manager):
        """Set the currency manager for the upgrade menu."""
        self.currency_manager = currency_manager

    def set_previous_scene(self, scene_name):
        """Set the previous scene to return to."""
        self.previous_scene = scene_name

    def handle_event(self, event):
        """Handle user input events."""
        if event.type == pygame.KEYDOWN:
            if not self.in_details_view:
                self.handle_main_menu_key(event)
            else:
                self.handle_upgrade_details_key(event)

        elif event.type == pygame.MOUSEMOTION:
            if not self.in_details_view:
                self.handle_main_menu_mouse_motion(event)
            else:
                self.handle_upgrade_details_mouse_motion(event)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if not self.in_details_view:
                self.handle_main_menu_mouse_button(event)
            else:
                self.handle_upgrade_details_mouse_button(event)

    def process_events(self, events):
        """Process all events and return True if we need to exit."""
        for event in events:
            if event.type == pygame.QUIT:
                return True
            self.handle_event(event)
        return False

    def handle_main_menu_key(self, event):
        """Handle key presses for the main upgrade menu."""
        total_options = len(self.upgrade_types) + 1  # +1 for back button

        if event.key == pygame.K_UP:
            self.selected_option = (self.selected_option - 1) % total_options
            self.play_sound("menu_navigate")
        elif event.key == pygame.K_DOWN:
            self.selected_option = (self.selected_option + 1) % total_options
            self.play_sound("menu_navigate")
        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
            self.select_main_menu_option()
        elif event.key == pygame.K_ESCAPE:
            self.switch_to_scene(self.previous_scene)

    def handle_upgrade_details_key(self, event):
        """Handle key presses for the upgrade details screen."""
        if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
            self.purchase_upgrade()
        elif event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
            self.in_details_view = False
            self.play_sound("menu_navigate")

    def handle_main_menu_mouse_motion(self, event):
        """Handle mouse motion in the main upgrade menu."""
        mouse_pos = pygame.mouse.get_pos()
        for i in range(len(self.upgrade_types) + 1):  # +1 for back button
            button_rect = self.get_button_rect(i)
            if button_rect.collidepoint(mouse_pos):
                if self.selected_option != i:
                    self.selected_option = i
                    self.play_sound("menu_navigate")
                break

    def handle_upgrade_details_mouse_motion(self, event):
        """Handle mouse motion in the upgrade details screen."""
        mouse_pos = pygame.mouse.get_pos()
        purchase_rect = self.get_purchase_button_rect()
        back_rect = self.get_back_button_rect()

        if purchase_rect.collidepoint(mouse_pos):
            self.selected_option = 0  # Purchase button
        elif back_rect.collidepoint(mouse_pos):
            self.selected_option = 1  # Back button

    def handle_main_menu_mouse_button(self, event):
        """Handle mouse clicks in the main upgrade menu."""
        if event.button == 1:  # Left mouse button
            mouse_pos = pygame.mouse.get_pos()
            for i in range(len(self.upgrade_types) + 1):  # +1 for back button
                button_rect = self.get_button_rect(i)
                if button_rect.collidepoint(mouse_pos):
                    self.selected_option = i
                    self.select_main_menu_option()
                    break

    def handle_upgrade_details_mouse_button(self, event):
        """Handle mouse clicks in the upgrade details screen."""
        if event.button == 1:  # Left mouse button
            mouse_pos = pygame.mouse.get_pos()
            purchase_rect = self.get_purchase_button_rect()
            back_rect = self.get_back_button_rect()

            if purchase_rect.collidepoint(mouse_pos):
                self.purchase_upgrade()
            elif back_rect.collidepoint(mouse_pos):
                self.in_details_view = False
                self.play_sound("menu_navigate")

    def select_main_menu_option(self):
        """Handle selection in the main upgrade menu."""
        # Last option is always 'Back'
        if self.selected_option == len(self.upgrade_types):
            self.play_sound("button_click")
            self.switch_to_scene(self.previous_scene)
        else:
            # Selected an upgrade option
            self.play_sound("menu_navigate")
            self.selected_upgrade = self.upgrade_types[self.selected_option]
            self.in_details_view = True
            self.selected_option = 0  # Reset selection for the details screen

    def purchase_upgrade(self):
        """Attempt to purchase the currently selected upgrade."""
        if not self.selected_upgrade:
            return

        upgrade_config = config.get(
            "player", "upgrades", "types", self.selected_upgrade, default={}
        )
        max_level = upgrade_config.get("max_level", 5)
        current_level = self.currency_manager.get_upgrade_level(self.selected_upgrade)

        # Check if already at max level
        if current_level >= max_level:
            self.play_sound("menu_error")
            logger.debug(f"Upgrade {self.selected_upgrade} already at max level")
            return

        # Calculate cost for the next level
        base_cost = upgrade_config.get("base_cost", 100)
        cost_multiplier = upgrade_config.get("cost_multiplier", 1.5)
        cost = int(base_cost * (cost_multiplier**current_level))

        # Attempt to purchase
        if self.currency_manager.upgrade(self.selected_upgrade, cost):
            self.play_sound("powerup")
            logger.info(f"Purchased {self.selected_upgrade} upgrade to level {current_level + 1}")
        else:
            # Not enough currency
            self.play_sound("menu_error")
            logger.debug(f"Not enough currency for {self.selected_upgrade} upgrade")

    def update(self):
        """Update menu logic."""
        pass

    def get_button_rect(self, index):
        """Get the rectangle for a button at the given index."""
        # Calculate starting Y position for the first button
        button_start_y = self.panel_rect.top + 100  # Offset from top of panel

        # Calculate button position
        button_y = button_start_y + index * self.button_spacing
        button_rect = pygame.Rect(
            self.panel_rect.centerx - self.scaled_button_normal.get_width() // 2,
            button_y,
            self.scaled_button_normal.get_width(),
            self.scaled_button_normal.get_height(),
        )
        return button_rect

    def get_purchase_button_rect(self):
        """Get the rectangle for the purchase button in the details screen."""
        button_y = self.panel_rect.centery + 80
        button_rect = pygame.Rect(
            self.panel_rect.centerx - self.scaled_button_normal.get_width() // 2,
            button_y,
            self.scaled_button_normal.get_width(),
            self.scaled_button_normal.get_height(),
        )
        return button_rect

    def get_back_button_rect(self):
        """Get the rectangle for the back button in the details screen."""
        button_y = self.panel_rect.centery + 140
        button_rect = pygame.Rect(
            self.panel_rect.centerx - self.scaled_button_normal.get_width() // 2,
            button_y,
            self.scaled_button_normal.get_width(),
            self.scaled_button_normal.get_height(),
        )
        return button_rect

    def render(self):
        """Render the upgrade menu."""
        # Initialize currency manager if not set
        if not self.currency_manager:
            self.currency_manager = CurrencyManager()
            logger.debug("Initialized default currency manager")

        # Fill the background
        bg_color = config.get_color("dark_blue")
        self.screen.fill(bg_color)

        # Draw the panel background
        self.screen.blit(self.panel, self.panel_rect)

        # Draw menu title with a slight shadow for better visibility
        title = self.title_font.render("Upgrades", True, config.get_color("dark_blue"))
        title_rect = title.get_rect(center=(self.panel_rect.centerx + 2, self.panel_rect.top + 42))
        self.screen.blit(title, title_rect)

        title = self.title_font.render("Upgrades", True, config.get_color("white"))
        title_rect = title.get_rect(center=(self.panel_rect.centerx, self.panel_rect.top + 40))
        self.screen.blit(title, title_rect)

        # Display current currency with gold color and shadow for emphasis
        currency_name = config.get("player", "upgrades", "currency", "name", default="Souls")
        currency_text = f"{currency_name}: {self.currency_manager.get_currency()}"

        # Shadow
        currency_shadow = self.heading_font.render(
            currency_text, True, config.get_color("dark_blue")
        )
        currency_shadow_rect = currency_shadow.get_rect(
            topright=(self.panel_rect.right - 18, self.panel_rect.top + 22)
        )
        self.screen.blit(currency_shadow, currency_shadow_rect)

        # Actual text
        currency_surf = self.heading_font.render(currency_text, True, config.get_color("gold"))
        currency_rect = currency_surf.get_rect(
            topright=(self.panel_rect.right - 20, self.panel_rect.top + 20)
        )
        self.screen.blit(currency_surf, currency_rect)

        # Render the appropriate menu
        if not self.in_details_view:
            self.render_main_menu()
        else:
            self.render_upgrade_details()

    def render_main_menu(self):
        """Render the main upgrade menu."""
        # Draw panel background
        draw_panel(self.screen, self.panel_rect)

        # Draw title with shadow
        draw_text_with_shadow(
            self.screen,
            "Upgrades",
            self.title_font,
            config.get_color("white"),
            config.get_color("dark_blue"),
            (self.panel_rect.centerx, self.panel_rect.top + 40),
            "center",
            (2, 2),
        )

        # Display current currency
        currency_name = config.get("player", "upgrades", "currency", "name", default="Souls")
        draw_currency_display(
            self.screen,
            (self.panel_rect.right - 20, self.panel_rect.top + 20),
            self.currency_manager.get_currency(),
            currency_name,
            "right",
        )

        # Calculate vertical spacing between buttons
        button_height = self.scaled_button_normal.get_height()
        total_buttons = len(self.upgrade_types) + 1  # +1 for back button

        # Calculate total space needed for buttons
        total_button_space = (
            total_buttons * button_height + (total_buttons - 1) * self.button_spacing
        )

        # Calculate starting Y position to center the button group in the panel
        available_height = self.panel_rect.height - 120  # Allow space for header and footer
        top_margin = (available_height - total_button_space) // 2
        button_start_y = self.panel_rect.top + 100 + top_margin

        # Draw upgrade buttons
        for i, upgrade_type in enumerate(self.upgrade_types):
            # Get upgrade info
            upgrade_config = config.get("player", "upgrades", "types", upgrade_type, default={})
            upgrade_name = upgrade_config.get("name", upgrade_type.capitalize())
            current_level = self.currency_manager.get_upgrade_level(upgrade_type)
            max_level = upgrade_config.get("max_level", 5)

            # Calculate button position
            button_rect = pygame.Rect(
                self.panel_rect.centerx - self.scaled_button_normal.get_width() // 2,
                button_start_y + i * (button_height + self.button_spacing),
                self.scaled_button_normal.get_width(),
                button_height,
            )

            # Draw the button
            is_selected = i == self.selected_option
            draw_button(
                self.screen,
                button_rect,
                f"{upgrade_name} - Level {current_level}/{max_level}",
                is_selected,
            )

            # Add navigation indicator arrow for selected option
            if is_selected:
                draw_selection_arrow(self.screen, button_rect)

        # Draw the Back button
        back_index = len(self.upgrade_types)
        back_rect = pygame.Rect(
            self.panel_rect.centerx - self.scaled_button_normal.get_width() // 2,
            button_start_y + back_index * (button_height + self.button_spacing),
            self.scaled_button_normal.get_width(),
            button_height,
        )

        # Draw the back button with text
        is_back_selected = back_index == self.selected_option
        draw_button(self.screen, back_rect, "Back to Main Menu", is_back_selected)

        # Add navigation indicator for back button if selected
        if is_back_selected:
            draw_selection_arrow(self.screen, back_rect)

        # Add keyboard navigation hint at the bottom
        hint_text = "Use Arrow Keys to Navigate, Enter to Select"
        hint_surf = self.small_font.render(hint_text, True, config.get_color("light_grey"))
        hint_rect = hint_surf.get_rect(
            center=(self.panel_rect.centerx, self.panel_rect.bottom - 20)
        )
        self.screen.blit(hint_surf, hint_rect)

    def render_upgrade_details(self):
        """Render the details screen for the selected upgrade."""
        if not self.selected_upgrade:
            return

        # Draw panel background
        draw_panel(self.screen, self.panel_rect)

        # Get upgrade configuration
        upgrade_config = config.get(
            "player", "upgrades", "types", self.selected_upgrade, default={}
        )
        upgrade_name = upgrade_config.get("name", self.selected_upgrade.capitalize())
        description = upgrade_config.get("description", "")
        current_level = self.currency_manager.get_upgrade_level(self.selected_upgrade)
        max_level = upgrade_config.get("max_level", 5)
        base_cost = upgrade_config.get("base_cost", 100)
        cost_multiplier = upgrade_config.get("cost_multiplier", 1.5)
        effect_per_level = upgrade_config.get("effect_per_level", 1)

        # Calculate upgrade cost
        next_level_cost = (
            int(base_cost * (cost_multiplier**current_level)) if current_level < max_level else 0
        )

        # Draw title with shadow
        title_y_pos = self.panel_rect.top + 40
        draw_text_with_shadow(
            self.screen,
            upgrade_name,
            self.heading_font,
            config.get_color("gold"),
            config.get_color("dark_blue"),
            (self.panel_rect.centerx, title_y_pos),
            "center",
            (2, 2),
        )

        # Display current currency
        currency_name = config.get("player", "upgrades", "currency", "name", default="Souls")
        draw_currency_display(
            self.screen,
            (self.panel_rect.right - 20, self.panel_rect.top + 20),
            self.currency_manager.get_currency(),
            currency_name,
            "right",
        )

        # Draw description - position below the title with proper spacing
        description_y = title_y_pos + 60
        draw_text_with_shadow(
            self.screen,
            description,
            self.info_font,
            config.get_color("white"),
            config.get_color("dark_blue"),
            (self.panel_rect.centerx, description_y),
            "center",
            (1, 1),
        )

        # Draw info box for upgrade stats - centered in the panel with proper spacing
        stats_box_width = int(self.panel_rect.width * 0.85)
        stats_box_height = int(self.panel_rect.height * 0.3)
        stats_box_rect = pygame.Rect(
            self.panel_rect.centerx - stats_box_width // 2,
            description_y + 50,
            stats_box_width,
            stats_box_height,
        )
        draw_info_box(self.screen, stats_box_rect)

        # Draw current level with progress bar
        level_y = stats_box_rect.top + 30
        level_text = f"Level: {current_level}/{max_level}"
        level_x = stats_box_rect.left + 30

        # Draw level text
        level_rect = self.info_font.render(level_text, True, config.get_color("white")).get_rect(
            midleft=(level_x, level_y)
        )
        self.screen.blit(
            self.info_font.render(level_text, True, config.get_color("white")), level_rect
        )

        # Draw progress bar for level - positioned next to the level text
        progress_width = int(stats_box_width * 0.5)
        progress_height = 12
        progress_rect = pygame.Rect(
            level_rect.right + 30, level_y - progress_height // 2, progress_width, progress_height
        )
        draw_progress_bar(self.screen, progress_rect, current_level, max_level)

        # Draw effect text
        effect_y = level_y + 40
        effect_text = self.get_effect_text(self.selected_upgrade, effect_per_level)
        effect_rect = self.info_font.render(effect_text, True, config.get_color("white")).get_rect(
            midleft=(level_x, effect_y)
        )
        self.screen.blit(
            self.info_font.render(effect_text, True, config.get_color("white")), effect_rect
        )

        # Draw cost or max level text
        cost_y = effect_y + 40
        if current_level < max_level:
            # Change color based on affordability
            cost_color = config.get_color("white")
            cost_suffix = ""

            if next_level_cost > self.currency_manager.get_currency():
                cost_color = config.get_color("red")
                cost_suffix = " (Not Enough Souls)"

            cost_text = f"Upgrade Cost: {next_level_cost} Souls{cost_suffix}"
            cost_surf = self.info_font.render(cost_text, True, cost_color)
            cost_rect = cost_surf.get_rect(midleft=(level_x, cost_y))
            self.screen.blit(cost_surf, cost_rect)
        else:
            # Maximum level reached
            max_text = "MAXIMUM LEVEL REACHED"
            max_surf = self.info_font.render(max_text, True, config.get_color("gold"))
            max_rect = max_surf.get_rect(midleft=(level_x, cost_y))
            self.screen.blit(max_surf, max_rect)

        # Calculate positions for buttons with proper spacing
        button_height = self.scaled_button_normal.get_height()
        button_spacing = self.button_spacing

        # Space remaining for buttons
        remaining_height = self.panel_rect.bottom - stats_box_rect.bottom - 70

        # Calculate y positions for buttons to be centered in the remaining space
        button_start_y = (
            stats_box_rect.bottom + (remaining_height - 2 * button_height - button_spacing) // 2
        )

        # Draw purchase button
        purchase_rect = pygame.Rect(
            self.panel_rect.centerx - self.scaled_button_normal.get_width() // 2,
            button_start_y,
            self.scaled_button_normal.get_width(),
            button_height,
        )

        # Determine if button should be enabled
        button_enabled = (
            current_level < max_level and next_level_cost <= self.currency_manager.get_currency()
        )

        # Draw purchase button using component
        draw_button(
            self.screen,
            purchase_rect,
            "Purchase Upgrade",
            self.selected_option == 0,
            # not button_enabled
        )

        # Draw arrow indicator if selected
        if self.selected_option == 0:
            draw_selection_arrow(self.screen, purchase_rect)

        # Draw back button
        back_rect = pygame.Rect(
            self.panel_rect.centerx - self.scaled_button_normal.get_width() // 2,
            purchase_rect.bottom + button_spacing,
            self.scaled_button_normal.get_width(),
            button_height,
        )

        # Draw back button using component
        draw_button(self.screen, back_rect, "Back", self.selected_option == 1)

        # Draw arrow indicator if selected
        if self.selected_option == 1:
            draw_selection_arrow(self.screen, back_rect)

        # Add keyboard navigation hint at the bottom
        hint_text = "Use Up/Down to Navigate, Enter to Select"
        hint_surf = self.small_font.render(hint_text, True, config.get_color("light_grey"))
        hint_rect = hint_surf.get_rect(
            center=(self.panel_rect.centerx, self.panel_rect.bottom - 20)
        )
        self.screen.blit(hint_surf, hint_rect)

    def get_effect_text(self, upgrade_type, effect_per_level):
        """Get descriptive text about an upgrade's effect."""
        if upgrade_type == "health":
            return f"Effect: +{effect_per_level} Health per level"
        elif upgrade_type == "speed":
            return f"Effect: +{effect_per_level} Movement Speed per level"
        elif upgrade_type == "fire_rate":
            return f"Effect: -{effect_per_level}ms Shot Cooldown per level"
        elif upgrade_type == "damage":
            return f"Effect: +{effect_per_level} Damage per level"
        elif upgrade_type == "crit_chance":
            return f"Effect: +{effect_per_level * 100}% Critical Chance per level"
        elif upgrade_type == "crit_multiplier":
            return f"Effect: +{effect_per_level * 100}% Critical Damage per level"
        else:
            return f"Effect: +{effect_per_level} per level"
