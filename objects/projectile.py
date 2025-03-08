import pygame
from managers import config
from utils.logger import GameLogger

# Get a logger for the projectile module
logger = GameLogger.get_logger("projectile")


class Projectile(pygame.sprite.Sprite):
    # Counter for unique projectile IDs
    next_id = 1

    def __init__(
        self,
        position: tuple[float, float],
        velocity: tuple[float, float],
        damage: int = None,
        is_enemy_projectile: bool = False,
        map_width: int = None,
        map_height: int = None,
    ):
        super().__init__()
        # Assign a unique ID to each projectile
        self.id = Projectile.next_id
        Projectile.next_id += 1

        # Cache projectile dimensions from config
        self.width = config.get("projectile", "dimensions", "width", default=10)
        self.height = config.get("projectile", "dimensions", "height", default=10)

        # Create projectile image
        self.image = pygame.Surface((self.width, self.height))

        # Cache color based on projectile type
        self.color = config.get_color("red") if is_enemy_projectile else config.get_color("white")
        self.image.fill(self.color)

        # Set initial position and velocity
        self.rect = self.image.get_rect(center=position)
        self.position = list(position)
        self.velocity = velocity
        self.is_enemy_projectile = is_enemy_projectile

        # Cache damage from config if not provided
        self.damage = (
            damage
            if damage is not None
            else config.get("projectile", "attributes", "damage", default=10)
        )

        # Cache map dimensions for boundary checking
        self.map_width = map_width or config.get("screen", "width", default=800)
        self.map_height = map_height or config.get("screen", "height", default=600)

        # Cache off-screen margin
        self.off_screen_margin = config.get("projectile", "off_screen_margin", default=100)

        self.active = True
        logger.debug(
            f"Projectile {self.id} created at {position} with velocity {velocity} (enemy: {is_enemy_projectile})"
        )

    def update(self):
        """Update the projectile position based on velocity and check boundaries."""
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        self.rect.center = (int(self.position[0]), int(self.position[1]))

        # Check if projectile is off-map with a margin
        margin = self.off_screen_margin
        if (
            self.rect.right < -margin
            or self.rect.left > self.map_width + margin
            or self.rect.bottom < -margin
            or self.rect.top > self.map_height + margin
        ):
            self.kill()
            logger.debug(f"Projectile {self.id} went far off-map and was removed")

    def deactivate(self):
        """Deactivate the projectile."""
        self.active = False
        logger.debug(f"Projectile {self.id} deactivated")

    def kill(self):
        """Override kill method to set active to False before removing from groups."""
        self.active = False
        super().kill()
        logger.debug(f"Projectile {self.id} killed")
