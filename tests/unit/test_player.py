"""Tests for the Player class."""

import pytest
import pygame
from objects import Player


class TestPlayer:
    """Tests for the Player class."""

    def test_player_initialization(self):
        """Test that a Player object can be created with proper attributes."""
        player = Player()
        assert player.current_health == player.max_health
        assert player.invincible is False
        assert player.rect.center == (400, 300)  # Default position
        assert isinstance(player.image, pygame.Surface)

    def test_player_take_damage(self):
        """Test that the player takes damage correctly."""
        player = Player()
        initial_health = player.current_health

        # Player takes 10 damage
        player.take_damage(10)
        assert player.current_health == initial_health - 10
        assert player.invincible is True  # Should be invincible after damage

        # Player is invincible, should not take more damage
        player.take_damage(10)
        assert player.current_health == initial_health - 10  # Health unchanged

    def test_player_death(self):
        """Test that the player dies when health reaches zero."""
        player = Player()
        player.current_health = 10  # Set low health

        # Should not die yet
        result = player.take_damage(9)
        assert result is False
        assert player.current_health == 1

        # Reset invincibility for testing
        player.invincible = False

        # Should die now
        result = player.take_damage(10)
        assert result is True
        assert player.current_health <= 0
