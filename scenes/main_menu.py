import pygame
from .scene import Scene
from managers import config


class MainMenuScene(Scene):
    """Main menu scene for the game."""

    def __init__(self):
        super().__init__()
        self.title_font = pygame.font.SysFont("Arial", 64)
        self.button_font = pygame.font.SysFont("Arial", 36)

        # Menu options
        self.menu_options = [
            {"text": "Start Game", "action": "game"},
            {"text": "Exit", "action": "exit"},
        ]
        self.selected_option = 0

        # Start playing main menu music
        self.play_scene_music("main_menu")

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
                    self.switch_to_scene(action)

    def update(self):
        """Update menu logic. Nothing needed for a simple menu."""
        pass

    def render(self):
        """Render the main menu."""
        screen_width = config.get("screen", "width", default=800)
        screen_height = config.get("screen", "height", default=600)

        # Fill the background with black
        self.screen.fill(config.get_color("black"))

        # Draw title
        title = self.title_font.render("Draugr's Descent", True, config.get_color("white"))
        title_rect = title.get_rect(center=(screen_width // 2, screen_height // 4))
        self.screen.blit(title, title_rect)

        # Draw menu options
        for i, option in enumerate(self.menu_options):
            color = (255, 255, 0) if i == self.selected_option else config.get_color("white")
            text = self.button_font.render(option["text"], True, color)
            position = (screen_width // 2, screen_height // 2 + i * 60)
            text_rect = text.get_rect(center=position)
            self.screen.blit(text, text_rect)

            # Draw a selection indicator
            if i == self.selected_option:
                pygame.draw.rect(self.screen, color, text_rect.inflate(20, 10), 2)
