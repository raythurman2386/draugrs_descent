"""Utility functions and helpers for testing the Draugr's Descent game."""

import pygame
import random
from unittest.mock import MagicMock


def create_mock_surface(width=800, height=600):
    """Create a mock pygame Surface for testing."""
    surface = pygame.Surface((width, height))
    # Add some basic methods that might be used in tests
    surface.get_rect = lambda: pygame.Rect(0, 0, width, height)
    return surface


def create_mock_event(event_type, **kwargs):
    """Create a mock pygame event for testing."""
    event = MagicMock()
    event.type = event_type
    for key, value in kwargs.items():
        setattr(event, key, value)
    return event


def set_random_seed(seed=42):
    """Set a fixed random seed for deterministic test results."""
    random.seed(seed)
    # If pygame has its own random functionality, seed it here
    try:
        pygame.random.seed(seed)
    except (AttributeError, TypeError):
        pass  # pygame might not have its own random functionality


def create_test_game_state():
    """Create a minimal game state for testing specific components."""
    from game import Game, GameState
    from objects import Player

    # Create minimal mocks needed for a Game instance
    mock_screen = create_mock_surface()
    mock_clock = MagicMock()

    # Create a game in a deterministic state
    game = Game(mock_screen, mock_clock)
    game.state = GameState.PLAYING
    game.player = Player((400, 300))
    game.score = 0

    # Clear any entities that might be randomly initialized
    game.enemies.empty()
    game.powerups.empty()
    game.projectiles.empty()

    return game


def simulate_key_press(key_constant):
    """Simulate a key press for testing input handling."""
    return create_mock_event(pygame.KEYDOWN, key=key_constant)


def simulate_key_release(key_constant):
    """Simulate a key release for testing input handling."""
    return create_mock_event(pygame.KEYUP, key=key_constant)


def simulate_mouse_click(position, button=1):
    """Simulate a mouse click for testing mouse input."""
    return create_mock_event(pygame.MOUSEBUTTONDOWN, pos=position, button=button)
