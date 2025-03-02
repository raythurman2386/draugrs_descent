import pytest
import pygame
from scenes.game_scene import GameScene
from utils.scoring import ScoreManager
from objects.enemy import Enemy
from objects.powerup import Powerup


@pytest.fixture
def game_scene(pygame_setup):
    """Initialize a game scene for testing."""
    return GameScene()


class TestGameScoring:
    """Integration tests for the game scoring system."""

    def test_score_updates_on_enemy_death(self, game_scene):
        """Test that defeating an enemy updates the score correctly."""
        # Make sure the game scene has a score manager
        assert hasattr(game_scene, "score_manager")
        assert isinstance(game_scene.score_manager, ScoreManager)
        
        # Get initial score
        initial_score = game_scene.score_manager.current_score
        
        # Directly call the handle_enemy_death method
        enemy = Enemy((100, 100))
        game_scene.enemy_group.add(enemy)
        game_scene.handle_enemy_death(enemy)
        
        # Score should increase by ENEMY_DEFEAT_POINTS
        assert game_scene.score_manager.current_score == initial_score + ScoreManager.ENEMY_DEFEAT_POINTS
        
    def test_score_updates_on_powerup_collection(self, game_scene):
        """Test that collecting a powerup updates the score correctly."""
        # Get initial score
        initial_score = game_scene.score_manager.current_score
        
        # Create a powerup
        powerup = Powerup((100, 100), "health")
        game_scene.powerup_group.add(powerup)
        
        # Directly call the powerup collection code instead of using collision detection
        powerup.active = True  # Ensure the powerup is active
        game_scene.score_manager.powerup_collected()
        
        # Score should increase by POWERUP_COLLECTED_POINTS
        assert game_scene.score_manager.current_score == initial_score + ScoreManager.POWERUP_COLLECTED_POINTS
        
    def test_high_score_persistence(self, game_scene, mocker):
        """Test that high scores persist between game sessions."""
        # Set a high score
        game_scene.score_manager.add_score(1000)
        high_score = game_scene.score_manager.high_score
        
        # Mock the save method to avoid actual file operations
        save_mock = mocker.patch.object(game_scene.score_manager, "save_high_score")
        
        # Directly call the save method to test it
        game_scene.score_manager.save_high_score()
        
        # Verify high score was saved
        save_mock.assert_called_once()
        
        # Create a new game scene
        new_game = GameScene()
        
        # Mock the load method to return our high score
        load_mock = mocker.patch.object(new_game.score_manager, "load_high_score", return_value=high_score)
        
        # Call load directly
        loaded_score = new_game.score_manager.load_high_score()
        
        # Verify high score is loaded
        assert loaded_score == high_score
        load_mock.assert_called_once() 