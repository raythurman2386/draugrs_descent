"""Tests for the Enemy class."""

import pytest
import pygame
from objects import Enemy, RangedEnemy, ChargerEnemy


class TestEnemy:
    """Tests for the Enemy class."""

    ENEMY_TYPES = [Enemy, RangedEnemy, ChargerEnemy]

    @pytest.mark.parametrize("enemy_type", ENEMY_TYPES)
    def test_enemy_initialization(self, enemy_type):
        """Test that an Enemy object can be created with proper attributes."""
        position = (100, 200)
        enemy = enemy_type(position)
        assert enemy.health == enemy.max_health
        assert enemy.rect.x == position[0]
        assert enemy.rect.y == position[1]
        assert isinstance(enemy.image, pygame.Surface)
        assert hasattr(enemy, "id")  # Ensure it has a unique ID

    @pytest.mark.parametrize("enemy_type", ENEMY_TYPES)
    def test_enemy_take_damage(self, enemy_type):
        """Test that the enemy takes damage correctly."""
        enemy = enemy_type((100, 100))
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

    @pytest.mark.parametrize("enemy_type", ENEMY_TYPES)
    def test_enemy_movement(self, enemy_type):
        """Test that the enemy moves toward the player."""
        # Create enemy at 100,100 and target at 400,400 (bottom-right)
        enemy = enemy_type((100, 100))
        player_pos = (400, 400)  # Player is to the bottom-right
        initial_pos = (enemy.rect.x, enemy.rect.y)

        # Explicitly set attributes
        if enemy_type == RangedEnemy:
            enemy.speed = 2.5
            enemy.preferred_distance = 200
            print(
                f"RangedEnemy - Speed: {enemy.speed}, Preferred Distance: {enemy.preferred_distance}"
            )
        elif enemy_type == ChargerEnemy:
            enemy.speed = 2.8
            enemy.charge_distance = 150
            enemy.last_charge_time = -3000  # Ensure charge is ready
            print(f"ChargerEnemy - Speed: {enemy.speed}, Charge Distance: {enemy.charge_distance}")

        # Call update with appropriate parameters
        if enemy_type == RangedEnemy:
            enemy.update(player_pos, 0, pygame.sprite.Group(), pygame.sprite.Group())
        elif enemy_type == ChargerEnemy:
            enemy.update(player_pos, 0)
        else:
            enemy.update(player_pos)

        # Debug output
        print(f"Initial position: {initial_pos}, Final position: ({enemy.rect.x}, {enemy.rect.y})")

        # Verify movement - enemy should move diagonally toward player
        assert enemy.rect.x > initial_pos[0], f"Enemy should move right toward player"
        assert enemy.rect.y > initial_pos[1], f"Enemy should move down toward player"
