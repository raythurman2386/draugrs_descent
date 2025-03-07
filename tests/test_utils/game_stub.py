"""Test utilities and stubs for game testing."""

import pygame
import random
from enum import Enum, auto
from objects import Player, Enemy


class GameState(Enum):
    """Enum representing the different states the game can be in."""

    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()


# Basic Game class stub for tests
class GameStub:
    """A stub implementation of the Game class for testing purposes."""

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.state = GameState.MENU
        self.player = Player()
        self.score = 0
        self.enemies = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.enemy_spawn_rate = 1000  # milliseconds
        self.enemy_spawn_timer = 0

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.state == GameState.MENU and event.key == pygame.K_RETURN:
                    self.state = GameState.PLAYING
                elif self.state == GameState.GAME_OVER and event.key == pygame.K_r:
                    self.reset_game()
                    self.state = GameState.PLAYING

    def update(self):
        if self.state == GameState.PLAYING:
            # Check player health
            if self.player.current_health <= 0:
                self.state = GameState.GAME_OVER

            # Update enemy spawn timer
            try:
                current_time = pygame.time.get_ticks()
            except AttributeError:
                # For tests when pygame.time.get_ticks() may not be available
                current_time = self.enemy_spawn_timer + self.enemy_spawn_rate + 1

            # Explicitly check for enemy spawning for tests
            if (
                hasattr(self, "enemy_spawn_timer")
                and current_time - self.enemy_spawn_timer > self.enemy_spawn_rate
            ):
                # Directly spawn an enemy for the test
                self.spawn_enemy()
                self.enemy_spawn_timer = current_time

            # Update entities
            self.player.update()
            self.enemies.update(self.player.rect.center)
            self.projectiles.update()
            self.powerups.update()

            # Check for collisions with enemies that died - Important: Process all enemies
            dead_enemies = [enemy for enemy in self.enemies if enemy.health <= 0]
            for enemy in dead_enemies:
                enemy.kill()
                self.score += 100  # Increase score by 100 points when enemy dies

    def reset_game(self):
        self.player = Player()
        self.score = 0
        self.enemies.empty()
        self.powerups.empty()
        self.projectiles.empty()

    def spawn_enemy(self):
        # Create enemy at a random position on the screen edges
        # Handle the case when self.screen doesn't have a get_rect method (test screens)
        if hasattr(self.screen, "get_rect"):
            screen_rect = self.screen.get_rect()
        else:
            # For test screens, use a default size
            screen_rect = pygame.Rect(0, 0, 800, 600)

        side = random.choice(["top", "right", "bottom", "left"])

        if side == "top":
            x = random.randint(0, screen_rect.width)
            y = -20
        elif side == "right":
            x = screen_rect.width + 20
            y = random.randint(0, screen_rect.height)
        elif side == "bottom":
            x = random.randint(0, screen_rect.width)
            y = screen_rect.height + 20
        else:  # left
            x = -20
            y = random.randint(0, screen_rect.height)

        enemy = Enemy((x, y))
        self.enemies.add(enemy)
