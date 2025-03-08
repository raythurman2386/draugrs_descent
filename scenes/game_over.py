import pygame
from .scene import Scene
from managers import config, game_asset_manager
from utils.logger import GameLogger

# Get a logger for the game over scene
logger = GameLogger.get_logger("game_over")


class GameOverScene(Scene):
    """Game over scene displayed when the player dies."""

    def __init__(self):
        super().__init__()

        # Game stats to display
        self.final_score = 0
        self.high_score = 0
        self.enemies_killed = 0
        self.powerups_collected = 0
        self.time_survived = 0

        # Menu options
        self.menu_options = [
            {"text": "Restart", "action": "game"},
            {"text": "Main Menu", "action": "main_menu"},
            {"text": "Exit", "action": "exit"},
        ]
        self.selected_option = 0
        
        # UI theme from config
        self.ui_theme = config.get("ui", "default_theme", default="blue")
        self.load_ui_assets()

    def load_ui_assets(self):
        """Load UI assets for the game over screen."""
        logger.debug(f"Loading game over UI assets with theme: {self.ui_theme}")
        
        # Load the panel and buttons
        self.panel = game_asset_manager.get_ui_element(f"{self.ui_theme}_panel.png", self.ui_theme)
        self.button_normal = game_asset_manager.get_ui_element(f"{self.ui_theme}_button00.png", self.ui_theme)
        self.button_hover = game_asset_manager.get_ui_element(f"{self.ui_theme}_button01.png", self.ui_theme)
        
        # Get screen dimensions
        self.screen_width = config.get("screen", "width", default=800)
        self.screen_height = config.get("screen", "height", default=600)
        
        # Get panel dimensions from config
        panel_width_ratio = config.get("ui", "game_over", "panel", "width_ratio", default=0.6)
        panel_height_ratio = config.get("ui", "game_over", "panel", "height_ratio", default=0.75)
        panel_width = int(self.screen_width * panel_width_ratio)
        panel_height = int(self.screen_height * panel_height_ratio)
        
        # Scale the panel to fit our needs
        self.panel = pygame.transform.scale(self.panel, (panel_width, panel_height))
        
        # Calculate panel position
        self.panel_rect = self.panel.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        
        # Get button configuration from config
        button_width_ratio = config.get("ui", "game_over", "buttons", "width_ratio", default=0.7)
        button_height = config.get("ui", "game_over", "buttons", "height", default=50)
        button_spacing = config.get("ui", "game_over", "buttons", "spacing", default=70)
        
        # Scale buttons to fit within the panel based on config
        button_width = int(panel_width * button_width_ratio)
        
        # Create scaled buttons
        self.scaled_button_normal = pygame.transform.scale(self.button_normal, (button_width, button_height))
        self.scaled_button_hover = pygame.transform.scale(self.button_hover, (button_width, button_height))
        
        # Calculate button positions - position them at the bottom of the panel with good spacing
        self.button_rects = []
        
        # Calculate where the buttons should start (from bottom of panel, leave some space)
        total_button_height = len(self.menu_options) * button_height + (len(self.menu_options) - 1) * (button_spacing - button_height)
        button_start_y = self.panel_rect.bottom - total_button_height - 30  # 30px padding from bottom
        
        for i in range(len(self.menu_options)):
            button_rect = self.scaled_button_normal.get_rect(
                center=(self.panel_rect.centerx, button_start_y + i * button_spacing)
            )
            self.button_rects.append(button_rect)
        
        # Load button font based on config
        button_font_size = config.get("ui", "game_over", "buttons", "font_size", default=24)
        
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
        
        # Load title font
        title_font_size = config.get("ui", "game_over", "title", "font_size", default=48)
        title_size_name = "title" if title_font_size >= 36 else "heading"
        self.game_over_title_font = game_asset_manager.get_font("default", title_size_name)
        
        # Load stats font - use smaller font for stats to avoid overlap
        stats_font_size = config.get("ui", "game_over", "stats", "font_size", default=18)
        stats_size_name = "small"
        if stats_font_size >= 28:
            stats_size_name = "normal"
        elif stats_font_size >= 24:
            stats_size_name = "ui"
        
        self.stats_font = game_asset_manager.get_font("default", stats_size_name)
        
        logger.debug(f"Game over UI assets loaded with {len(self.button_rects)} buttons")

    def reset(self):
        """Reset the scene state."""
        self.selected_option = 0

        # Get stats from the game scene
        if self.scene_manager:
            game_scene = self.scene_manager.scenes.get("game")
            if game_scene:
                self.final_score = game_scene.score_manager.current_score
                self.high_score = game_scene.score_manager.high_score
                self.enemies_killed = game_scene.enemies_killed
                self.powerups_collected = game_scene.powerups_collected
                self.time_survived = game_scene.time_survived

        # Play game over music
        self.play_scene_music("game_over")

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
                    # Always reset the game when starting from game over
                    game_scene.reset()
                    # Ensure the game isn't paused
                    game_scene.paused = False
            self.switch_to_scene(action)

    def update(self):
        """Update menu logic. Nothing needed for a simple menu."""
        pass

    def render(self):
        """Render the game over screen."""
        # Set background color
        background_color = config.get("ui", "game_over", "background_color", default="black")
        self.screen.fill(config.get_color(background_color))
        
        # Draw the panel background
        self.screen.blit(self.panel, self.panel_rect)

        # Get title configuration
        title_color = config.get("ui", "game_over", "title", "color", default="red")
        
        # Draw title - position at the top of the panel with good spacing
        title = self.game_over_title_font.render("GAME OVER", True, config.get_color(title_color))
        title_rect = title.get_rect(center=(self.screen_width // 2, self.panel_rect.top + 60))
        self.screen.blit(title, title_rect)

        # Draw score and stats - calculate spacing to fit between title and buttons
        available_space = self.button_rects[0].top - (title_rect.bottom + 20)  # Space between title and first button
        
        # Divide the available space evenly
        num_stat_lines = 5  # Score, high score, and 3 stat lines
        line_spacing = available_space / (num_stat_lines + 1)  # +1 for extra padding
        
        # Start position for stats (after title with some padding)
        y_position = title_rect.bottom + line_spacing

        # Score display
        score_color = config.get("ui", "game_over", "stats", "score_color", default="yellow")
        score_text = self.stats_font.render(
            f"SCORE: {self.final_score:,}", True, config.get_color(score_color)
        )
        score_rect = score_text.get_rect(center=(self.screen_width // 2, y_position))
        self.screen.blit(score_text, score_rect)

        # High score display
        y_position += line_spacing
        high_score_color = (
            config.get_color(score_color)
            if self.final_score >= self.high_score
            else config.get_color("orange")
        )
        high_score_text = self.stats_font.render(
            f"HIGH SCORE: {self.high_score:,}", True, high_score_color
        )
        high_score_rect = high_score_text.get_rect(center=(self.screen_width // 2, y_position))
        self.screen.blit(high_score_text, high_score_rect)

        # Stats display
        y_position += line_spacing
        stats = [
            f"ENEMIES DEFEATED: {self.enemies_killed}",
            f"POWERUPS COLLECTED: {self.powerups_collected}",
            f"TIME SURVIVED: {self.time_survived} SECONDS",
        ]

        stats_color = config.get("ui", "game_over", "stats", "text_color", default="white")
        for stat in stats:
            stat_text = self.stats_font.render(stat, True, config.get_color(stats_color))
            stat_rect = stat_text.get_rect(center=(self.screen_width // 2, y_position))
            self.screen.blit(stat_text, stat_rect)
            y_position += line_spacing

        # Get button text color from config
        button_text_color = config.get("ui", "game_over", "buttons", "text_color", default="white")
        
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
