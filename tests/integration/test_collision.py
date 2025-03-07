"""Integration tests for collision detection in Draugr's Descent."""

import pytest
import pygame
from objects import Player, Enemy, Powerup, Projectile
from utils import collision_handler
from tests.test_utils.game_stub import GameStub


class TestCollisionDetection:
    """Tests for collision detection between game objects."""

    def test_player_enemy_collision(self, pygame_setup, mock_screen):
        """Test that player and enemy collisions are properly detected and handled."""
        # Create a player and an enemy at the same position
        player = Player((100, 100))
        initial_health = player.current_health
        enemy = Enemy((100, 100))

        # Manual collision detection and handling
        collided = pygame.sprite.collide_rect(player, enemy)
        assert collided  # Entities should be colliding

        # Call the collision handler
        collision_handler.handle_player_enemy_collision(player, enemy)

        # Player should have taken damage
        assert player.current_health < initial_health
        # Player should be temporarily invincible
        assert player.invincible

    def test_player_powerup_collision(self, pygame_setup, mock_screen):
        """Test that player and powerup collisions are properly detected and handled."""
        # Test 1: Health powerup
        # Create a player and a powerup at the same position
        player = Player((100, 100))
        player.current_health = 50  # Reduce health to see the effect
        powerup = Powerup((100, 100), "health")

        # Test collision
        collided = pygame.sprite.collide_rect(player, powerup)
        assert collided  # Entities should be colliding

        # Call the collision handler
        collision_handler.handle_player_powerup_collision(player, powerup)

        # Player should have gained health
        assert player.current_health > 50
        # Powerup should be deactivated
        assert not powerup.active

        # Test 2: Weapon boost powerup
        player = Player((100, 100))
        original_cooldown = player.shot_cooldown
        weapon_powerup = Powerup((100, 100), "weapon")

        # Test collision
        collided = pygame.sprite.collide_rect(player, weapon_powerup)
        assert collided

        # Call the collision handler
        collision_handler.handle_player_powerup_collision(player, weapon_powerup)

        # Player should have weapon boost active with reduced cooldown
        assert player.weapon_boost_active
        assert player.shot_cooldown < original_cooldown
        # Powerup should be deactivated
        assert not weapon_powerup.active

    def test_projectile_enemy_collision(self, pygame_setup, mock_screen):
        """Test that projectile and enemy collisions are properly detected and handled."""
        # Create a projectile and an enemy at the same position
        projectile = Projectile((100, 100), (1, 0), 10)  # Projectile with damage 10
        enemy = Enemy((100, 100))
        initial_health = enemy.health

        # Test collision
        collided = pygame.sprite.collide_rect(projectile, enemy)
        assert collided  # Entities should be colliding

        # Call the collision handler
        result = collision_handler.handle_projectile_enemy_collision(projectile, enemy)

        # Enemy should have taken damage
        assert enemy.health < initial_health
        # Projectile should be deactivated
        assert not projectile.active

        # Check if the result indicates if the enemy died
        if enemy.health <= 0:
            assert result is True  # Enemy died
        else:
            assert result is False  # Enemy still alive
