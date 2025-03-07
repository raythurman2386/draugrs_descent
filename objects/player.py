import pygame
import math
from utils.logger import GameLogger
from utils import find_closest_enemy
from .projectile import Projectile
from managers import config

# Get a logger for the player module
logger = GameLogger.get_logger("player")


class Player(pygame.sprite.Sprite):
    def __init__(self, position=None):
        super().__init__()
        # Get player dimensions from config
        width = config.get("player", "dimensions", "width", default=50)
        height = config.get("player", "dimensions", "height", default=50)

        self.image = pygame.Surface((width, height))
        self.image.fill(config.get_color("green"))
        self.rect = self.image.get_rect()

        # Get player start position from config
        start_x = config.get("player", "start_position", "x", default=400)
        start_y = config.get("player", "start_position", "y", default=300)
        self.rect.center = position if position else (start_x, start_y)

        # Get player attributes from config
        self.max_health = config.get("player", "attributes", "max_health", default=100)
        self.current_health = self.max_health
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = config.get(
            "player", "attributes", "invincibility_duration", default=1000
        )
        self.last_shot_time = 0
        self.shot_cooldown = config.get("player", "attributes", "shot_cooldown", default=500)

        # Weapon boost properties
        self.weapon_boost_active = False
        self.weapon_boost_timer = 0
        self.weapon_boost_duration = 0
        self.base_shot_cooldown = config.get("player", "attributes", "shot_cooldown", default=500)

        # Visual effect properties
        self.flash_effect = False
        self.flash_duration = 200
        self.flash_timer = 0
        self.flash_color = None

        # These will be set by the game class
        self.screen = None
        self.enemy_group = None
        self.projectile_group = None
        self.all_sprites = None

        logger.info("Player initialized")

    def update(self):
        # Handle player movement
        keys = pygame.key.get_pressed()
        moving = False
        if keys[pygame.K_LEFT]:
            self.rect.x -= config.get("player", "attributes", "movement_speed", default=5)
            moving = True
        if keys[pygame.K_RIGHT]:
            self.rect.x += config.get("player", "attributes", "movement_speed", default=5)
            moving = True
        if keys[pygame.K_UP]:
            self.rect.y -= config.get("player", "attributes", "movement_speed", default=5)
            moving = True
        if keys[pygame.K_DOWN]:
            self.rect.y += config.get("player", "attributes", "movement_speed", default=5)
            moving = True

        # Keep player within screen bounds
        if self.screen:
            self.rect.clamp_ip(self.screen.get_rect())

        # Handle shooting only when moving
        current_time = pygame.time.get_ticks()
        if moving and current_time - self.last_shot_time > self.shot_cooldown:
            logger.debug(f"Attempting to shoot at {current_time}")
            projectile = self.shoot()
            if projectile:
                logger.debug(f"Projectile created: {projectile}")
                logger.debug(f"Projectile velocity: {projectile.velocity}")
                logger.debug(f"Projectile position: {projectile.rect.center}")
                # Add projectile to groups unconditionally
                self.projectile_group.add(projectile)
                self.all_sprites.add(projectile)
                logger.debug("Projectile added to groups")
            self.last_shot_time = current_time

        # Handle invincibility
        if self.invincible:
            current_time = pygame.time.get_ticks()
            if current_time - self.invincible_timer > self.invincible_duration:
                self.invincible = False
                logger.debug("Player invincibility ended")

        # Check for weapon boost expiration
        if self.weapon_boost_active:
            current_time = pygame.time.get_ticks()
            if current_time - self.weapon_boost_timer > self.weapon_boost_duration:
                self.deactivate_weapon_boost()
                logger.debug("Weapon boost expired")

        # Update visual effects
        self.update_visual_effects()

    def shoot(self):
        # Find the closest enemy to aim at
        if self.enemy_group:
            logger.debug(f"Enemy group count: {len(self.enemy_group)}")
            closest_enemy = find_closest_enemy(self.rect.center, self.enemy_group)

            if closest_enemy:
                logger.debug(f"Closest enemy found at {closest_enemy.rect.center}")
                # Calculate velocity towards the enemy
                dx = closest_enemy.rect.centerx - self.rect.centerx
                dy = closest_enemy.rect.centery - self.rect.centery
                distance = math.sqrt(dx**2 + dy**2)
                velocity = (dx / distance * 10, dy / distance * 10)
                projectile = Projectile(self.rect.center, velocity)
                logger.debug(f"Projectile velocity: {velocity}")
                logger.debug(f"Projectile position: {projectile.rect.center}")
                return projectile
        logger.debug("No valid target found")
        return None

    def take_damage(self, amount):
        """Handle player taking damage with appropriate logging."""
        if not self.invincible:
            self.current_health -= amount
            self.invincible = True
            self.invincible_timer = pygame.time.get_ticks()
            logger.info(
                f"Player took {amount} damage. Health: {self.current_health}/{self.max_health}"
            )
            # Flash red when taking damage
            self.start_flash_effect((255, 0, 0))
            if self.current_health <= 0:
                logger.warning("Player died!")
                return True  # Player died
        return False  # Player still alive

    def start_flash_effect(self, color):
        """Start a flash effect with the given color."""
        self.flash_effect = True
        self.flash_timer = pygame.time.get_ticks()
        self.flash_color = color
        logger.debug(f"Started flash effect with color {color}")

    def update_visual_effects(self):
        """Update visual effects for the player."""
        current_time = pygame.time.get_ticks()

        # Reset image to original before applying effects
        self.image = pygame.Surface((self.rect.width, self.rect.height)).convert_alpha()
        self.image.fill(config.get_color("green"))

        # Handle invincibility visual effect (pulsing)
        if self.invincible:
            # Make player pulse or flicker when invincible
            if (current_time // 200) % 2:  # Toggle visibility every 200ms
                alpha = 128  # Semi-transparent
                self.image.set_alpha(alpha)
            else:
                self.image.set_alpha(255)  # Fully visible

        # Handle flash effect
        if self.flash_effect:
            if current_time - self.flash_timer < self.flash_duration:
                # Apply color flash
                flash_surface = pygame.Surface(self.image.get_size()).convert_alpha()
                flash_surface.fill(self.flash_color)
                # Set lower alpha for a subtle effect
                flash_surface.set_alpha(100)
                self.image.blit(flash_surface, (0, 0))
            else:
                # End flash effect
                self.flash_effect = False
                logger.debug("Flash effect ended")

    def activate_weapon_boost(
        self, duration=config.get("powerups", "weapon_boost", "duration", default=5000)
    ):
        """Activate weapon boost, increasing fire rate."""
        self.weapon_boost_active = True
        self.weapon_boost_timer = pygame.time.get_ticks()
        self.weapon_boost_duration = duration

        # Reduce shot cooldown (increase fire rate)
        self.shot_cooldown = int(
            self.base_shot_cooldown
            * (1 - config.get("powerups", "weapon_boost", "factor", default=0.5))
        )
        logger.info(
            f"Weapon boost activated. Shot cooldown reduced to {self.shot_cooldown}ms for {duration}ms"
        )

    def deactivate_weapon_boost(self):
        """Deactivate weapon boost, restoring normal fire rate."""
        if self.weapon_boost_active:
            self.weapon_boost_active = False
            self.shot_cooldown = self.base_shot_cooldown
            logger.info("Weapon boost deactivated. Shot cooldown restored to normal.")
