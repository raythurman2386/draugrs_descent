import pygame
from .scene import Scene
from managers import config, game_asset_manager
from utils.logger import GameLogger

logger = GameLogger.get_logger("pause_menu")


class PauseMenuScene(Scene):
    """Pause menu scene."""

    def __init__(self):
        super().__init__()

        # Menu options
        self.menu_options = [
            {"text": "Resume", "action": "game"},
            {"text": "Options", "action": "options"},
            {"text": "Main Menu", "action": "main_menu"},
            {"text": "Exit", "action": "exit"},
        ]
        self.selected_option = 0

        # UI theme from config
        self.ui_theme = config.get("ui", "default_theme", default="blue")
        self.load_ui_assets()

        # Create a semi-transparent overlay
        screen_width = config.get("screen", "width", default=800)
        screen_height = config.get("screen", "height", default=600)
        overlay_color = config.get("ui", "pause_menu", "overlay_color", default=[0, 0, 0, 128])
        
        self.overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        self.overlay.fill(tuple(overlay_color))  # Black with opacity

        # Start playing pause menu music
        self.play_scene_music("pause")

    def load_ui_assets(self):
        """Load UI assets for the menu."""
        logger.debug(f"Loading pause menu UI assets with theme: {self.ui_theme}")
        
        # Load the panel and buttons
        self.panel = game_asset_manager.get_ui_element(f"{self.ui_theme}_panel.png", self.ui_theme)
        self.button_normal = game_asset_manager.get_ui_element(f"{self.ui_theme}_button00.png", self.ui_theme)
        self.button_hover = game_asset_manager.get_ui_element(f"{self.ui_theme}_button01.png", self.ui_theme)
        
        # Get screen dimensions
        screen_width = config.get("screen", "width", default=800)
        screen_height = config.get("screen", "height", default=600)
        
        # Get panel dimensions from config
        panel_width_ratio = config.get("ui", "pause_menu", "panel", "width_ratio", default=0.4)
        panel_height_ratio = config.get("ui", "pause_menu", "panel", "height_ratio", default=0.6)
        panel_width = int(screen_width * panel_width_ratio)
        panel_height = int(screen_height * panel_height_ratio)
        
        # Scale the panel to fit our menu needs based on config
        self.panel = pygame.transform.scale(self.panel, (panel_width, panel_height))
        
        # Calculate panel position
        self.panel_rect = self.panel.get_rect(center=(screen_width // 2, screen_height // 2))
        
        # Get button configuration from config
        button_width_ratio = config.get("ui", "pause_menu", "buttons", "width_ratio", default=0.7)
        button_height = config.get("ui", "pause_menu", "buttons", "height", default=45)
        button_spacing = config.get("ui", "pause_menu", "buttons", "spacing", default=50)
        button_start_y = self.panel_rect.top + 100  # Fixed offset for pause menu
        
        # Scale buttons to fit better within the panel based on config
        button_width = int(panel_width * button_width_ratio)
        
        # Create button rects for collision detection
        self.button_rects = []
        
        for i in range(len(self.menu_options)):
            # Create a scaled button for this option
            button = pygame.transform.scale(
                self.button_normal if i != self.selected_option else self.button_hover,
                (button_width, button_height)
            )
            
            # Store the scaled versions
            if i == 0:
                self.scaled_button_normal = pygame.transform.scale(self.button_normal, (button_width, button_height))
                self.scaled_button_hover = pygame.transform.scale(self.button_hover, (button_width, button_height))
            
            # Create a rect for this button
            button_rect = button.get_rect(
                center=(self.panel_rect.centerx, button_start_y + i * button_spacing)
            )
            self.button_rects.append(button_rect)
            
        # Load button font based on config
        # Map from numerical font size to named size
        button_font_size = config.get("ui", "pause_menu", "buttons", "font_size", default=20)
        
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
        
        logger.debug(f"Pause menu UI assets loaded with {len(self.button_rects)} buttons")

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
            elif event.key == pygame.K_ESCAPE:
                # Pressing escape again returns to game
                self.play_sound("button_click")

                # Stop the pause music before resuming the game
                self.sound_manager.stop_music()

                # Just unpause the game to resume
                if self.scene_manager:
                    game_scene = self.scene_manager.scenes.get("game")
                    if game_scene:
                        game_scene.resume_from_pause()
                self.switch_to_scene("game")
        
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
        elif action == "game":
            # Stop the pause music before resuming the game
            self.sound_manager.stop_music()

            # Just unpause the game to resume
            if self.scene_manager:
                game_scene = self.scene_manager.scenes.get("game")
                if game_scene:
                    game_scene.resume_from_pause()
            self.switch_to_scene(action)
        elif action == "main_menu":
            # Stop the pause music before going to the main menu
            self.sound_manager.stop_music()

            # If returning to main menu, reset the game state for later
            if self.scene_manager:
                game_scene = self.scene_manager.scenes.get("game")
                if game_scene:
                    game_scene.reset()
            self.switch_to_scene(action)
        elif action == "options":
            # Set the previous scene to return to pause menu
            if self.scene_manager:
                options_scene = self.scene_manager.scenes.get("options")
                if options_scene:
                    options_scene.set_previous_scene("pause")
            self.switch_to_scene(action)
        else:
            self.switch_to_scene(action)

    def update(self):
        """Update menu logic. Nothing needed for a simple menu."""
        pass

    def render(self):
        """Render the pause menu over the game screen."""
        # Get screen dimensions from config
        screen_width = config.get("screen", "width", default=800)
        screen_height = config.get("screen", "height", default=600)

        # Note: we're not clearing the screen here since
        # we want to see the game paused in the background

        # Apply semi-transparent overlay
        self.screen.blit(self.overlay, (0, 0))
        
        # Draw background panel
        self.screen.blit(self.panel, self.panel_rect)

        # Get title configuration
        title_font_size = config.get("ui", "pause_menu", "title", "font_size", default=32)
        title_color = config.get("ui", "pause_menu", "title", "color", default="white")
        
        # Draw title
        title = self.title_font.render("PAUSED", True, config.get_color(title_color))
        title_rect = title.get_rect(center=(screen_width // 2, self.panel_rect.top + 40))
        self.screen.blit(title, title_rect)

        # Get button text color from config
        button_text_color = config.get("ui", "pause_menu", "buttons", "text_color", default="white")
        
        # Draw menu options as buttons
        for i, option in enumerate(self.menu_options):
            # Choose button image based on selection
            button_img = self.scaled_button_hover if i == self.selected_option else self.scaled_button_normal
            
            # Draw the button
            button_rect = self.button_rects[i]
            self.screen.blit(button_img, button_rect)
            
            # Draw the button text
            text = self.button_font.render(option["text"], True, config.get_color(button_text_color))
            text_rect = text.get_rect(center=button_rect.center)
            self.screen.blit(text, text_rect)
