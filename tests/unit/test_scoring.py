import pytest
import pygame
import json
import os
from unittest.mock import patch, mock_open
from utils.scoring import ScoreManager


class TestScoreManager:
    """Test cases for the game's scoring system."""

    @pytest.fixture
    def score_manager_with_mock(self):
        """Fixture to create a ScoreManager with mocked file operations."""
        # Use a context manager to patch the file operations
        with patch("builtins.open", mock_open()), patch(
            "os.path.exists", return_value=False
        ), patch("json.load", return_value={"high_score": 0}):
            score_manager = ScoreManager()
            yield score_manager

    def test_score_initialization(self):
        """Test that the score manager initializes with a zero score."""
        with patch("os.path.exists", return_value=False):
            score_manager = ScoreManager()
            assert score_manager.current_score == 0
            assert score_manager.high_score == 0

    def test_add_score(self):
        """Test adding points to the current score."""
        with patch("os.path.exists", return_value=False):
            score_manager = ScoreManager()
            score_manager.add_score(100)
            assert score_manager.current_score == 100

            # Test adding more points
            score_manager.add_score(50)
            assert score_manager.current_score == 150

    def test_high_score_update(self):
        """Test that high score is updated when current score exceeds it."""
        with patch("os.path.exists", return_value=False):
            score_manager = ScoreManager()
            score_manager.add_score(100)
            assert score_manager.high_score == 100

            # Reset score but high score should remain
            score_manager.reset_current_score()
            assert score_manager.current_score == 0
            assert score_manager.high_score == 100

            # Score below high score shouldn't update high score
            score_manager.add_score(50)
            assert score_manager.high_score == 100

            # Score above high score should update it
            score_manager.add_score(60)  # Total: 110
            assert score_manager.high_score == 110

    def test_score_events(self):
        """Test that different game events award the correct number of points."""
        with patch("os.path.exists", return_value=False):
            score_manager = ScoreManager()

            # Test enemy defeat points
            score_manager.enemy_defeated()
            assert score_manager.current_score == ScoreManager.ENEMY_DEFEAT_POINTS

            # Test powerup collection points
            score_manager.powerup_collected()
            expected_score = (
                ScoreManager.ENEMY_DEFEAT_POINTS + ScoreManager.POWERUP_COLLECTED_POINTS
            )
            assert score_manager.current_score == expected_score

            # Test time survived points
            score_manager.add_time_survived_points(30)  # 30 seconds
            time_points = 30 * ScoreManager.POINTS_PER_SECOND
            expected_score += time_points
            assert score_manager.current_score == expected_score

    def test_score_reset(self):
        """Test resetting the current score."""
        with patch("os.path.exists", return_value=False):
            score_manager = ScoreManager()
            score_manager.add_score(500)
            assert score_manager.current_score == 500

            score_manager.reset_current_score()
            assert score_manager.current_score == 0
            # High score should remain
            assert score_manager.high_score == 500

    def test_score_multiplier(self):
        """Test the score multiplier functionality."""
        with patch("os.path.exists", return_value=False):
            score_manager = ScoreManager()

            # Default multiplier should be 1
            assert score_manager.score_multiplier == 1.0

            # Test setting multiplier
            score_manager.set_multiplier(2.0)
            score_manager.add_score(100)
            assert score_manager.current_score == 200  # 100 * 2.0

            # Test multiplier reset
            score_manager.reset_multiplier()
            score_manager.add_score(100)
            assert score_manager.current_score == 300  # 200 + 100 * 1.0
