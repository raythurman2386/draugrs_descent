import pygame
from .scene import Scene
from managers import config, game_asset_manager
from utils.logger import GameLogger

logger = GameLogger.get_logger("main_menu")


class MainMenuScene(Scene):
    """Main menu scene for the game."""

    def __init__(self):
        super().__init__()

        # Menu options
        self.menu_options = [
            {"text": "Start Game", "action": "game"},
            {"text": "Options", "action": "options"},
            {"text": "Exit", "action": "exit"},
        ]
        self.selected_option = 0

        # UI theme from config
        self.ui_theme = config.get("ui", "default_theme", default="blue")
        self.load_ui_assets()

        # Start playing main menu music
        self.play_scene_music("main_menu")

    def load_ui_assets(self):
        """Load UI assets for the menu."""
        logger.debug(f"Loading UI assets with theme: {self.ui_theme}")

        # Load the panel and buttons
        self.panel = game_asset_manager.get_ui_element(f"{self.ui_theme}_panel.png", self.ui_theme)
        self.button_normal = game_asset_manager.get_ui_element(
            f"{self.ui_theme}_button00.png", self.ui_theme
        )
        self.button_hover = game_asset_manager.get_ui_element(
            f"{self.ui_theme}_button01.png", self.ui_theme
        )

        # Get screen dimensions
        screen_width = config.get("screen", "width", default=800)
        screen_height = config.get("screen", "height", default=600)

        # Get panel dimensions from config
        panel_width_ratio = config.get("ui", "main_menu", "panel", "width_ratio", default=0.4)
        panel_height_ratio = config.get("ui", "main_menu", "panel", "height_ratio", default=0.5)
        panel_width = int(screen_width * panel_width_ratio)
        panel_height = int(screen_height * panel_height_ratio)

        # Scale the panel to fit our menu needs based on config
        self.panel = pygame.transform.scale(self.panel, (panel_width, panel_height))

        # Calculate panel position
        self.panel_rect = self.panel.get_rect(center=(screen_width // 2, screen_height // 2))

        # Get button configuration from config
        button_width_ratio = config.get("ui", "main_menu", "buttons", "width_ratio", default=0.7)
        button_height = config.get("ui", "main_menu", "buttons", "height", default=45)
        button_spacing = config.get("ui", "main_menu", "buttons", "spacing", default=60)
        button_start_y = self.panel_rect.top + config.get(
            "ui", "main_menu", "buttons", "start_y_offset", default=100
        )

        # Scale buttons to fit better within the panel based on config
        button_width = int(panel_width * button_width_ratio)

        # Create button rects for collision detection
        self.button_rects = []

        for i in range(len(self.menu_options)):
            # Create a scaled button for this option
            button = pygame.transform.scale(
                self.button_normal if i != self.selected_option else self.button_hover,
                (button_width, button_height),
            )

            # Store the scaled versions
            if i == 0:
                self.scaled_button_normal = pygame.transform.scale(
                    self.button_normal, (button_width, button_height)
                )
                self.scaled_button_hover = pygame.transform.scale(
                    self.button_hover, (button_width, button_height)
                )

            # Create a rect for this button
            button_rect = button.get_rect(
                center=(self.panel_rect.centerx, button_start_y + i * button_spacing)
            )
            self.button_rects.append(button_rect)

        # Load button font based on config
        # Convert numeric font size to nearest size name
        button_font_size = config.get("ui", "main_menu", "buttons", "font_size", default=24)

        # Map numeric font size to closest pre-defined size name
        if button_font_size >= 36:
            size_name = "title"
        elif button_font_size >= 30:
            size_name = "heading"
        elif button_font_size >= 26:
            size_name = "normal"
        elif button_font_size >= 22:
            size_name = "ui"
        else:
            size_name = "small"

        self.button_font = game_asset_manager.get_font("default", size_name)

        logger.debug(f"Main menu UI assets loaded with {len(self.button_rects)} buttons")

    def handle_event(self, event):
        """Handle menu navigation and selection."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.menu_options)
                self.play_sound("menu_navigate")
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.menu_options)
                self.play_sound("menu_navigate")
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self.select_current_option()

        # Handle mouse events
        elif event.type == pygame.MOUSEMOTION:
            # Check if mouse is over any button
            mouse_pos = pygame.mouse.get_pos()
            for i, rect in enumerate(self.button_rects):
                if rect.collidepoint(mouse_pos):
                    if self.selected_option != i:
                        self.selected_option = i
                        self.play_sound("menu_navigate")
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                mouse_pos = pygame.mouse.get_pos()
                for i, rect in enumerate(self.button_rects):
                    if rect.collidepoint(mouse_pos):
                        self.selected_option = i
                        self.select_current_option()
                        break

    def select_current_option(self):
        """Execute the action for the currently selected option."""
        self.play_sound("button_click")
        action = self.menu_options[self.selected_option]["action"]
        if action == "exit":
            self.done = True
        else:
            # Make sure game is reset if starting a new game
            if action == "game" and self.scene_manager:
                game_scene = self.scene_manager.scenes.get("game")
                if game_scene:
                    # Always reset the game when starting from main menu
                    game_scene.reset()
                    # Ensure the game isn't paused
                    game_scene.paused = False
            elif action == "options" and self.scene_manager:
                # Set the previous scene to return to main menu
                options_scene = self.scene_manager.scenes.get("options")
                if options_scene:
                    options_scene.set_previous_scene("main_menu")
            self.switch_to_scene(action)

    def update(self):
        """Update menu logic."""
        pass

    def render(self):
        """Render the main menu."""
        screen_width = config.get("screen", "width", default=800)
        screen_height = config.get("screen", "height", default=600)

        # Fill the background with the configured color
        bg_color_name = config.get("ui", "main_menu", "background_color", default="dark_blue")
        bg_color = config.get_color(bg_color_name)
        self.screen.fill(bg_color)

        # Draw background panel
        self.screen.blit(self.panel, self.panel_rect)

        # Get title configuration
        title_y_offset = config.get("ui", "main_menu", "title", "y_offset", default=-40)
        title_color = config.get("ui", "main_menu", "title", "color", default="white")

        # Draw title
        title = self.title_font.render("Draugr's Descent", True, config.get_color(title_color))
        title_rect = title.get_rect(
            center=(screen_width // 2, self.panel_rect.top + title_y_offset)
        )
        self.screen.blit(title, title_rect)

        # Get button text color from config
        button_text_color = config.get("ui", "main_menu", "buttons", "text_color", default="white")

        # Draw menu options as buttons
        for i, option in enumerate(self.menu_options):
            # Choose button image based on selection
            button_img = (
                self.scaled_button_hover if i == self.selected_option else self.scaled_button_normal
            )

            # Draw the button
            button_rect = self.button_rects[i]
            self.screen.blit(button_img, button_rect)

            # Draw the button text
            text = self.button_font.render(
                option["text"], True, config.get_color(button_text_color)
            )
            text_rect = text.get_rect(center=button_rect.center)
            self.screen.blit(text, text_rect)
