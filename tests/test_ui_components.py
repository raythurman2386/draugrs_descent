"""Tests for UI components."""

import os
import sys
import unittest
import pygame
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ui.components import (
    draw_panel,
    draw_button,
    draw_selection_arrow,
    draw_progress_bar,
    draw_text_with_shadow,
    draw_info_box,
    draw_currency_display,
)
from managers import config


class TestUIComponents(unittest.TestCase):
    """Test cases for UI components."""

    def setUp(self):
        """Set up pygame and create a test surface."""
        pygame.init()
        self.surface = pygame.Surface((800, 600))

        # Create mock for asset manager
        self.mock_game_asset_manager = MagicMock()
        self.mock_font = MagicMock()
        self.mock_font.render.return_value = pygame.Surface((100, 30))
        self.mock_game_asset_manager.get_font.return_value = self.mock_font

        # Create mock UI elements
        self.mock_panel = pygame.Surface((200, 200))
        self.mock_button = pygame.Surface((150, 40))
        self.mock_game_asset_manager.get_ui_element.return_value = self.mock_button

        # Mock config
        self.original_config_get_color = config.get_color
        config.get_color = MagicMock(return_value=(255, 255, 255))

    def tearDown(self):
        """Clean up."""
        pygame.quit()
        # Restore original config.get_color
        config.get_color = self.original_config_get_color

    def test_draw_button(self):
        """Test drawing a button."""
        # Use a real rectangle for this test
        rect = pygame.Rect(100, 100, 150, 40)

        # Test with various button states
        with unittest.mock.patch("managers.game_asset_manager", self.mock_game_asset_manager):
            # Normal button
            draw_button(self.surface, rect, "Test Button", False, False)
            self.mock_game_asset_manager.get_ui_element.assert_called()

            # Selected button
            draw_button(self.surface, rect, "Test Button", True, False)

            # Disabled button
            draw_button(self.surface, rect, "Test Button", False, True)

    def test_draw_progress_bar(self):
        """Test drawing a progress bar."""
        rect = pygame.Rect(100, 100, 200, 20)

        # Test with different values
        draw_progress_bar(self.surface, rect, 5, 10)
        draw_progress_bar(self.surface, rect, 0, 10)
        draw_progress_bar(self.surface, rect, 10, 10)

    def test_draw_text_with_shadow(self):
        """Test drawing text with shadow."""
        with unittest.mock.patch("managers.game_asset_manager", self.mock_game_asset_manager):
            draw_text_with_shadow(
                self.surface,
                "Test Text",
                self.mock_font,
                (255, 255, 255),
                (0, 0, 0),
                (100, 100),
                "center",
                (2, 2),
            )
            self.mock_font.render.assert_called()


if __name__ == "__main__":
    unittest.main()
