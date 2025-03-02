import pygame
from .scene import Scene
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE, RED


class GameOverScene(Scene):
    """Game over scene displayed when the player dies."""

    def __init__(self):
        super().__init__()
        self.title_font = pygame.font.SysFont("Arial", 64)
        self.button_font = pygame.font.SysFont("Arial", 36)

        # Menu options
        self.menu_options = [
            {"text": "Restart", "action": "game"},
            {"text": "Main Menu", "action": "main_menu"},
            {"text": "Exit", "action": "exit"},
        ]
        self.selected_option = 0

    def handle_event(self, event):
        """Handle menu navigation and selection."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(
                    self.menu_options
                )
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(
                    self.menu_options
                )
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                action = self.menu_options[self.selected_option]["action"]
                if action == "exit":
                    self.done = True
                else:
                    self.switch_to_scene(action)

    def update(self):
        """Update menu logic. Nothing needed for a simple menu."""
        pass

    def render(self):
        """Render the game over screen."""
        self.screen.fill(BLACK)

        # Draw title
        title = self.title_font.render("GAME OVER", True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        self.screen.blit(title, title_rect)

        # Draw menu options
        for i, option in enumerate(self.menu_options):
            color = (255, 255, 0) if i == self.selected_option else WHITE
            text = self.button_font.render(option["text"], True, color)
            position = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 60)
            text_rect = text.get_rect(center=position)
            self.screen.blit(text, text_rect)

            # Draw a selection indicator
            if i == self.selected_option:
                pygame.draw.rect(self.screen, color, text_rect.inflate(20, 10), 2)
