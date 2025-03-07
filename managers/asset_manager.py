import os
import pygame
from utils.logger import GameLogger

# Get a logger for the asset manager
logger = GameLogger.get_logger("assets")


class AssetManager:
    """Manages game assets including fonts, images, and other resources."""

    # Asset paths
    FONT_PATH = "assets/fonts"
    IMAGE_PATH = "assets/images"

    # Font filenames
    FONTS = {
        "default": "kenney_future.ttf",
        "narrow": "kenney_future_narrow.ttf",
        "square": "kenney_future_square.ttf",
    }

    # Font sizes
    FONT_SIZES = {
        "title": 48,
        "heading": 32,
        "normal": 28,
        "ui": 24,
        "small": 20,
    }

    def __init__(self):
        """Initialize the asset manager."""
        self.initialized = False
        self.fonts = {}  # Dictionary to store loaded fonts
        self.images = {}  # Dictionary to store loaded images

        # Initialize pygame if not already done
        if not pygame.get_init():
            pygame.init()

        self.initialized = True
        self._load_fonts()
        logger.info("Asset manager initialized")

    def _load_fonts(self):
        """Load all fonts into memory."""
        if not self.initialized:
            return

        # Create fonts dictionary structure
        for font_name in self.FONTS:
            self.fonts[font_name] = {}

        # Add some fallback system fonts
        self.fonts["system"] = {}

        try:
            # Load each font at different sizes
            for font_name, filename in self.FONTS.items():
                font_path = os.path.join(self.FONT_PATH, filename)

                if os.path.exists(font_path):
                    # Load the font at each size
                    for size_name, size in self.FONT_SIZES.items():
                        self.fonts[font_name][size_name] = pygame.font.Font(font_path, size)
                    logger.debug(f"Loaded font: {font_name}")
                else:
                    logger.warning(f"Font file not found: {font_path}")
                    # Use system font as fallback
                    for size_name, size in self.FONT_SIZES.items():
                        self.fonts[font_name][size_name] = pygame.font.SysFont("Arial", size)

            # Load system fonts
            for size_name, size in self.FONT_SIZES.items():
                self.fonts["system"][size_name] = pygame.font.SysFont("Arial", size)

        except Exception as e:
            logger.error(f"Error loading fonts: {e}")
            # Ensure we have at least some fonts available
            for size_name, size in self.FONT_SIZES.items():
                self.fonts["system"][size_name] = pygame.font.SysFont("Arial", size)

    def get_font(self, font_name="default", size_name="normal"):
        """
        Get a font by name and size.

        Args:
            font_name: The name of the font (default, narrow, square, system)
            size_name: The size of the font (title, heading, normal, ui, small)

        Returns:
            A pygame Font object
        """
        # Handle missing fonts
        if font_name not in self.fonts:
            logger.warning(f"Font '{font_name}' not found, using system font")
            font_name = "system"

        # Handle missing sizes
        if size_name not in self.FONT_SIZES:
            logger.warning(f"Font size '{size_name}' not found, using normal size")
            size_name = "normal"

        return self.fonts[font_name][size_name]

    def load_image(self, filename, directory=None, convert_alpha=True):
        """
        Load an image from the specified directory.

        Args:
            filename: Name of the image file
            directory: Subdirectory within IMAGE_PATH (optional)
            convert_alpha: Whether to convert the image for alpha transparency

        Returns:
            A pygame Surface with the image
        """
        if not self.initialized:
            return None

        # Construct the complete path
        if directory:
            path = os.path.join(self.IMAGE_PATH, directory, filename)
        else:
            path = os.path.join(self.IMAGE_PATH, filename)

        # Check if already loaded
        if path in self.images:
            return self.images[path]

        try:
            if os.path.exists(path):
                # Load the image
                if convert_alpha:
                    image = pygame.image.load(path).convert_alpha()
                else:
                    image = pygame.image.load(path).convert()

                # Cache the image
                self.images[path] = image
                logger.debug(f"Loaded image: {path}")
                return image
            else:
                logger.warning(f"Image file not found: {path}")
                return None
        except Exception as e:
            logger.error(f"Error loading image {path}: {e}")
            return None


# Create a global instance of the asset manager
game_asset_manager = AssetManager()
