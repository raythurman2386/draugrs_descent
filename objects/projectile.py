import pygame
from managers import config
from utils.logger import GameLogger

# Get a logger for the projectile module
logger = GameLogger.get_logger("projectile")


class Projectile(pygame.sprite.Sprite):
    # Counter for unique projectile IDs
    next_id = 1

    def __init__(self, position, velocity, damage=None, is_enemy_projectile=False):
        super().__init__()
        # Assign a unique ID to each projectile
        self.id = Projectile.next_id
        Projectile.next_id += 1

        # Get projectile dimensions from config
        width = config.get("projectile", "dimensions", "width", default=10)
        height = config.get("projectile", "dimensions", "height", default=10)

        self.image = pygame.Surface((width, height))

        # Set color based on whether it's an enemy projectile or player projectile
        if is_enemy_projectile:
            self.image.fill(config.get_color("red"))
        else:
            self.image.fill(config.get_color("white"))

        self.rect = self.image.get_rect()
        self.rect.center = position
        self.position = list(position)
        self.velocity = velocity
        self.is_enemy_projectile = is_enemy_projectile

        # Get damage from config if not provided
        self.damage = (
            damage
            if damage is not None
            else config.get("projectile", "attributes", "damage", default=10)
        )

        self.active = True
        logger.debug(
            f"Projectile {self.id} created at {position} with velocity {velocity} (enemy: {is_enemy_projectile})"
        )

    def update(self):
        """Update the projectile position based on velocity."""
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        self.rect.center = (int(self.position[0]), int(self.position[1]))

        # Check if projectile is off-screen
        screen_width = config.get("screen", "width", default=800)
        screen_height = config.get("screen", "height", default=600)

        if (
            self.rect.right < 0
            or self.rect.left > screen_width
            or self.rect.bottom < 0
            or self.rect.top > screen_height
        ):
            self.kill()
            logger.debug(f"Projectile {self.id} went off-screen and was removed")

    def deactivate(self):
        """Deactivate the projectile."""
        self.active = False
        logger.debug(f"Projectile {self.id} deactivated")

    def kill(self):
        """Override kill method to set active to False before removing from groups."""
        self.active = False
        super().kill()
        logger.debug(f"Projectile {self.id} killed")
