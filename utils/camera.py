import pygame
import random
import math
from utils.logger import GameLogger

# Get a logger for the camera system
logger = GameLogger.get_logger("camera")


class Camera:
    """Camera system for tracking player and moving the game world with screen shake."""

    def __init__(self, map_width, map_height, screen_width, screen_height):
        """
        Initialize the camera.

        Args:
            map_width (int): Width of the entire map in pixels
            map_height (int): Height of the entire map in pixels
            screen_width (int): Width of the game screen
            screen_height (int): Height of the game screen
        """
        self.camera = pygame.Rect(0, 0, map_width, map_height)
        self.width = map_width
        self.height = map_height
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.half_screen_width = int(screen_width / 2)
        self.half_screen_height = int(screen_height / 2)

        # Screen shake properties
        self.shake_duration = 0
        self.shake_intensity = 0
        self.shake_start_time = 0
        self.shake_offset = (0, 0)

        logger.debug(f"Camera initialized: {self.camera}")

    def update(self, target):
        """
        Update camera position to follow the target.

        Args:
            target: The target object (usually player) to follow, with a rect attribute
        """
        # Calculate the center point where we want the camera to focus
        x = -target.rect.centerx + self.half_screen_width
        y = -target.rect.centery + self.half_screen_height

        # Limit scrolling to map boundaries if the map is larger than the screen
        if self.width > self.screen_width:
            x = min(0, x)  # Left boundary
            x = max(-(self.width - self.screen_width), x)  # Right boundary

        if self.height > self.screen_height:
            y = min(0, y)  # Top boundary
            y = max(-(self.height - self.screen_height), y)  # Bottom boundary

        # Update camera position
        self.camera.x = x
        self.camera.y = y

        # Apply screen shake if active
        self._update_screen_shake()

        logger.debug(f"Camera updated: x={x}, y={y}")

    def _update_screen_shake(self):
        """Update screen shake effect if active."""
        if self.shake_duration > 0:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.shake_start_time
            if elapsed < self.shake_duration:
                remaining_percentage = 1.0 - (elapsed / self.shake_duration)
                current_intensity = self.shake_intensity * remaining_percentage
                # Slower oscillation for a more noticeable shake
                time_factor = elapsed / 100  # Adjusted for smoother effect
                sine_component = math.sin(time_factor) * current_intensity * 0.5
                shake_x = random.uniform(-current_intensity, current_intensity)
                shake_y = random.uniform(-current_intensity, current_intensity)
                self.shake_offset = (int(shake_x + sine_component), int(shake_y))
                logger.debug(f"Screen shake offset: {self.shake_offset}")
            else:
                self.shake_duration = 0
                self.shake_offset = (0, 0)
                logger.debug("Screen shake ended")

    def start_screen_shake(self, duration, intensity):
        """
        Start a screen shake effect.

        Args:
            duration (int): Duration of the shake in milliseconds
            intensity (float): Maximum pixel offset for the shake
        """
        self.shake_duration = duration
        self.shake_intensity = intensity
        self.shake_start_time = pygame.time.get_ticks()
        logger.debug(f"Screen shake started: duration={duration}ms, intensity={intensity}")

    def apply(self, entity):
        """
        Apply camera offset to an entity.

        Args:
            entity: Entity with a rect attribute to offset

        Returns:
            pygame.Rect: Rect with camera offset applied
        """
        offset_x = self.camera.x + self.shake_offset[0]
        offset_y = self.camera.y + self.shake_offset[1]
        return pygame.Rect(
            entity.rect.x + offset_x,
            entity.rect.y + offset_y,
            entity.rect.width,
            entity.rect.height,
        )

    def apply_rect(self, rect):
        """
        Apply camera offset to a rect.

        Args:
            rect (pygame.Rect): Pygame Rect to offset

        Returns:
            pygame.Rect: Rect with camera offset applied
        """
        offset_x = self.camera.x + self.shake_offset[0]
        offset_y = self.camera.y + self.shake_offset[1]
        return rect.move(offset_x, offset_y)

    def get_offset(self):
        """
        Get the current camera offset.

        Returns:
            tuple: (x, y) with the current camera offset
        """
        return (self.camera.x + self.shake_offset[0], self.camera.y + self.shake_offset[1])

    def reset(self):
        """Reset the camera to its initial state."""
        self.camera.x = 0
        self.camera.y = 0
        self.shake_duration = 0
        self.shake_intensity = 0
        self.shake_start_time = 0
        self.shake_offset = (0, 0)
        logger.debug("Camera reset to initial state")
