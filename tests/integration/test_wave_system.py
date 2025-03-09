import pytest
import pygame
import os
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from scenes.game_scene import GameScene
from managers.wave_manager import WaveManager
from utils.logger import GameLogger

# Setup logger for tests
logger = GameLogger.get_logger("test_wave_system")


class TestWaveSystem:
    """Integration tests for the wave system in the game scene."""

    @pytest.fixture
    def mock_scene_manager(self):
        """Create a mock scene manager."""
        mock_manager = MagicMock()
        mock_manager.scenes = {"game_over": MagicMock()}
        return mock_manager

    @pytest.fixture
    def game_scene(self, mock_scene_manager):
        """Create a game scene instance for testing."""
        # Initialize pygame for time functions
        pygame.init()

        # Create a mock screen
        screen = pygame.Surface((800, 600))

        # Patch ScoreManager
        with patch("managers.score_manager.ScoreManager") as mock_score_class:
            # Configure the mock score manager
            mock_score_manager = MagicMock()
            mock_score_manager.current_score = 0
            mock_score_manager.score = 0
            # Add the add_score method that's used in GameScene
            mock_score_manager.add_score = MagicMock()
            mock_score_class.return_value = mock_score_manager

            # Create the game scene
            scene = GameScene()
            scene.scene_manager = mock_scene_manager
            scene.screen = screen

            # Mock methods that interact with external systems
            scene.play_scene_music = MagicMock()
            scene.play_sound = MagicMock()
            scene.switch_to_scene = MagicMock()

            # Mock _load_map to avoid file access
            with patch.object(scene, "_load_map"):
                scene._initialize_game()

            return scene

    def test_wave_manager_initialization(self, game_scene):
        """Test that the wave manager is properly initialized in the game scene."""
        assert hasattr(game_scene, "wave_manager")
        assert isinstance(game_scene.wave_manager, WaveManager)
        assert game_scene.wave_manager.current_wave == 0
        assert not game_scene.wave_in_progress

    def test_wave_transition(self, game_scene):
        """Test the wave transition mechanic."""
        # Set up wave transition state
        game_scene.wave_transition_timer = pygame.time.get_ticks()
        game_scene.wave_transition_text = "Get Ready! Wave 1"

        # Verify transition state
        assert game_scene.wave_transition_timer > 0
        assert "Get Ready!" in game_scene.wave_transition_text

        # Simulate wave start
        game_scene.wave_transition_timer = 0
        game_scene.wave_in_progress = True
        game_scene.wave_manager.current_wave = 1
        game_scene.wave_manager.enemies_remaining = 10
        game_scene.wave_manager.wave_in_progress = True

        # Verify wave started
        assert game_scene.wave_in_progress
        assert game_scene.wave_manager.current_wave == 1
        assert game_scene.wave_manager.enemies_remaining > 0
        assert game_scene.wave_transition_timer == 0

    def test_enemy_spawning(self, game_scene):
        """Test that enemies are spawned according to the wave manager."""
        # Set up wave state
        game_scene.wave_in_progress = True
        game_scene.wave_manager.current_wave = 1
        game_scene.wave_manager.wave_in_progress = True
        game_scene.wave_manager.enemies_remaining = 10

        # Get initial enemy count
        initial_enemy_count = len(game_scene.enemy_group)

        # Manually spawn an enemy
        enemy_type = "basic"
        attr_multipliers = {"health": 1.0, "damage": 1.0, "speed": 1.0}
        game_scene.spawn_enemy(enemy_type, attr_multipliers)

        # Verify an enemy was spawned
        assert len(game_scene.enemy_group) > initial_enemy_count, "Enemy was not spawned"

    def test_wave_completion(self, game_scene):
        """Test that wave completion is properly detected and handled."""
        # Set up active wave
        game_scene.wave_in_progress = True
        game_scene.wave_manager.current_wave = 1
        game_scene.wave_manager.wave_in_progress = True
        game_scene.wave_manager.enemies_remaining = 10

        # Reset the transition timer to ensure clean state
        game_scene.wave_transition_timer = 0

        # Log initial state
        logger.info(
            f"Initial state - wave_in_progress: {game_scene.wave_in_progress}, wave_transition_timer: {game_scene.wave_transition_timer}"
        )

        # Simulate wave completion by marking the wave as complete in the wave manager
        game_scene.wave_manager.enemies_remaining = 0
        game_scene.wave_manager.wave_in_progress = False

        # Ensure enemy_group is empty as required by new check
        game_scene.enemy_group.empty()

        # First update() call should detect the wave is completed and set wave_in_progress to false
        with patch("pygame.time.get_ticks", return_value=1000):
            # Update the game state
            game_scene.update()

            # Verify wave is completed in the game scene
            assert not game_scene.wave_in_progress, "Game scene should detect wave completion"
            assert game_scene.wave_transition_timer == 0, "Transition timer should not be set yet"

            logger.info(
                f"After first update - wave_in_progress: {game_scene.wave_in_progress}, wave_transition_timer: {game_scene.wave_transition_timer}"
            )

            # Second update() call should recognize that no wave is in progress and start the transition
            game_scene.update()

            # Verify transition started
            assert (
                game_scene.wave_transition_timer == 1000
            ), "Wave transition timer should be set to current time"
            assert (
                "Wave 1 complete" in game_scene.wave_transition_text
            ), "Wave completion text should be set"

            logger.info(
                f"After second update - wave_transition_timer: {game_scene.wave_transition_timer}, wave_transition_text: {game_scene.wave_transition_text}"
            )

    def test_wave_ui_rendering(self, game_scene):
        """Test that wave information is correctly rendered in the UI."""
        # Set up wave state
        game_scene.wave_manager.current_wave = 1
        game_scene.wave_in_progress = True
        game_scene.wave_manager.wave_in_progress = True
        game_scene.wave_manager.enemies_remaining = 5

        # Mock draw_text
        with patch.object(game_scene, "draw_text") as mock_draw_text:
            # Render wave info
            game_scene._render_wave_info()

            # Check that draw_text was called with appropriate parameters
            mock_draw_text.assert_any_call("Wave 1", 28, (255, 255, 255), 400, 15, align="center")

            # Check for enemies remaining call
            enemies_call_found = False
            for call in mock_draw_text.call_args_list:
                args, kwargs = call
                if "Enemies: 5" in args[0]:
                    enemies_call_found = True
                    break

            assert enemies_call_found, "Enemies remaining text not rendered"

    def test_boss_wave_mechanics(self, game_scene):
        """Test that boss waves have special handling."""
        # Check boss wave detection
        wave_manager = game_scene.wave_manager

        # Normal waves
        assert not wave_manager.is_boss_wave(1)
        assert not wave_manager.is_boss_wave(4)

        # Boss waves
        assert wave_manager.is_boss_wave(5)
        assert wave_manager.is_boss_wave(10)

        # Test boss attributes
        # We'll check a normal wave's attribute multipliers compared to a boss wave
        normal_wave_multiplier = wave_manager.get_enemy_attributes_multiplier(1)
        boss_wave_multiplier = wave_manager.get_enemy_attributes_multiplier(5)

        # Boss waves should have higher multipliers
        assert boss_wave_multiplier["health"] > normal_wave_multiplier["health"]
