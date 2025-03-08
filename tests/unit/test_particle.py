"""Unit tests for the Particle and ParticleSystem classes."""

import pytest
import pygame
import time
from unittest.mock import MagicMock, patch
from objects.particle import Particle, ParticleSystem
from utils.logger import GameLogger

# Initialize pygame for testing
pygame.init()

# Set up logger for tests
logger = GameLogger.get_logger("test_particle")


class TestParticle:
    """Tests for the Particle class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        # Create a test surface
        self.screen = pygame.Surface((800, 600))

        # Create a basic particle for testing
        self.position = (400, 300)
        self.velocity = (2.0, -1.5)
        self.color = (255, 200, 0)  # Yellow
        self.size = 5
        self.lifetime = 500  # ms
        self.particle = Particle(self.position, self.velocity, self.color, self.size, self.lifetime)

    def test_init(self):
        """Test particle initialization."""
        # Check initial properties
        assert self.particle.position[0] == self.position[0]
        assert self.particle.position[1] == self.position[1]
        assert self.particle.velocity[0] == self.velocity[0]
        assert self.particle.velocity[1] == self.velocity[1]
        assert self.particle.color == self.color
        assert self.particle.size == self.size
        assert self.particle.lifetime == self.lifetime
        assert self.particle.fade_out is True  # Default value
        assert self.particle.original_alpha == 255

        # Check that the image was created correctly
        assert self.particle.image.get_size() == (self.size, self.size)
        assert self.particle.rect.center == self.position

    def test_update_position(self):
        """Test particle position update."""
        # Store initial position
        initial_x = self.particle.position[0]
        initial_y = self.particle.position[1]

        # Update particle
        self.particle.update()

        # Check that position changed according to velocity
        assert self.particle.position[0] == initial_x + self.velocity[0]
        assert self.particle.position[1] == initial_y + self.velocity[1]
        assert self.particle.rect.center == (
            int(self.particle.position[0]),
            int(self.particle.position[1]),
        )

    def test_update_with_gravity(self):
        """Test particle update with gravity."""
        # Create a particle with gravity
        gravity_particle = Particle(
            self.position, self.velocity, self.color, self.size, self.lifetime, gravity=0.5
        )

        # Store initial velocity
        initial_vy = gravity_particle.velocity[1]

        # Update particle
        gravity_particle.update()

        # Check that velocity changed due to gravity
        assert gravity_particle.velocity[1] == initial_vy + 0.5

    @patch("pygame.time.get_ticks")
    def test_particle_fades_out(self, mock_get_ticks):
        """Test that particle fades out over time."""
        # Mock time progression
        mock_get_ticks.return_value = 100  # Born time
        fade_particle = Particle(
            self.position,
            self.velocity,
            self.color,
            self.size,
            1000,  # 1000ms lifetime
            fade_out=True,
        )

        # First update - 25% through lifetime
        mock_get_ticks.return_value = 350  # 250ms later (25% of lifetime)
        fade_particle.update()

        # Check alpha value (should be around 75% of original)
        expected_alpha = int(0.75 * 255)
        assert abs(fade_particle.alpha - expected_alpha) <= 5  # Allow small rounding difference

        # Second update - 75% through lifetime
        mock_get_ticks.return_value = 850  # 750ms later (75% of lifetime)
        fade_particle.update()

        # Check alpha value (should be around 25% of original)
        expected_alpha = int(0.25 * 255)
        assert abs(fade_particle.alpha - expected_alpha) <= 5  # Allow small rounding difference

    @patch("pygame.time.get_ticks")
    def test_particle_dies_after_lifetime(self, mock_get_ticks):
        """Test that particle is killed after its lifetime expires."""
        # Create a test sprite group
        test_group = pygame.sprite.Group()

        # Mock time points
        mock_get_ticks.return_value = 1000  # Born time
        death_particle = Particle(
            self.position, self.velocity, self.color, self.size, 500  # 500ms lifetime
        )

        # Add the particle to a sprite group so alive() works correctly
        test_group.add(death_particle)

        # Before lifetime ends
        mock_get_ticks.return_value = 1400  # 400ms passed (not dead yet)
        death_particle.update()
        assert death_particle.alive()  # Should still be alive

        # After lifetime ends
        mock_get_ticks.return_value = 1600  # 600ms passed (should be dead)
        death_particle.update()
        assert not death_particle.alive()  # Should be dead


class TestParticleSystem:
    """Tests for the ParticleSystem class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        # Create a test surface
        self.screen = pygame.Surface((800, 600))

        # Patch the config manager
        self.config_patcher = patch("objects.particle.config")
        self.mock_config = self.config_patcher.start()

        # Configure the mock
        self.mock_config.get.side_effect = self._mock_config_get
        self.mock_config.get_color.return_value = (255, 0, 0)  # Red

        # Create the particle system
        self.particle_system = ParticleSystem()

    def teardown_method(self):
        """Clean up after each test method."""
        self.config_patcher.stop()

    def _mock_config_get(self, *args, **kwargs):
        """Mock implementation of config.get."""
        if args[0] == "particles" and args[1] == "enabled":
            return kwargs.get("default", True)

        if args[0] == "particles" and args[1] == "types" and args[2] == "hit":
            return {
                "count": 10,
                "min_speed": 1.0,
                "max_speed": 3.0,
                "min_lifetime": 400,
                "max_lifetime": 800,
                "colors": ["red", "orange"],
                "size_range": [3, 6],
                "gravity": 0.1,
                "fade_out": True,
            }

        if args[0] == "particles" and args[1] == "types" and args[2] == "death":
            return {
                "count": 15,
                "min_speed": 2.0,
                "max_speed": 4.0,
                "min_lifetime": 500,
                "max_lifetime": 1000,
                "colors": ["red", "dark_red"],
                "size_range": [4, 8],
                "gravity": 0.05,
                "fade_out": True,
            }

        return kwargs.get("default", None)

    def test_init(self):
        """Test particle system initialization."""
        assert self.particle_system.particles is not None
        assert len(self.particle_system.particles) == 0
        assert self.particle_system.enabled is True

    def test_create_particles(self):
        """Test creating particles."""
        # Create hit particles
        position = (300, 200)
        self.particle_system.create_particles(position, "hit")

        # Should create 10 particles based on our mock config
        assert len(self.particle_system.particles) == 10

        # All particles should be at or near the specified position
        for particle in self.particle_system.particles:
            # Particles start at the position but may have moved slightly in the first frame
            # So we check they're within a small range of the starting position
            assert abs(particle.position[0] - position[0]) < 10
            assert abs(particle.position[1] - position[1]) < 10

    def test_create_different_particle_types(self):
        """Test creating different types of particles."""
        # Create hit particles
        self.particle_system.create_particles((300, 200), "hit")
        hit_count = len(self.particle_system.particles)

        # Create death particles
        self.particle_system.create_particles((400, 300), "death")
        death_count = len(self.particle_system.particles) - hit_count

        # Should create particles according to the config
        assert hit_count == 10
        assert death_count == 15

    def test_update_particles(self):
        """Test updating particles."""
        # Create some particles
        self.particle_system.create_particles((300, 200), "hit")
        initial_positions = [(p.position[0], p.position[1]) for p in self.particle_system.particles]

        # Update the particles
        self.particle_system.update()

        # All particles should have moved
        for i, particle in enumerate(self.particle_system.particles):
            assert (particle.position[0], particle.position[1]) != initial_positions[i]

    def test_draw_particles(self):
        """Test drawing particles to a surface."""
        # Create some particles
        self.particle_system.create_particles((300, 200), "hit")

        # Get a clean test surface
        test_surface = pygame.Surface((800, 600))

        # Draw particles
        self.particle_system.draw(test_surface)

        # This is hard to test definitively without checking pixels
        # So we'll just ensure the method doesn't crash
        assert True

    def test_clear_particles(self):
        """Test clearing all particles."""
        # Create some particles
        self.particle_system.create_particles((300, 200), "hit")
        assert len(self.particle_system.particles) > 0

        # Clear particles
        self.particle_system.clear()

        # Should have no particles left
        assert len(self.particle_system.particles) == 0

    def test_disabled_particle_system(self):
        """Test that disabled particle system doesn't create particles."""
        # Disable the particle system
        self.particle_system.enabled = False

        # Try to create particles
        self.particle_system.create_particles((300, 200), "hit")

        # Should not create any particles when disabled
        assert len(self.particle_system.particles) == 0
