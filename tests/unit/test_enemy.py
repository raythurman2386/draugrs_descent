"""Tests for the Enemy class."""

import pytest
import pygame
from objects import Enemy


class TestEnemy:
    """Tests for the Enemy class."""

    def test_enemy_initialization(self):
        """Test that an Enemy object can be created with proper attributes."""
        position = (100, 200)
        enemy = Enemy(position)
        assert enemy.health == enemy.max_health
        assert enemy.rect.center == position
        assert isinstance(enemy.image, pygame.Surface)
        assert hasattr(enemy, "id")  # Ensure it has a unique ID

    def test_enemy_take_damage(self):
        """Test that the enemy takes damage correctly."""
        enemy = Enemy((100, 100))
        initial_health = enemy.health

        # Enemy takes 5 damage
        result = enemy.take_damage(5)
        assert enemy.health == initial_health - 5
        assert result is False  # Enemy is not dead yet

        # Enemy takes lethal damage
        enemy.health = 10
        result = enemy.take_damage(10)
        assert enemy.health <= 0
        assert result is True  # Enemy is dead

    def test_enemy_update_movement(self):
        """Test that the enemy moves toward the player."""
        enemy = Enemy((100, 100))
        player_pos = (200, 200)  # Player is to the bottom-right

        # Store initial position
        initial_pos = (enemy.rect.x, enemy.rect.y)

        # Update enemy
        enemy.update(player_pos)

        # Enemy should have moved toward player
        assert enemy.rect.x > initial_pos[0]  # Moved right
        assert enemy.rect.y > initial_pos[1]  # Moved down
