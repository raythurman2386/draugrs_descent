"""Integration tests for the game loop and state updates in Draugr's Descent."""

import pytest
import pygame
from tests.test_utils.game_stub import GameStub, GameState
from objects import Player, Enemy, Powerup


class TestGameLoop:
    """Tests for the game loop and state updates."""

    def test_game_initialization(self, pygame_setup, mock_screen, mock_clock):
        """Test that the game initializes properly."""
        game = GameStub(mock_screen, mock_clock)

        # Check initial game state
        assert game.state == GameState.MENU
        assert isinstance(game.player, Player)
        assert game.score == 0
        assert len(game.enemies) >= 0
        assert len(game.powerups) >= 0

    def test_game_state_transitions(self, pygame_setup, mock_screen, mock_clock, mock_event):
        """Test that game states transition correctly."""
        game = GameStub(mock_screen, mock_clock)

        # Initial state should be MENU
        assert game.state == GameState.MENU

        # Simulate starting the game
        start_event = mock_event(pygame.KEYDOWN, key=pygame.K_RETURN)
        game.handle_events([start_event])

        # Game should now be in PLAYING state
        assert game.state == GameState.PLAYING

        # Simulate player death
        game.player.current_health = 0
        game.update()

        # Game should now be in GAME_OVER state
        assert game.state == GameState.GAME_OVER

        # Simulate restarting the game
        restart_event = mock_event(pygame.KEYDOWN, key=pygame.K_r)
        game.handle_events([restart_event])

        # Game should be back in PLAYING state with reset values
        assert game.state == GameState.PLAYING
        assert game.score == 0
        assert game.player.current_health == game.player.max_health

    def test_enemy_spawning(self, pygame_setup, mock_screen, mock_clock):
        """Test that enemies spawn correctly during gameplay."""
        game = GameStub(mock_screen, mock_clock)
        game.state = GameState.PLAYING

        # Record initial enemy count
        initial_enemy_count = len(game.enemies)

        # Directly spawn an enemy for the test
        game.spawn_enemy()

        # There should be more enemies now
        assert len(game.enemies) > initial_enemy_count

    def test_score_increases_on_enemy_death(self, pygame_setup, mock_screen, mock_clock):
        """Test that score increases when an enemy is killed."""
        game = GameStub(mock_screen, mock_clock)
        game.state = GameState.PLAYING
        initial_score = game.score

        # Add an enemy with low health
        enemy = Enemy((100, 100))
        enemy.current_health = 1
        game.enemies.add(enemy)

        # Kill the enemy and update the game
        enemy.take_damage(10)  # More than enough to kill
        game.update()

        # Score should have increased
        assert game.score > initial_score
