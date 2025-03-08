import os
import sys
import unittest
import pygame

# Add the root directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from managers.asset_manager import AssetManager
from utils.logger import GameLogger


class TestAssetManager(unittest.TestCase):
    """Test cases for the AssetManager class."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        # Initialize pygame
        pygame.init()
        # Make sure we have a display surface for loading images
        pygame.display.set_mode((100, 100), pygame.NOFRAME)
        # Initialize logger
        cls.logger = GameLogger.get_logger("test_assets")
        # Create a test instance of AssetManager
        cls.asset_manager = AssetManager()

    @classmethod
    def tearDownClass(cls):
        """Tear down test fixtures."""
        pygame.quit()

    def test_initialize(self):
        """Test that AssetManager initializes correctly."""
        self.assertTrue(self.asset_manager.initialized)
        self.assertIsInstance(self.asset_manager.fonts, dict)
        self.assertIsInstance(self.asset_manager.images, dict)
        self.assertIsInstance(self.asset_manager.ui_elements, dict)
        self.assertIsInstance(self.asset_manager.spritesheets, dict)
        self.assertIsInstance(self.asset_manager.spritesheet_data, dict)

    def test_get_font(self):
        """Test that fonts can be retrieved."""
        # Test getting different fonts
        for font_name in self.asset_manager.FONTS:
            for size_name in self.asset_manager.FONT_SIZES:
                font = self.asset_manager.get_font(font_name, size_name)
                self.assertIsNotNone(font)
                self.assertIsInstance(font, pygame.font.Font)

        # Test fallback to system font
        font = self.asset_manager.get_font("nonexistent", "normal")
        self.assertIsNotNone(font)
        self.assertIsInstance(font, pygame.font.Font)

    def test_load_spritesheet(self):
        """Test loading UI spritesheets."""
        for theme in self.asset_manager.UI_THEMES:
            spritesheet = self.asset_manager.load_spritesheet(theme)
            self.assertIsNotNone(spritesheet)
            self.assertIsInstance(spritesheet, pygame.Surface)

            # Check that the spritesheet is cached
            sheet_name = self.asset_manager.UI_THEMES[theme]
            self.assertIn(sheet_name, self.asset_manager.spritesheets)

            # Check that XML data was parsed
            self.assertIn(sheet_name, self.asset_manager.spritesheet_data)
            self.assertGreater(len(self.asset_manager.spritesheet_data[sheet_name]), 0)

    def test_get_ui_element(self):
        """Test retrieving UI elements from spritesheets."""
        # Test UI elements from the blue theme
        test_elements = ["blue_button00.png", "blue_panel.png", "blue_checkmark.png"]

        for element_name in test_elements:
            ui_element = self.asset_manager.get_ui_element(element_name, "blue")
            self.assertIsNotNone(ui_element)
            self.assertIsInstance(ui_element, pygame.Surface)

            # Test that the element is cached
            element_key = f"blueSheet_{element_name}"
            self.assertIn(element_key, self.asset_manager.ui_elements)

        # Test fallback when theme doesn't exist
        ui_element = self.asset_manager.get_ui_element("blue_button00.png", "nonexistent")
        self.assertIsNotNone(ui_element)
        self.assertIsInstance(ui_element, pygame.Surface)

        # Test handling of nonexistent element
        ui_element = self.asset_manager.get_ui_element("nonexistent.png", "blue")
        self.assertIsNone(ui_element)

    def test_preload_ui_assets(self):
        """Test preloading UI assets."""
        # Clear any cached spritesheets
        self.asset_manager.spritesheets = {}
        self.asset_manager.spritesheet_data = {}

        # Preload all themes
        self.asset_manager.preload_ui_assets()

        # Check that all themes were loaded
        for theme in self.asset_manager.UI_THEMES:
            sheet_name = self.asset_manager.UI_THEMES[theme]
            self.assertIn(sheet_name, self.asset_manager.spritesheets)
            self.assertIn(sheet_name, self.asset_manager.spritesheet_data)


if __name__ == "__main__":
    unittest.main()
