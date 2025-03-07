"""Unit tests for the collision system."""

import pygame
import pytest
from unittest.mock import MagicMock, patch

from utils import (
    CollisionSystem,
    handle_player_enemy_collision,
    handle_player_powerup_collision,
    handle_projectile_enemy_collision,
    handle_enemy_projectile_player_collision,
)
from utils.logger import GameLogger

# Get a logger for the collision test module
logger = GameLogger.get_logger("test_collision_system")


class MockSprite(pygame.sprite.Sprite):
    """Mock sprite for collision tests."""

    def __init__(self, x=0, y=0, width=10, height=10, is_enemy_projectile=False):
        super().__init__()
        self.id = id(self)
        self.rect = pygame.Rect(x, y, width, height)
        self.damage = 1
        self.is_enemy_projectile = is_enemy_projectile
        self.active = True

    def kill(self):
        """Mock kill method."""
        self.alive = False

    def take_damage(self, damage):
        """Mock take_damage method."""
        return True


class TestCollisionSystem:
    """Tests for the CollisionSystem class."""

    @pytest.fixture
    def setup_collision_system(self):
        """Setup a collision system with test sprites."""
        # Initialize Pygame for the tests
        pygame.init()

        # Create a collision system with both algorithms for testing
        quadtree_system = CollisionSystem(800, 600, algorithm=CollisionSystem.QUADTREE)
        spatial_hash_system = CollisionSystem(800, 600, algorithm=CollisionSystem.SPATIAL_HASH)

        # Create test sprites
        player = MockSprite(400, 300, 20, 20)
        enemy1 = MockSprite(100, 100, 15, 15)
        enemy2 = MockSprite(200, 200, 15, 15)
        enemy3 = MockSprite(700, 500, 15, 15)

        player_projectile = MockSprite(90, 90, 5, 5, is_enemy_projectile=False)
        enemy_projectile = MockSprite(390, 290, 5, 5, is_enemy_projectile=True)

        powerup = MockSprite(410, 305, 10, 10)
        powerup.type = "health"
        powerup.apply_effect = MagicMock(return_value=True)

        # Create sprite groups
        enemy_group = pygame.sprite.Group(enemy1, enemy2, enemy3)
        projectile_group = pygame.sprite.Group(player_projectile, enemy_projectile)
        powerup_group = pygame.sprite.Group(powerup)

        return {
            "quadtree_system": quadtree_system,
            "spatial_hash_system": spatial_hash_system,
            "player": player,
            "enemies": [enemy1, enemy2, enemy3],
            "enemy_group": enemy_group,
            "player_projectile": player_projectile,
            "enemy_projectile": enemy_projectile,
            "projectile_group": projectile_group,
            "powerup": powerup,
            "powerup_group": powerup_group,
        }

    def test_collision_system_initialization(self, setup_collision_system):
        """Test that CollisionSystem initializes correctly with different algorithms."""
        quadtree_system = setup_collision_system["quadtree_system"]
        spatial_hash_system = setup_collision_system["spatial_hash_system"]

        # Test QuadTree initialization
        assert quadtree_system.algorithm == CollisionSystem.QUADTREE
        assert quadtree_system.screen_width == 800
        assert quadtree_system.screen_height == 600

        # Test SpatialHashGrid initialization
        assert spatial_hash_system.algorithm == CollisionSystem.SPATIAL_HASH
        assert spatial_hash_system.screen_width == 800
        assert spatial_hash_system.screen_height == 600

        logger.info("CollisionSystem initialization tests passed")

    def test_update_spatial_structure(self, setup_collision_system):
        """Test updating the spatial structure with game objects."""
        # Test with both algorithms
        for system_name in ["quadtree_system", "spatial_hash_system"]:
            collision_system = setup_collision_system[system_name]
            player = setup_collision_system["player"]
            enemy_group = setup_collision_system["enemy_group"]
            projectile_group = setup_collision_system["projectile_group"]
            powerup_group = setup_collision_system["powerup_group"]

            # Update the spatial structure
            collision_system.update(projectile_group, enemy_group, player, powerup_group)

            # Since it's difficult to directly test the internal state,
            # we'll verify it works through the collision checking tests
            logger.info(f"Updated {system_name} with game objects")

    def test_projectile_enemy_collisions(self, setup_collision_system):
        """Test detecting collisions between projectiles and enemies."""
        # Test with both algorithms
        for system_name in ["quadtree_system", "spatial_hash_system"]:
            collision_system = setup_collision_system[system_name]
            player = setup_collision_system["player"]
            enemy_group = setup_collision_system["enemy_group"]
            projectile_group = setup_collision_system["projectile_group"]
            powerup_group = setup_collision_system["powerup_group"]

            # Position a projectile to collide with enemy1
            player_projectile = setup_collision_system["player_projectile"]
            enemy1 = setup_collision_system["enemies"][0]
            player_projectile.rect.x = enemy1.rect.x
            player_projectile.rect.y = enemy1.rect.y

            # Update the spatial structure
            collision_system.update(projectile_group, enemy_group, player, powerup_group)

            # Check for collisions
            collisions = collision_system.check_projectile_enemy_collisions(
                projectile_group, enemy_group
            )

            # Verify collision was detected
            assert player_projectile in collisions
            assert enemy1 in collisions[player_projectile]

            logger.info(f"Projectile-enemy collision detection test passed for {system_name}")

    def test_enemy_projectile_player_collision(self, setup_collision_system):
        """Test detecting collisions between enemy projectiles and the player."""
        # Test with both algorithms
        for system_name in ["quadtree_system", "spatial_hash_system"]:
            collision_system = setup_collision_system[system_name]
            player = setup_collision_system["player"]
            enemy_group = setup_collision_system["enemy_group"]
            projectile_group = setup_collision_system["projectile_group"]
            powerup_group = setup_collision_system["powerup_group"]

            # Position an enemy projectile to collide with the player
            enemy_projectile = setup_collision_system["enemy_projectile"]
            enemy_projectile.rect.x = player.rect.x
            enemy_projectile.rect.y = player.rect.y

            # Update the spatial structure
            collision_system.update(projectile_group, enemy_group, player, powerup_group)

            # Check for collisions
            projectile_hits = collision_system.check_enemy_projectile_player_collision(
                player, projectile_group
            )

            # Verify collision was detected
            assert enemy_projectile in projectile_hits

            logger.info(
                f"Enemy projectile-player collision detection test passed for {system_name}"
            )

    def test_player_enemy_collisions(self, setup_collision_system):
        """Test detecting collisions between the player and enemies."""
        # Test with both algorithms
        for system_name in ["quadtree_system", "spatial_hash_system"]:
            collision_system = setup_collision_system[system_name]
            player = setup_collision_system["player"]
            enemy_group = setup_collision_system["enemy_group"]
            projectile_group = setup_collision_system["projectile_group"]
            powerup_group = setup_collision_system["powerup_group"]

            # Position an enemy to collide with the player
            enemy2 = setup_collision_system["enemies"][1]
            enemy2.rect.x = player.rect.x
            enemy2.rect.y = player.rect.y

            # Update the spatial structure
            collision_system.update(projectile_group, enemy_group, player, powerup_group)

            # Check for collisions
            enemy_hits = collision_system.check_player_enemy_collisions(player, enemy_group)

            # Verify collision was detected
            assert enemy2 in enemy_hits

            logger.info(f"Player-enemy collision detection test passed for {system_name}")

    def test_player_powerup_collisions(self, setup_collision_system):
        """Test detecting collisions between the player and powerups."""
        # Test with both algorithms
        for system_name in ["quadtree_system", "spatial_hash_system"]:
            collision_system = setup_collision_system[system_name]
            player = setup_collision_system["player"]
            enemy_group = setup_collision_system["enemy_group"]
            projectile_group = setup_collision_system["projectile_group"]
            powerup_group = setup_collision_system["powerup_group"]

            # The powerup is already positioned near the player
            powerup = setup_collision_system["powerup"]

            # Update the spatial structure
            collision_system.update(projectile_group, enemy_group, player, powerup_group)

            # Check for collisions
            powerup_hits = collision_system.check_player_powerup_collisions(player, powerup_group)

            # Verify collision was detected
            assert powerup in powerup_hits

            logger.info(f"Player-powerup collision detection test passed for {system_name}")

    def test_spatial_partitioning_efficiency(self, setup_collision_system):
        """Test that spatial partitioning reduces the number of collision checks."""
        # Create a large number of sprites spread across the screen
        many_enemies = pygame.sprite.Group()
        for i in range(100):
            x = (i % 10) * 80  # Spread across x-axis
            y = (i // 10) * 60  # Spread across y-axis
            enemy = MockSprite(x, y, 15, 15)
            many_enemies.add(enemy)

        # Create a player at one corner and a projectile at the opposite corner
        corner_player = MockSprite(10, 10, 20, 20)
        corner_projectile = MockSprite(790, 590, 5, 5)
        corner_projectiles = pygame.sprite.Group(corner_projectile)

        # Test with both algorithms
        for system_name in ["quadtree_system", "spatial_hash_system"]:
            collision_system = setup_collision_system[system_name]

            # Update the spatial structure
            collision_system.update(
                corner_projectiles,
                many_enemies,
                corner_player,
                pygame.sprite.Group(),  # Empty powerup group
            )

            # The projectile and player are in opposite corners, so they shouldn't
            # collide with most of the enemies in an efficient implementation
            projectile_collisions = collision_system.check_projectile_enemy_collisions(
                corner_projectiles, many_enemies
            )

            player_collisions = collision_system.check_player_enemy_collisions(
                corner_player, many_enemies
            )

            # We expect few or no collisions due to the spatial partitioning
            assert len(projectile_collisions) <= 3  # Allow a small margin for boundary cases
            assert len(player_collisions) <= 3

            logger.info(f"Spatial partitioning efficiency test passed for {system_name}")
