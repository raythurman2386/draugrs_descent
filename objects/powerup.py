import pygame
import math
from utils.logger import GameLogger
from managers import config

# Get a logger for the powerup module
logger = GameLogger.get_logger("powerup")


class Powerup(pygame.sprite.Sprite):
    """A class representing a powerup that can be collected by the player."""

    # Counter for unique powerup IDs
    next_id = 1

    def __init__(self, position: tuple[int, int], powerup_type: str):
        """Initialize a powerup at the given position with the specified type.

        Args:
            position: The (x, y) coordinates for the powerup.
            powerup_type: The type of powerup ("health", "shield", "weapon").
        """
        super().__init__()

        # Assign a unique ID to each powerup
        self.id = Powerup.next_id
        Powerup.next_id += 1

        self.type = powerup_type
        self.active = True
        self.creation_time = pygame.time.get_ticks()

        # Cache configuration values
        self.lifespan = config.get("powerups", "attributes", "lifespan", default=10000)
        self.base_width = config.get("powerups", "dimensions", "width", default=30)
        self.base_height = config.get("powerups", "dimensions", "height", default=30)
        self.pulse_speed = 0.1
        self.pulse_size = 4
        self.color = config.get("powerups", "colors", self.type, default=(255, 255, 255))

        # Animation properties
        self.pulse_factor = 0

        # Create initial image
        self._create_image()
        self.rect = self.image.get_rect(center=position)

        logger.debug(f"Powerup {self.id} of type {powerup_type} created at position {position}")

    def _create_image(self):
        """Create the powerup image with the current pulse size."""
        pulse_offset = self.pulse_factor * self.pulse_size
        current_width = self.base_width + pulse_offset
        current_height = self.base_height + pulse_offset

        self.image = pygame.Surface((int(current_width), int(current_height)), pygame.SRCALPHA)
        radius = min(int(current_width), int(current_height)) // 2
        center = (int(current_width // 2), int(current_height // 2))
        pygame.draw.circle(self.image, self.color, center, radius)

        # Add visual indicators based on type
        if self.type == "health":
            pygame.draw.rect(
                self.image,
                (255, 255, 255),
                (int(current_width / 2 - 2), int(current_height / 4), 4, int(current_height / 2)),
            )
            pygame.draw.rect(
                self.image,
                (255, 255, 255),
                (int(current_width / 4), int(current_height / 2 - 2), int(current_width / 2), 4),
            )
        elif self.type == "shield":
            pygame.draw.circle(
                self.image,
                (255, 255, 255),
                center,
                int(min(current_width, current_height) / 3),
                2,
            )
        elif self.type == "weapon":
            points = [
                (int(current_width / 2), int(current_height / 4)),
                (int(current_width / 2 + current_width / 5), int(current_height / 2)),
                (int(current_width / 2), int(current_height / 2)),
                (int(current_width / 2 - current_width / 5), int(current_height * 3 / 4)),
            ]
            pygame.draw.polygon(self.image, (255, 255, 255), points)

        self.mask = pygame.mask.from_surface(self.image)

    def apply_effect(self, player) -> bool:
        """Apply the powerup effect to the player.

        Args:
            player: The player object to apply the effect to.

        Returns:
            True if the effect was applied successfully, False otherwise.
        """
        if not self.active:
            return False

        if self.type == "health":
            health_restore = config.get("powerups", "effects", "health_restore", default=30)
            original_health = player.current_health
            player.current_health = min(player.current_health + health_restore, player.max_health)
            health_gained = player.current_health - original_health
            logger.info(
                f"Health powerup applied. Player gained {health_gained} health. Health now: {player.current_health}/{player.max_health}"
            )

        elif self.type == "shield":
            shield_duration = config.get("powerups", "effects", "shield_duration", default=5000)
            player.invincible = True
            player.invincible_timer = pygame.time.get_ticks()
            player.invincible_duration = shield_duration
            logger.info(f"Shield powerup applied. Player invincible for {shield_duration}ms")

        elif self.type == "weapon":
            weapon_boost_duration = config.get(
                "powerups", "effects", "weapon_boost_duration", default=10000
            )
            player.activate_weapon_boost(weapon_boost_duration)
            logger.info(
                f"Weapon boost powerup applied. Player's fire rate increased for {weapon_boost_duration}ms"
            )

        self.deactivate()
        return True

    def deactivate(self):
        """Deactivate the powerup, making it unavailable for collection."""
        self.active = False
        logger.debug(f"Powerup {self.id} deactivated")

    def update(self):
        """Update the powerup state each frame."""
        current_time = pygame.time.get_ticks()

        # Check if powerup has expired
        if current_time - self.creation_time > self.lifespan:
            logger.debug(f"Powerup {self.id} expired")
            self.kill()
            return

        # Update pulsing animation
        self.pulse_factor = (math.sin(current_time * self.pulse_speed * 0.001) + 1) / 2

        # Recreate the image with the new pulse size
        prev_center = self.rect.center
        self._create_image()
        self.rect = self.image.get_rect(center=prev_center)
