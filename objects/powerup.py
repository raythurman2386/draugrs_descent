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

    def __init__(self, position, powerup_type):
        """Initialize a powerup at the given position with the specified type.

        Args:
            position (tuple): The (x, y) coordinates for the powerup.
            powerup_type (str): The type of powerup ("health", "shield", etc.)
        """
        super().__init__()

        # Assign a unique ID to each powerup
        self.id = Powerup.next_id
        Powerup.next_id += 1

        self.type = powerup_type
        self.active = True
        self.creation_time = pygame.time.get_ticks()
        self.lifespan = config.get(
            "powerups", "attributes", "lifespan", default=10000
        )  # 10 seconds lifespan

        # Animation properties
        self.base_size = (
            config.get("powerups", "dimensions", "width", default=30),
            config.get("powerups", "dimensions", "height", default=30),
        )
        self.pulse_factor = 0
        self.pulse_speed = 0.1
        self.pulse_size = 4  # Max amount to pulse

        # Create the powerup sprite with initial size
        self._create_image()
        self.rect = self.image.get_rect()
        self.rect.center = position
        self._orig_center = position  # Store original center for animation

        logger.debug(f"Powerup {self.id} of type {powerup_type} created at position {position}")

    def _create_image(self):
        """Create the powerup image with the current pulse size."""
        # Calculate current size based on pulse
        pulse_offset = self.pulse_factor * self.pulse_size
        current_width = self.base_size[0] + pulse_offset
        current_height = self.base_size[1] + pulse_offset

        # Create the surface
        self.image = pygame.Surface((int(current_width), int(current_height)))
        color = config.get(
            "powerups", "colors", self.type, default=(255, 255, 255)
        )  # Default to white if type not found
        self.image.fill(color)

        # Add a visual indicator for the powerup type
        if self.type == "health":
            # Add a plus sign for health
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
            # Add a circle for shield
            pygame.draw.circle(
                self.image,
                (255, 255, 255),
                (int(current_width / 2), int(current_height / 2)),
                int(min(current_width, current_height) / 3),
                2,
            )
        elif self.type == "weapon":
            # Add a lightning bolt for weapon boost
            points = [
                (int(current_width / 2), int(current_height / 4)),  # Top middle
                (
                    int(current_width / 2 + current_width / 5),
                    int(current_height / 2),
                ),  # Right middle
                (int(current_width / 2), int(current_height / 2)),  # Center
                (
                    int(current_width / 2 - current_width / 5),
                    int(current_height * 3 / 4),
                ),  # Bottom left
            ]
            pygame.draw.lines(self.image, (255, 255, 255), False, points, 2)

    def apply_effect(self, player):
        """Apply the powerup effect to the player.

        Args:
            player: The player object to apply the effect to.

        Returns:
            bool: True if the effect was applied successfully.
        """
        if not self.active:
            return False

        if self.type == "health":
            # Restore health
            original_health = player.current_health
            player.current_health = min(
                player.current_health
                + config.get("powerups", "effects", "health_restore", default=30),
                player.max_health,
            )
            health_gained = player.current_health - original_health
            logger.info(
                f"Health powerup applied. Player gained {health_gained} health. Health now: {player.current_health}/{player.max_health}"
            )

        elif self.type == "shield":
            # Provide temporary invincibility
            player.invincible = True
            player.invincible_timer = pygame.time.get_ticks()
            player.invincible_duration = config.get(
                "powerups", "effects", "shield_duration", default=5000
            )
            logger.info(
                f"Shield powerup applied. Player invincible for {config.get('powerups', 'effects', 'shield_duration', default=5000)}ms"
            )

        elif self.type == "weapon":
            # Apply weapon boost (increased fire rate)
            player.activate_weapon_boost(
                config.get("powerups", "effects", "weapon_boost_duration", default=10000)
            )
            logger.info(
                f"Weapon boost powerup applied. Player's fire rate increased for {config.get('powerups', 'effects', 'weapon_boost_duration', default=10000)}ms"
            )

        # Deactivate the powerup after use
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
        self.pulse_factor = (
            math.sin(current_time * self.pulse_speed * 0.001) + 1
        ) / 2  # Value between 0 and 1

        # Recreate the image with the new pulse size
        prev_center = self.rect.center
        self._create_image()
        self.rect = self.image.get_rect()
        self.rect.center = prev_center
