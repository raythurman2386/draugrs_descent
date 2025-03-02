"""Tests for the Powerup/Item system."""

import pytest
import pygame
from objects import Powerup, Player
from constants import PLAYER_SHOT_COOLDOWN, POWERUP_WEAPON_BOOST_FACTOR


class TestPowerup:
    """Tests for the Powerup class and item system."""

    def test_powerup_initialization(self):
        """Test that a Powerup object can be created with proper attributes."""
        position = (200, 300)
        powerup_type = "health"
        powerup = Powerup(position, powerup_type)

        assert powerup.type == powerup_type
        assert powerup.rect.center == position
        assert isinstance(powerup.image, pygame.Surface)
        assert powerup.active

    def test_powerup_collection(self):
        """Test that a powerup can be collected and applied to a player."""
        # Create player and powerup
        player = Player((100, 100))
        player.current_health = 50  # Set player health to be below max

        # Create health powerup
        health_powerup = Powerup((100, 100), "health")

        # Simulate collection
        health_powerup.apply_effect(player)

        # Check if player health increased
        assert player.current_health > 50
        assert not health_powerup.active  # Powerup should be deactivated after collection

    def test_shield_powerup(self):
        """Test that a shield powerup provides temporary invincibility."""
        # Create player and powerup
        player = Player((100, 100))
        player.invincible = False

        # Create shield powerup
        shield_powerup = Powerup((100, 100), "shield")

        # Simulate collection
        shield_powerup.apply_effect(player)

        # Player should be invincible
        assert player.invincible
        assert not shield_powerup.active  # Powerup should be deactivated

    def test_powerup_deactivation(self):
        """Test that powerups deactivate correctly."""
        powerup = Powerup((100, 100), "health")
        assert powerup.active

        powerup.deactivate()
        assert not powerup.active

    def test_weapon_boost_powerup(self):
        """Test that a weapon boost powerup increases fire rate."""
        # Create player and powerup
        player = Player((100, 100))
        original_cooldown = player.shot_cooldown

        # Create weapon boost powerup
        weapon_powerup = Powerup((100, 100), "weapon")

        # Simulate collection
        weapon_powerup.apply_effect(player)

        # Player should have increased fire rate (reduced cooldown)
        expected_cooldown = int(PLAYER_SHOT_COOLDOWN * (1 - POWERUP_WEAPON_BOOST_FACTOR))
        assert player.weapon_boost_active
        assert player.shot_cooldown == expected_cooldown
        assert not weapon_powerup.active  # Powerup should be deactivated
