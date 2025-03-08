import pygame
import random
import math
from utils.logger import GameLogger
from managers import config

# Get a logger for the particle module
logger = GameLogger.get_logger("particle")


class Particle(pygame.sprite.Sprite):
    """Individual particle for visual effects."""

    def __init__(
        self,
        position: tuple[float, float],
        velocity: tuple[float, float],
        color: tuple[int, int, int],
        size: int,
        lifetime: int,
        gravity: float = 0.0,
        fade_out: bool = True,
    ):
        super().__init__()
        self.position = [float(position[0]), float(position[1])]  # Float for precision
        self.velocity = list(velocity)
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.born_time = pygame.time.get_ticks()
        self.gravity = gravity
        self.fade_out = fade_out
        self.original_alpha = 255
        self.alpha = self.original_alpha

        # Create particle surface
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (size // 2, size // 2), size // 2)
        self.rect = self.image.get_rect(center=(int(position[0]), int(position[1])))
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        """Update particle position, velocity, and appearance."""
        current_time = pygame.time.get_ticks()
        time_alive = current_time - self.born_time
        if time_alive >= self.lifetime:
            self.kill()
            return

        life_ratio = 1.0 - (time_alive / self.lifetime)
        self.velocity[1] += self.gravity
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        self.rect.center = (int(self.position[0]), int(self.position[1]))
        if self.fade_out:
            self.alpha = int(life_ratio * self.original_alpha)
            self.image.set_alpha(self.alpha)


class ParticleSystem:
    """System for managing particle effects."""

    def __init__(self):
        """Initialize the particle system."""
        self.particles = pygame.sprite.Group()
        self.enabled = config.get("particles", "enabled", default=True)
        self.camera_offset = (0, 0)
        # Cache particle configurations
        self.particle_configs = {
            "hit": config.get(
                "particles",
                "types",
                "hit",
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
            ),
            "death": config.get(
                "particles",
                "types",
                "death",
                default={
                    "count": 10,
                    "min_speed": 2.0,
                    "max_speed": 5.0,
                    "min_lifetime": 1000,
                    "max_lifetime": 1500,
                    "colors": ["red", "orange"],
                    "size_range": [5, 10],
                    "gravity": 0.1,
                    "fade_out": True,
                },
            ),
            "powerup": config.get(
                "particles",
                "types",
                "powerup",
                default={
                    "count": 15,
                    "min_speed": 0.5,
                    "max_speed": 2.0,
                    "min_lifetime": 800,
                    "max_lifetime": 1200,
                    "colors": ["yellow", "green"],
                    "size_range": [2, 4],
                    "gravity": -0.05,
                    "fade_out": True,
                },
            ),
        }
        logger.debug(f"Particle system initialized. Enabled: {self.enabled}")

    def set_camera_offset(self, offset: tuple[int, int]):
        """Set the current camera offset for proper positioning."""
        self.camera_offset = offset

    def create_particles(self, position: tuple[float, float], particle_type: str):
        """Create a burst of particles at the specified position."""
        if not self.enabled:
            return

        # Use cached configuration
        particle_config = self.particle_configs.get(particle_type, self.particle_configs["hit"])
        count = particle_config["count"]
        min_speed = particle_config["min_speed"]
        max_speed = particle_config["max_speed"]
        min_lifetime = particle_config["min_lifetime"]
        max_lifetime = particle_config["max_lifetime"]
        color_names = particle_config["colors"]
        size_range = particle_config["size_range"]
        gravity = particle_config["gravity"]
        fade_out = particle_config["fade_out"]

        colors = [config.get_color(color_name) for color_name in color_names]

        for _ in range(count):
            color = random.choice(colors)
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(min_speed, max_speed)
            velocity_x = math.cos(angle) * speed
            velocity_y = math.sin(angle) * speed
            lifetime = random.randint(min_lifetime, max_lifetime)
            size = random.randint(size_range[0], size_range[1])
            particle = Particle(
                position, (velocity_x, velocity_y), color, size, lifetime, gravity, fade_out
            )
            self.particles.add(particle)

    def update(self):
        """Update all particles."""
        self.particles.update()

    def draw(self, surface: pygame.Surface):
        """Draw all particles to the surface with camera offset applied."""
        for particle in self.particles:
            original_center = particle.rect.center
            particle.rect.center = (
                int(particle.position[0] + self.camera_offset[0]),
                int(particle.position[1] + self.camera_offset[1]),
            )
        self.particles.draw(surface)
        for particle in self.particles:
            particle.rect.center = original_center

    def clear(self):
        """Remove all particles."""
        self.particles.empty()
