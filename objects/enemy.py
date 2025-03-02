import pygame
from constants import (
    ENEMY_WIDTH, ENEMY_HEIGHT, RED, 
    ENEMY_MAX_HEALTH, ENEMY_DAMAGE
)
from utils.logger import GameLogger

# Get a logger for the enemy module
logger = GameLogger.get_logger("enemy")

class Enemy(pygame.sprite.Sprite):
    # Counter for unique enemy IDs
    next_id = 1
    
    def __init__(self, position):
        super().__init__()
        # Assign a unique ID to each enemy
        self.id = Enemy.next_id
        Enemy.next_id += 1
        
        self.image = pygame.Surface((ENEMY_WIDTH, ENEMY_HEIGHT))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = position
        self.max_health = ENEMY_MAX_HEALTH
        self.current_health = ENEMY_MAX_HEALTH
        
        logger.debug(f"Enemy {self.id} created at position {position}")

    def update(self, player_position):
        # Simple enemy movement towards the player
        if player_position:
            dx = player_position[0] - self.rect.centerx
            dy = player_position[1] - self.rect.centery
            distance = (dx**2 + dy**2)**0.5
            
            # Move towards the player if not too close
            if distance > 0:
                speed = 2  # Adjust as needed
                self.rect.x += dx / distance * speed
                self.rect.y += dy / distance * speed
                
    def take_damage(self, amount):
        """Handle enemy taking damage with appropriate logging."""
        self.current_health -= amount
        logger.debug(f"Enemy {self.id} took {amount} damage. Health: {self.current_health}/{self.max_health}")
        
        if self.current_health <= 0:
            logger.info(f"Enemy {self.id} was defeated")
            return True
        return False
