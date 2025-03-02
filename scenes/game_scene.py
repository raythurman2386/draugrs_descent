import pygame
import random
from .scene import Scene
from objects import Player, Enemy, Powerup
from utils.logger import GameLogger
from utils.utils import adjust_log_level
from utils import handle_player_powerup_collision, handle_player_enemy_collision
from constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    BLACK,
    FRAME_RATE,
    ENEMY_SPAWN_INTERVAL,
    ENEMY_SPAWN_EDGES,
    HEALTH_BAR_WIDTH,
    HEALTH_BAR_HEIGHT,
)
import logging

# Get a logger for the game scene
logger = GameLogger.get_logger("game_scene")


class GameScene(Scene):
    """Main gameplay scene."""

    def __init__(self):
        super().__init__()

        logger.info("Initializing GameScene")

        # Create game object groups
        self.player = Player()
        self.all_sprites = pygame.sprite.Group(self.player)
        self.enemy_group = pygame.sprite.Group()
        self.projectile_group = pygame.sprite.Group()
        self.powerup_group = pygame.sprite.Group()

        # Set player references
        self.player.screen = self.screen
        self.player.all_sprites = self.all_sprites
        self.player.enemy_group = self.enemy_group
        self.player.projectile_group = self.projectile_group

        # Enemy spawn timer
        self.last_spawn_time = pygame.time.get_ticks()

        # Pause flag
        self.paused = False

        # Game stats
        self.enemies_killed = 0
        self.time_survived = 0
        self.start_time = pygame.time.get_ticks()
        self.powerups_collected = 0

        logger.info("GameScene initialized")

    def spawn_enemy(self):
        """Spawn an enemy at a random screen edge."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_spawn_time > ENEMY_SPAWN_INTERVAL:
            edge = random.randint(0, 3)
            if edge == 0:  # Top
                position = (
                    random.randint(0, SCREEN_WIDTH),
                    ENEMY_SPAWN_EDGES["TOP"][1],
                )
            elif edge == 1:  # Bottom
                position = (
                    random.randint(0, SCREEN_WIDTH),
                    ENEMY_SPAWN_EDGES["BOTTOM"][1],
                )
            elif edge == 2:  # Left
                position = (
                    ENEMY_SPAWN_EDGES["LEFT"][0],
                    random.randint(0, SCREEN_HEIGHT),
                )
            else:  # Right
                position = (
                    ENEMY_SPAWN_EDGES["RIGHT"][0],
                    random.randint(0, SCREEN_HEIGHT),
                )

            enemy = Enemy(position)
            self.enemy_group.add(enemy)
            self.all_sprites.add(enemy)
            self.last_spawn_time = current_time
            logger.debug(f"Enemy spawned at {position}")

    def handle_event(self, event):
        """Handle game-specific events."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                logger.info("Game paused")
                self.paused = True
                self.switch_to_scene("pause")
            # Debug level toggles
            elif event.key == pygame.K_F1:
                adjust_log_level(logging.DEBUG)
                logger.debug("Debug logging enabled")
            elif event.key == pygame.K_F2:
                adjust_log_level(logging.INFO)
                logger.info("Info logging enabled")
            elif event.key == pygame.K_F3:
                adjust_log_level(logging.WARNING)
                logger.warning("Warning logging enabled")

    def update(self):
        """Update game objects."""
        if not self.paused:
            self.player.update()
            self.enemy_group.update(self.player.rect.center)
            self.projectile_group.update()
            self.powerup_group.update()
            self.check_collisions()
            self.spawn_enemy()

            # Update time survived
            self.time_survived = (pygame.time.get_ticks() - self.start_time) // 1000

            # Check for game over
            if self.player.current_health <= 0:
                logger.info(
                    f"Game over. Enemies killed: {self.enemies_killed}, Powerups: {self.powerups_collected}, Time survived: {self.time_survived}s"
                )
                self.switch_to_scene("game_over")

    def check_collisions(self):
        """Check and handle collisions between game objects."""
        # Projectiles vs Enemies
        hits = pygame.sprite.groupcollide(self.projectile_group, self.enemy_group, True, False)
        for projectile, enemies in hits.items():
            for enemy in enemies:
                # Use the enemy's take_damage method
                if enemy.take_damage(projectile.damage):
                    self.handle_enemy_death(enemy)
                    logger.debug(f"Enemy killed. Total killed: {self.enemies_killed}")

        # Player vs Enemies
        if not self.player.invincible:
            enemy_collisions = pygame.sprite.spritecollide(self.player, self.enemy_group, False)
            for enemy in enemy_collisions:
                handle_player_enemy_collision(self.player, enemy)

        # Player vs Powerups
        powerup_collisions = pygame.sprite.spritecollide(self.player, self.powerup_group, False)
        for powerup in powerup_collisions:
            if powerup.active:
                handle_player_powerup_collision(self.player, powerup)
                powerup.kill()  # Remove from all sprite groups
                self.powerups_collected += 1
                logger.info(
                    f"Powerup collected: {powerup.type}. Total collected: {self.powerups_collected}"
                )

    def handle_enemy_death(self, enemy):
        """Handle an enemy's death, including potential powerup drops."""
        # Remove enemy
        enemy.kill()
        self.enemies_killed += 1

        # Random chance to drop a powerup (25% chance)
        if random.random() < 0.25:  # 25% chance
            self.drop_powerup(enemy.rect.center)

    def drop_powerup(self, position):
        """Create a random powerup at the given position and add it to the game."""
        # Select a random powerup type
        powerup_type = random.choice(["health", "shield"])

        # Create the powerup
        powerup = Powerup(position, powerup_type)

        # Add to sprite groups
        self.powerup_group.add(powerup)
        self.all_sprites.add(powerup)

        logger.debug(f"Dropped {powerup_type} powerup at {position}")

    def render(self):
        """Draw the game scene."""
        self.screen.fill(BLACK)
        self.all_sprites.draw(self.screen)

        # Draw health bar
        health_ratio = self.player.current_health / self.player.max_health
        pygame.draw.rect(
            self.screen, (255, 0, 0), (10, 10, HEALTH_BAR_WIDTH, HEALTH_BAR_HEIGHT)
        )  # Background
        pygame.draw.rect(
            self.screen,
            (0, 255, 0),
            (10, 10, HEALTH_BAR_WIDTH * health_ratio, HEALTH_BAR_HEIGHT),
        )  # Health

        # Draw game stats
        self.draw_text(f"Enemies: {self.enemies_killed}", (255, 255, 255), SCREEN_WIDTH - 100, 20)
        self.draw_text(
            f"Powerups: {self.powerups_collected}", (255, 255, 255), SCREEN_WIDTH - 100, 50
        )
        self.draw_text(f"Time: {self.time_survived}s", (255, 255, 255), SCREEN_WIDTH - 100, 80)
