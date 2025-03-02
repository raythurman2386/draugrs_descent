import pygame
from constants import (
    PROJECTILE_WIDTH, PROJECTILE_HEIGHT, WHITE,
    PROJECTILE_DAMAGE
)
from utils.logger import GameLogger

# Get a logger for the projectile module
logger = GameLogger.get_logger("projectile")

class Projectile(pygame.sprite.Sprite):
    # Counter for unique projectile IDs
    next_id = 1
    
    def __init__(self, position, velocity):
        super().__init__()
        # Assign a unique ID to each projectile
        self.id = Projectile.next_id
        Projectile.next_id += 1
        
        self.image = pygame.Surface((PROJECTILE_WIDTH, PROJECTILE_HEIGHT))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.center = position
        self.velocity = velocity
        self.damage = PROJECTILE_DAMAGE
        
        logger.debug(f"Projectile {self.id} created at {position} with velocity {velocity}")

    def update(self):
        # Move the projectile based on its velocity
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]

        # Optional: Remove projectile if it goes off-screen
        screen_rect = pygame.display.get_surface().get_rect()
        if not screen_rect.colliderect(self.rect):
            logger.debug(f"Projectile {self.id} went off-screen and was removed")
            self.kill()