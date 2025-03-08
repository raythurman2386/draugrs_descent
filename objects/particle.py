import pygame
import random
import math
from utils.logger import GameLogger
from managers import config

# Get a logger for the particle module
logger = GameLogger.get_logger("particle")


class Particle(pygame.sprite.Sprite):
    """Individual particle for visual effects."""

    def __init__(self, position, velocity, color, size, lifetime, gravity=0.0, fade_out=True):
        super().__init__()
        # Use exact position (converted to integers for rect placement)
        self.position = [float(position[0]), float(position[1])]
        self.velocity = list(velocity)
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.born_time = pygame.time.get_ticks()
        self.gravity = gravity
        self.fade_out = fade_out
        self.original_alpha = 255  # Start with full opacity
        self.alpha = self.original_alpha

        # Create the particle surface - centered on the position
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (size // 2, size // 2), size // 2)
        self.rect = self.image.get_rect()

        # Position the rect so its center is exactly at the specified position
        self.rect.center = (int(position[0]), int(position[1]))

        # Create mask for pixel-perfect collision detection
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        """Update the particle position, velocity, and appearance."""
        # Get current time to calculate lifetime progress
        current_time = pygame.time.get_ticks()
        time_alive = current_time - self.born_time

        # Check if particle has expired
        if time_alive >= self.lifetime:
            self.kill()
            return

        # Calculate remaining lifetime percentage
        life_ratio = 1.0 - (time_alive / self.lifetime)

        # Apply gravity effect
        self.velocity[1] += self.gravity

        # Update position based on velocity
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        self.rect.center = (int(self.position[0]), int(self.position[1]))

        # Apply fading effect if enabled
        if self.fade_out:
            self.alpha = int(life_ratio * self.original_alpha)
            self.image.set_alpha(self.alpha)


class ParticleSystem:
    """System for managing particle effects."""

    def __init__(self):
        """Initialize the particle system."""
        self.particles = pygame.sprite.Group()
        self.enabled = config.get("particles", "enabled", default=True)
        self.camera_offset = (0, 0)  # Default to no offset
        logger.debug(f"Particle system initialized. Enabled: {self.enabled}")

    def set_camera_offset(self, offset):
        """Set the current camera offset for proper positioning.

        Args:
            offset (tuple): Camera offset (x, y)
        """
        self.camera_offset = offset

    def create_particles(self, position, particle_type):
        """Create a burst of particles at the specified position.

        Args:
            position (tuple): (x, y) position to create particles at (in world coordinates)
            particle_type (str): Type of particles to create (hit, death, etc.)
        """
        if not self.enabled:
            return

        # Get particle configuration for the specified type
        particle_config = config.get(
            "particles",
            "types",
            particle_type,
            default={
                "count": 5,
                "min_speed": 1.0,
                "max_speed": 3.0,
                "min_lifetime": 500,
                "max_lifetime": 1000,
                "colors": ["white"],
                "size_range": [3, 5],
                "gravity": 0.0,
                "fade_out": True,
            },
        )

        # Extract configuration values
        count = particle_config.get("count", 5)
        min_speed = particle_config.get("min_speed", 1.0)
        max_speed = particle_config.get("max_speed", 3.0)
        min_lifetime = particle_config.get("min_lifetime", 500)
        max_lifetime = particle_config.get("max_lifetime", 1000)
        color_names = particle_config.get("colors", ["white"])
        size_range = particle_config.get("size_range", [3, 5])
        gravity = particle_config.get("gravity", 0.0)
        fade_out = particle_config.get("fade_out", True)

        # Convert color names to RGB values
        colors = [config.get_color(color_name) for color_name in color_names]

        # Create particles
        for _ in range(count):
            # Select a random color from the available colors
            color = random.choice(colors)

            # Generate a random angle around the circle (0-360 degrees)
            angle = random.uniform(0, 2 * math.pi)

            # Generate a random speed between min and max speeds
            speed = random.uniform(min_speed, max_speed)

            # Calculate velocity components for even distribution in all directions
            velocity_x = math.cos(angle) * speed
            velocity_y = math.sin(angle) * speed

            # Random lifetime
            lifetime = random.randint(min_lifetime, max_lifetime)

            # Random size
            size = random.randint(size_range[0], size_range[1])

            # Create and add the particle
            particle = Particle(
                position,
                (velocity_x, velocity_y),
                color,
                size,
                lifetime,
                gravity=gravity,
                fade_out=fade_out,
            )
            self.particles.add(particle)

    def update(self):
        """Update all particles."""
        self.particles.update()

    def draw(self, surface):
        """Draw all particles to the surface with camera offset applied."""
        # We need to temporarily adjust each particle's rect for drawing
        # This doesn't change their actual world positions
        for particle in self.particles:
            # Store the original rect position
            original_center = particle.rect.center

            # Apply camera offset for drawing
            particle.rect.centerx = int(particle.position[0] + self.camera_offset[0])
            particle.rect.centery = int(particle.position[1] + self.camera_offset[1])

        # Draw all particles
        self.particles.draw(surface)

        # Restore original positions
        for particle in self.particles:
            particle.rect.center = (int(particle.position[0]), int(particle.position[1]))

    def clear(self):
        """Remove all particles."""
        self.particles.empty()
