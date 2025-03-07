import pygame
from .scene import Scene
from managers import config


class GameOverScene(Scene):
    """Game over scene displayed when the player dies."""

    def __init__(self):
        super().__init__()
        self.title_font = pygame.font.SysFont("Arial", 64)
        self.stats_font = pygame.font.SysFont("Arial", 28)
        self.button_font = pygame.font.SysFont("Arial", 36)

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
        self.screen.fill(config.BLACK)

        # Draw title
        title = self.title_font.render("GAME OVER", True, config.RED)
        title_rect = title.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 6))
        self.screen.blit(title, title_rect)

        # Draw score and stats
        y_position = config.SCREEN_HEIGHT // 3

        # Score display
        score_text = self.stats_font.render(f"SCORE: {self.final_score:,}", True, config.YELLOW)
        score_rect = score_text.get_rect(center=(config.SCREEN_WIDTH // 2, y_position))
        self.screen.blit(score_text, score_rect)

        # High score display
        y_position += 40
        high_score_color = config.YELLOW if self.final_score >= self.high_score else config.ORANGE
        high_score_text = self.stats_font.render(
            f"HIGH SCORE: {self.high_score:,}", True, high_score_color
        )
        high_score_rect = high_score_text.get_rect(center=(config.SCREEN_WIDTH // 2, y_position))
        self.screen.blit(high_score_text, high_score_rect)

        # Stats display
        y_position += 40
        stats = [
            f"Enemies Defeated: {self.enemies_killed}",
            f"Powerups Collected: {self.powerups_collected}",
            f"Time Survived: {self.time_survived} seconds",
        ]

        for stat in stats:
            stat_text = self.stats_font.render(stat, True, config.WHITE)
            stat_rect = stat_text.get_rect(center=(config.SCREEN_WIDTH // 2, y_position))
            self.screen.blit(stat_text, stat_rect)
            y_position += 30

        # Draw menu options
        y_position = config.SCREEN_HEIGHT - 180  # Start menu options lower on the screen

        for i, option in enumerate(self.menu_options):
            color = (255, 255, 0) if i == self.selected_option else config.WHITE
            text = self.button_font.render(option["text"], True, color)
            position = (config.SCREEN_WIDTH // 2, y_position + i * 50)
            text_rect = text.get_rect(center=position)
            self.screen.blit(text, text_rect)

            # Draw a selection indicator
            if i == self.selected_option:
                pygame.draw.rect(self.screen, color, text_rect.inflate(20, 10), 2)
