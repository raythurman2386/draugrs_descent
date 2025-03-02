import pygame
import math
from utils.logger import GameLogger
from utils import find_closest_enemy
from .projectile import Projectile
from constants import (
    PLAYER_WIDTH, PLAYER_HEIGHT, GREEN, 
    PLAYER_START_X, PLAYER_START_Y, 
    PLAYER_MAX_HEALTH, PLAYER_MOVEMENT_SPEED,
    PLAYER_SHOT_COOLDOWN, PLAYER_INVINCIBILITY_DURATION
)

# Get a logger for the player module
logger = GameLogger.get_logger("player")

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.center = (PLAYER_START_X, PLAYER_START_Y)
        self.max_health = PLAYER_MAX_HEALTH
        self.current_health = PLAYER_MAX_HEALTH
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = PLAYER_INVINCIBILITY_DURATION
        self.last_shot_time = 0
        self.shot_cooldown = PLAYER_SHOT_COOLDOWN
        
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
            self.rect.x -= PLAYER_MOVEMENT_SPEED
            moving = True
        if keys[pygame.K_RIGHT]:
            self.rect.x += PLAYER_MOVEMENT_SPEED
            moving = True
        if keys[pygame.K_UP]:
            self.rect.y -= PLAYER_MOVEMENT_SPEED
            moving = True
        if keys[pygame.K_DOWN]:
            self.rect.y += PLAYER_MOVEMENT_SPEED
            moving = True

        # Keep player within screen bounds
        if self.screen:
            self.rect.clamp_ip(self.screen.get_rect())

        # Handle shooting only when moving
        current_time = pygame.time.get_ticks()
        if moving and current_time - self.last_shot_time > self.shot_cooldown:
            logger.debug(f'Attempting to shoot at {current_time}')
            projectile = self.shoot()
            if projectile:
                logger.debug(f'Projectile created: {projectile}')
                logger.debug(f'Projectile velocity: {projectile.velocity}')
                logger.debug(f'Projectile position: {projectile.rect.center}')
                # Add projectile to groups unconditionally
                self.projectile_group.add(projectile)
                self.all_sprites.add(projectile)
                logger.debug('Projectile added to groups')
            self.last_shot_time = current_time

        # Handle invincibility
        if self.invincible:
            current_time = pygame.time.get_ticks()
            if current_time - self.invincible_timer > self.invincible_duration:
                self.invincible = False
                logger.debug('Player invincibility ended')

    def shoot(self):
        # Find the closest enemy to aim at
        if self.enemy_group:
            logger.debug(f'Enemy group count: {len(self.enemy_group)}')
            closest_enemy = find_closest_enemy(self.rect.center, self.enemy_group)
            
            if closest_enemy:
                logger.debug(f'Closest enemy found at {closest_enemy.rect.center}')
                # Calculate velocity towards the enemy
                dx = closest_enemy.rect.centerx - self.rect.centerx
                dy = closest_enemy.rect.centery - self.rect.centery
                distance = math.sqrt(dx**2 + dy**2)
                velocity = (dx/distance * 10, dy/distance * 10)
                projectile = Projectile(self.rect.center, velocity)
                logger.debug(f'Projectile velocity: {velocity}')
                logger.debug(f'Projectile position: {projectile.rect.center}')
                return projectile
        logger.debug('No valid target found')
        return None
        
    def take_damage(self, amount):
        """Handle player taking damage with appropriate logging."""
        if not self.invincible:
            self.current_health -= amount
            self.invincible = True
            self.invincible_timer = pygame.time.get_ticks()
            logger.info(f'Player took {amount} damage. Health: {self.current_health}/{self.max_health}')
            if self.current_health <= 0:
                logger.warning('Player died!')
                return True  # Player died
        return False  # Player still alive