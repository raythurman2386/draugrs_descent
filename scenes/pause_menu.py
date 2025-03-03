import pygame
from .scene import Scene
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE


class PauseMenuScene(Scene):
    """Pause menu scene."""

    def __init__(self):
        super().__init__()
        self.title_font = pygame.font.SysFont("Arial", 48)
        self.button_font = pygame.font.SysFont("Arial", 36)

        # Menu options
        self.menu_options = [
            {"text": "Resume", "action": "game"},
            {"text": "Main Menu", "action": "main_menu"},
            {"text": "Exit", "action": "exit"},
        ]
        self.selected_option = 0

        # Create a semi-transparent overlay
        self.overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 128))  # Black with 50% opacity

        # Start playing pause menu music
        self.play_scene_music("pause")

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
                else:
                    self.switch_to_scene(action)
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

    def update(self):
        """Update menu logic. Nothing needed for a simple menu."""
        pass

    def render(self):
        """Render the pause menu over the game screen."""
        # Note: we're not clearing the screen here since
        # we want to see the game paused in the background

        # Apply semi-transparent overlay
        self.screen.blit(self.overlay, (0, 0))

        # Draw title
        title = self.title_font.render("PAUSED", True, WHITE)
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
