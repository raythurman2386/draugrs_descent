import pygame
import random
import math
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

        # Apply screen shake if active
        self._update_screen_shake()

        logger.debug(f"Camera updated: x={x}, y={y}")

    def _update_screen_shake(self):
        """Update screen shake effect if active."""
        if self.shake_duration > 0:
            # Calculate how much time has passed since the shake started
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.shake_start_time

            # Check if shake should still be active
            if elapsed < self.shake_duration:
                # Calculate remaining shake intensity (decreases over time)
                remaining_percentage = 1.0 - (elapsed / self.shake_duration)
                current_intensity = self.shake_intensity * remaining_percentage

                # Generate random shake offset - use a more pronounced shake pattern
                # Alternate between positive and negative values for more visible effect
                shake_x = random.uniform(-current_intensity, current_intensity)
                shake_y = random.uniform(-current_intensity, current_intensity)

                # Add a sine wave component to make the shake more fluid
                time_factor = elapsed / 30  # Adjust for speed of oscillation
                sine_component = math.sin(time_factor) * current_intensity * 0.5

                # Combine random and sine components
                self.shake_offset = (int(shake_x + sine_component), int(shake_y))

                # Log the shake offset to verify it's being applied
                logger.debug(f"Screen shake offset: {self.shake_offset}")
            else:
                # Shake duration has ended
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
            Pygame rect with camera offset applied
        """
        # Apply base camera offset plus any shake offset
        offset_x = self.camera.x + self.shake_offset[0]
        offset_y = self.camera.y + self.shake_offset[1]
        return entity.rect.move(offset_x, offset_y)

    def apply_rect(self, rect):
        """
        Apply camera offset to a rect.

        Args:
            rect: Pygame Rect to offset

        Returns:
            Pygame rect with camera offset applied
        """
        # Apply base camera offset plus any shake offset
        offset_x = self.camera.x + self.shake_offset[0]
        offset_y = self.camera.y + self.shake_offset[1]
        return rect.move(offset_x, offset_y)

    def get_offset(self):
        """
        Get the current camera offset.

        Returns:
            Tuple (x, y) with the current camera offset
        """
        # Include shake offset in the camera offset
        return (self.camera.x + self.shake_offset[0], self.camera.y + self.shake_offset[1])
