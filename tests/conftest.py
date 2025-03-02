"""Test fixtures for the Draugr's Descent game."""

import os
import sys
import pytest
import pygame

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture(scope="session", autouse=True)
def pygame_setup():
    """Initialize pygame for testing and clean up afterwards."""
    # Some environments need a display for pygame
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.display.set_mode((800, 600))

    yield

    pygame.quit()


@pytest.fixture
def mock_screen():
    """Create a mock screen surface for testing."""
    return pygame.Surface((800, 600))


@pytest.fixture
def mock_clock():
    """Create a mock clock for testing."""
    return pygame.time.Clock()


@pytest.fixture
def mock_event():
    """Create a mock pygame event."""
    return lambda event_type, **kwargs: pygame.event.Event(event_type, **kwargs)


@pytest.fixture
def empty_sprite_group():
    """Create an empty sprite group for testing."""
    return pygame.sprite.Group()
