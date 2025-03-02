import pygame
from utils.logger import GameLogger
from constants import (
    POWERUP_WIDTH,
    POWERUP_HEIGHT,
    POWERUP_COLORS,
    POWERUP_HEALTH_RESTORE,
    POWERUP_SHIELD_DURATION,
)

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

        # Create the powerup sprite
        self.image = pygame.Surface((POWERUP_WIDTH, POWERUP_HEIGHT))
        color = POWERUP_COLORS.get(
            powerup_type, (255, 255, 255)
        )  # Default to white if type not found
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.center = position

        logger.debug(
            f"Powerup {self.id} of type {powerup_type} created at position {position}"
        )

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
            player.current_health = min(
                player.current_health + POWERUP_HEALTH_RESTORE, player.max_health
            )
            logger.info(
                f"Health powerup applied. Player health now: {player.current_health}/{player.max_health}"
            )

        elif self.type == "shield":
            # Provide temporary invincibility
            player.invincible = True
            player.invincible_timer = pygame.time.get_ticks()
            player.invincible_duration = POWERUP_SHIELD_DURATION
            logger.info(
                f"Shield powerup applied. Player invincible for {POWERUP_SHIELD_DURATION}ms"
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
        # Add any animation or movement logic here if needed
        pass
