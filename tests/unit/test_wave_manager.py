import pytest
import pygame
from unittest.mock import MagicMock, patch
import sys
import os

# Add the parent directory to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from managers.wave_manager import WaveManager
from utils.logger import GameLogger

# Setup logger for tests
logger = GameLogger.get_logger("test_wave_manager")


class TestWaveManager:
    """Test suite for the WaveManager class."""

    @pytest.fixture
    def mock_game_scene(self):
        """Create a mock game scene for testing."""
        mock_scene = MagicMock()
        mock_scene.spawn_enemy = MagicMock()
        mock_scene.spawn_boss = MagicMock()
        return mock_scene

    @pytest.fixture
    def wave_manager(self, mock_game_scene):
        """Create a WaveManager instance for testing."""
        # Initialize pygame for time functions
        pygame.init()
        return WaveManager(mock_game_scene)

    def test_init(self, wave_manager):
        """Test that WaveManager initializes correctly."""
        assert wave_manager.current_wave == 0
        assert wave_manager.wave_in_progress == False
        assert wave_manager.enemies_remaining == 0
        assert hasattr(wave_manager, "wave_config")
        assert hasattr(wave_manager, "boss_wave_frequency")

    def test_start_next_wave(self, wave_manager):
        """Test starting a new wave."""
        wave_manager.start_next_wave()
        assert wave_manager.current_wave == 1
        assert wave_manager.wave_in_progress == True
        assert wave_manager.enemies_remaining > 0
        assert wave_manager.current_wave_start_time > 0

    def test_wave_progression(self, wave_manager):
        """Test that waves progress correctly."""
        # Start wave 1
        wave_manager.start_next_wave()
        assert wave_manager.current_wave == 1

        # Complete wave 1
        wave_manager.enemies_remaining = 0
        wave_manager.wave_in_progress = False

        # Start wave 2
        wave_manager.start_next_wave()
        assert wave_manager.current_wave == 2

    def test_is_boss_wave(self, wave_manager):
        """Test boss wave detection."""
        # Set boss frequency to 5
        wave_manager.boss_wave_frequency = 5

        # Non-boss waves
        assert not wave_manager.is_boss_wave(1)
        assert not wave_manager.is_boss_wave(2)
        assert not wave_manager.is_boss_wave(3)
        assert not wave_manager.is_boss_wave(4)

        # Boss waves
        assert wave_manager.is_boss_wave(5)
        assert wave_manager.is_boss_wave(10)
        assert wave_manager.is_boss_wave(15)

    def test_get_enemy_count_for_wave(self, wave_manager):
        """Test enemy count scaling with wave number."""
        # Enemy count should increase with wave number
        wave_1_count = wave_manager.get_enemy_count_for_wave(1)
        wave_5_count = wave_manager.get_enemy_count_for_wave(5)
        wave_10_count = wave_manager.get_enemy_count_for_wave(10)

        assert wave_5_count > wave_1_count
        assert wave_10_count > wave_5_count

    def test_get_spawn_interval(self, wave_manager):
        """Test spawn interval decreases with wave number."""
        # Spawn intervals should decrease (faster spawning) with higher waves
        interval_wave_1 = wave_manager.get_spawn_interval(1)
        interval_wave_5 = wave_manager.get_spawn_interval(5)
        interval_wave_10 = wave_manager.get_spawn_interval(10)

        assert interval_wave_5 < interval_wave_1
        assert interval_wave_10 < interval_wave_5
        assert interval_wave_10 >= wave_manager.min_spawn_interval

    def test_get_enemy_attributes_multiplier(self, wave_manager):
        """Test enemy attribute scaling with wave number."""
        # Enemy attributes should scale up with wave number
        multiplier_wave_1 = wave_manager.get_enemy_attributes_multiplier(1)
        multiplier_wave_5 = wave_manager.get_enemy_attributes_multiplier(5)
        multiplier_wave_10 = wave_manager.get_enemy_attributes_multiplier(10)

        # Health, damage and speed should increase with wave number
        assert multiplier_wave_5["health"] > multiplier_wave_1["health"]
        assert multiplier_wave_10["health"] > multiplier_wave_5["health"]

        assert multiplier_wave_5["damage"] > multiplier_wave_1["damage"]
        assert multiplier_wave_10["damage"] > multiplier_wave_5["damage"]

        assert multiplier_wave_5["speed"] > multiplier_wave_1["speed"]
        assert multiplier_wave_10["speed"] > multiplier_wave_5["speed"]

    def test_get_enemy_type_distribution(self, wave_manager):
        """Test enemy type distribution changes with wave progression."""
        # Early waves should have more basic enemies
        distribution_wave_1 = wave_manager.get_enemy_type_distribution(1)
        assert distribution_wave_1["basic"] > distribution_wave_1["ranged"]
        assert distribution_wave_1["basic"] > distribution_wave_1["charger"]

        # Later waves should have more variety
        distribution_wave_10 = wave_manager.get_enemy_type_distribution(10)
        assert distribution_wave_10["ranged"] > distribution_wave_1["ranged"]
        assert distribution_wave_10["charger"] > distribution_wave_1["charger"]

    def test_update_with_active_wave(self, wave_manager, mock_game_scene):
        """Test the update method with an active wave."""
        # Start a wave and set a spawn time
        wave_manager.start_next_wave()
        wave_manager.last_enemy_spawn_time = 0  # Set to 0 to ensure spawning

        # Call update at a time that should trigger spawning
        current_time = wave_manager.get_spawn_interval(1) + 100  # Add buffer
        wave_manager.update(current_time)

        # Verify enemy was spawned
        mock_game_scene.spawn_enemy.assert_called_once()
        assert wave_manager.last_enemy_spawn_time == current_time

    def test_wave_completion(self, wave_manager):
        """Test detecting when a wave is complete."""
        # Start a wave
        wave_manager.start_next_wave()
        assert not wave_manager.is_wave_complete()

        # Kill all enemies
        wave_manager.enemies_remaining = 0
        assert wave_manager.is_wave_complete()
