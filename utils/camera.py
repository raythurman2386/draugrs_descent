import pygame
from utils.logger import GameLogger

# Get a logger for the camera system
logger = GameLogger.get_logger("camera")


class Camera:
    """Camera system for tracking player and moving the game world."""

    def __init__(self, map_width, map_height, screen_width, screen_height):
        """
        Initialize the camera.

        Args:
            map_width: Width of the entire map in pixels
            map_height: Height of the entire map in pixels
            screen_width: Width of the game screen
            screen_height: Height of the game screen
        """
        self.camera = pygame.Rect(0, 0, map_width, map_height)
        self.width = map_width
        self.height = map_height
        self.screen_width = screen_width
        self.screen_height = screen_height
        logger.debug(f"Camera initialized: {self.camera}")

    def update(self, target):
        """
        Update camera position to follow the target.

        Args:
            target: The target object (usually player) to follow
        """
        # Calculate the center point where we want the camera to focus
        x = -target.rect.centerx + int(self.screen_width / 2)
        y = -target.rect.centery + int(self.screen_height / 2)

        # Limit scrolling to map boundaries
        # Only clamp camera if the map is larger than the screen
        # This fixes the "invisible wall" issue by only applying boundaries when necessary
        if self.width > self.screen_width:
            x = min(0, x)  # Left boundary
            x = max(-(self.width - self.screen_width), x)  # Right boundary

        if self.height > self.screen_height:
            y = min(0, y)  # Top boundary
            y = max(-(self.height - self.screen_height), y)  # Bottom boundary

        # Update camera position
        self.camera.x = x
        self.camera.y = y
        logger.debug(f"Camera updated: x={x}, y={y}")

    def apply(self, entity):
        """
        Apply camera offset to an entity.

        Args:
            entity: Entity with a rect attribute to offset

        Returns:
            Pygame rect with camera offset applied
        """
        return entity.rect.move(self.camera.topleft)

    def apply_rect(self, rect):
        """
        Apply camera offset to a rect.

        Args:
            rect: Pygame Rect to offset

        Returns:
            Pygame rect with camera offset applied
        """
        return rect.move(self.camera.topleft)

    def get_offset(self):
        """
        Get the current camera offset.

        Returns:
            Tuple (x, y) with the current camera offset
        """
        return self.camera.topleft
