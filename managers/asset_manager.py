import os
import xml.etree.ElementTree as ET
import pygame
from utils.logger import GameLogger

# Get a logger for the asset manager
logger = GameLogger.get_logger("assets")


class AssetManager:
    """Manages game assets including fonts, images, UI elements, and other resources."""

    # Asset paths
    FONT_PATH = "assets/fonts"
    IMAGE_PATH = "assets/images"
    INTERFACE_PATH = "assets/interface"
    SCRIBBLE_DUNGEONS_PATH = "assets/scribble_dungeons"

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

    # UI color schemes
    UI_THEMES = {
        "blue": "blueSheet",
        "green": "greenSheet",
        "grey": "greySheet",
        "red": "redSheet",
        "yellow": "yellowSheet",
    }

    def __init__(self):
        """Initialize the asset manager."""
        self.initialized = False
        self.fonts = {}  # Dictionary to store loaded fonts
        self.images = {}  # Dictionary to store loaded images
        self.ui_elements = {}  # Dictionary to store UI elements
        self.spritesheets = {}  # Dictionary to store spritesheets
        self.spritesheet_data = {}  # Dictionary to store spritesheet metadata

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

    def load_spritesheet(self, theme="blue"):
        """
        Load a UI spritesheet and its XML data.

        Args:
            theme: The color theme of the spritesheet (blue, green, grey, red, yellow)

        Returns:
            The loaded spritesheet surface
        """
        if theme not in self.UI_THEMES:
            logger.warning(f"UI theme '{theme}' not found, using blue theme")
            theme = "blue"

        sheet_name = self.UI_THEMES[theme]

        # Convert forward slashes to backslashes for Windows paths
        sheet_path = os.path.normpath(
            os.path.join(self.INTERFACE_PATH, "Spritesheet", f"{sheet_name}.png")
        )
        xml_path = os.path.normpath(
            os.path.join(self.INTERFACE_PATH, "Spritesheet", f"{sheet_name}.xml")
        )

        # Check if already loaded
        if sheet_name in self.spritesheets:
            return self.spritesheets[sheet_name]

        try:
            # Load the spritesheet image
            if os.path.exists(sheet_path):
                # Make sure we have a display initialized before loading the image
                if pygame.display.get_surface() is None:
                    # Create a small display if none exists (for unit testing)
                    pygame.display.set_mode((1, 1), pygame.NOFRAME)

                spritesheet = pygame.image.load(sheet_path).convert_alpha()
                self.spritesheets[sheet_name] = spritesheet
                logger.debug(f"Loaded spritesheet: {sheet_path}")
            else:
                logger.warning(f"Spritesheet file not found: {sheet_path}")
                return None

            # Load the XML data
            if os.path.exists(xml_path):
                self._parse_spritesheet_xml(sheet_name, xml_path)
            else:
                logger.warning(f"Spritesheet XML file not found: {xml_path}")

            return self.spritesheets.get(sheet_name)
        except Exception as e:
            logger.error(f"Error loading spritesheet {sheet_path}: {e}")
            return None

    def _parse_spritesheet_xml(self, sheet_name, xml_path):
        """
        Parse the XML data for a spritesheet to extract individual sprite information.

        Args:
            sheet_name: The name of the spritesheet
            xml_path: Path to the XML file
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Initialize dictionary for this spritesheet if it doesn't exist
            if sheet_name not in self.spritesheet_data:
                self.spritesheet_data[sheet_name] = {}

            # Parse each SubTexture element
            for subtexture in root.findall(".//SubTexture"):
                name = subtexture.get("name")
                x = int(subtexture.get("x"))
                y = int(subtexture.get("y"))
                width = int(subtexture.get("width"))
                height = int(subtexture.get("height"))

                # Store sprite data
                self.spritesheet_data[sheet_name][name] = {
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                }

            logger.debug(f"Parsed {len(self.spritesheet_data[sheet_name])} sprites from {xml_path}")
        except Exception as e:
            logger.error(f"Error parsing spritesheet XML {xml_path}: {e}")

    def get_ui_element(self, element_name, theme="blue"):
        """
        Get a UI element from a spritesheet by name.

        Args:
            element_name: The name of the UI element
            theme: The color theme of the spritesheet

        Returns:
            A pygame Surface with the extracted UI element
        """
        if theme not in self.UI_THEMES:
            logger.warning(f"UI theme '{theme}' not found, using blue theme")
            theme = "blue"

        sheet_name = self.UI_THEMES[theme]

        # Check if we need to load the spritesheet
        if sheet_name not in self.spritesheets:
            if self.load_spritesheet(theme) is None:
                return None

        # Check if we have data for this element
        if (
            sheet_name not in self.spritesheet_data
            or element_name not in self.spritesheet_data[sheet_name]
        ):
            logger.warning(f"UI element '{element_name}' not found in theme '{theme}'")
            return None

        # Generate a key for the cached element
        element_key = f"{sheet_name}_{element_name}"

        # Check if we already extracted this element
        if element_key in self.ui_elements:
            return self.ui_elements[element_key]

        # Extract the element from the spritesheet
        sprite_data = self.spritesheet_data[sheet_name][element_name]
        spritesheet = self.spritesheets[sheet_name]

        # Create a new surface for the element
        element = pygame.Surface((sprite_data["width"], sprite_data["height"]), pygame.SRCALPHA)

        # Copy the element from the spritesheet
        element.blit(
            spritesheet,
            (0, 0),
            (sprite_data["x"], sprite_data["y"], sprite_data["width"], sprite_data["height"]),
        )

        # Cache the element
        self.ui_elements[element_key] = element

        return element

    def load_scribble_tileset(self, filename, directory="Tilesheet"):
        """
        Load a tileset from the Scribble Dungeons assets.

        Args:
            filename: Name of the tileset file
            directory: Subdirectory within SCRIBBLE_DUNGEONS_PATH (default: Tilesheet)

        Returns:
            A pygame Surface with the tileset
        """
        path = os.path.normpath(os.path.join(self.SCRIBBLE_DUNGEONS_PATH, directory, filename))

        # Check if already loaded
        if path in self.images:
            return self.images[path]

        try:
            if os.path.exists(path):
                # Load the tileset
                tileset = pygame.image.load(path).convert_alpha()

                # Cache the tileset
                self.images[path] = tileset
                logger.debug(f"Loaded scribble tileset: {path}")
                return tileset
            else:
                logger.warning(f"Scribble tileset file not found: {path}")
                return None
        except Exception as e:
            logger.error(f"Error loading scribble tileset {path}: {e}")
            return None

    def preload_ui_assets(self, themes=None):
        """
        Preload all UI assets from the specified themes.

        Args:
            themes: List of themes to preload (if None, preloads all themes)
        """
        if themes is None:
            themes = list(self.UI_THEMES.keys())

        for theme in themes:
            if theme in self.UI_THEMES:
                logger.info(f"Preloading UI assets for theme: {theme}")
                self.load_spritesheet(theme)
            else:
                logger.warning(f"Unknown theme: {theme}")

    def get_svg_ui_element(self, element_name, theme="blue", scale=None):
        """
        Load an SVG UI element from the Vector directory.

        Args:
            element_name: Name of the SVG element (e.g., 'slide_horizontal_color')
            theme: Color theme (blue, green, grey, red, yellow)
            scale: Optional (width, height) tuple to scale the SVG

        Returns:
            A pygame Surface with the loaded SVG element
        """
        # Validate theme
        theme = theme.capitalize()  # SVG folders use capitalized names (Blue, Green, etc.)
        valid_themes = ["Blue", "Green", "Grey", "Red", "Yellow"]
        if theme not in valid_themes:
            logger.warning(f"SVG UI theme '{theme}' not found, using Blue theme")
            theme = "Blue"

        # Construct the SVG path
        svg_path = os.path.normpath(
            os.path.join(self.INTERFACE_PATH, "Vector", theme, f"{element_name}.svg")
        )

        # Generate a unique key for the cached element
        element_key = f"svg_{theme}_{element_name}"
        if scale:
            element_key += f"_{scale[0]}x{scale[1]}"

        # Check if we already loaded this element
        if element_key in self.ui_elements:
            return self.ui_elements[element_key]

        try:
            if not os.path.exists(svg_path):
                logger.warning(f"SVG file not found: {svg_path}")
                # Return an empty surface
                surface = pygame.Surface((10, 10), pygame.SRCALPHA)
                surface.fill((255, 0, 255, 128))  # Purple semi-transparent fill for missing assets
                if scale:
                    surface = pygame.transform.scale(surface, scale)
                self.ui_elements[element_key] = surface
                return surface

            # Parse the SVG to extract dimensions and data
            tree = ET.parse(svg_path)
            root = tree.getroot()

            # Get SVG dimensions
            width = int(float(root.get("width", "100")))
            height = int(float(root.get("height", "100")))

            # Create a surface
            if scale:
                width, height = scale

            # Create a surface with transparency
            surface = pygame.Surface((width, height), pygame.SRCALPHA)

            # For simple SVGs (like Kenny's UI elements), we can extract the path data
            # and render it as a filled rectangle or polygon, but that's complex
            # Instead, for this implementation, we'll just fill the surface with the theme color

            # Map theme to color
            theme_colors = {
                "Blue": (0, 112, 224, 255),  # Blue
                "Green": (0, 204, 94, 255),  # Green
                "Grey": (128, 128, 128, 255),  # Grey
                "Red": (204, 51, 63, 255),  # Red
                "Yellow": (244, 180, 27, 255),  # Yellow
            }

            color = theme_colors.get(theme, (0, 112, 224, 255))  # Default to blue

            # Fill the surface with the theme color (with transparency)
            surface.fill(color)

            # Cache and return the element
            self.ui_elements[element_key] = surface
            return surface

        except Exception as e:
            logger.error(f"Error loading SVG element: {e}")
            # Return an empty surface on error
            surface = pygame.Surface((10, 10), pygame.SRCALPHA)
            surface.fill((255, 0, 0, 128))  # Red semi-transparent fill for error
            if scale:
                surface = pygame.transform.scale(surface, scale)
            self.ui_elements[element_key] = surface
            return surface

    def get_character_sprite(self, color, width=None, height=None):
        """
        Load a character sprite from the scribble_dungeons assets.

        Args:
            color: Color of the character (green, purple, red, yellow)
            width: Width to scale the sprite to (optional)
            height: Height to scale the sprite to (optional)

        Returns:
            A pygame Surface with the character sprite
        """
        # Validate color
        valid_colors = ["green", "purple", "red", "yellow"]
        if color not in valid_colors:
            logger.warning(f"Invalid character color '{color}', using 'green' instead")
            color = "green"

        # Generate a unique key for the cached image
        image_key = f"character_{color}"
        if width and height:
            image_key += f"_{width}x{height}"

        # Check if we already loaded this character
        if image_key in self.images:
            return self.images[image_key]

        try:
            # Construct the image path
            character_path = os.path.join(
                self.SCRIBBLE_DUNGEONS_PATH, "characters", f"{color}_character.png"
            )

            if not os.path.exists(character_path):
                logger.warning(f"Character sprite not found: {character_path}")

                # Create a colored rectangle as a fallback
                surface = pygame.Surface((width or 50, height or 50), pygame.SRCALPHA)

                # Map color names to RGB values
                color_map = {
                    "green": (0, 204, 0),
                    "purple": (155, 0, 255),
                    "red": (255, 0, 0),
                    "yellow": (255, 255, 0),
                }

                rgb_color = color_map.get(color, (0, 204, 0))  # Default to green
                surface.fill(rgb_color)
            else:
                # Load the image
                surface = pygame.image.load(character_path).convert_alpha()

                # Scale if dimensions provided
                if width and height:
                    surface = pygame.transform.scale(surface, (width, height))

            # Cache and return the image
            self.images[image_key] = surface
            return surface

        except Exception as e:
            logger.error(f"Error loading character sprite: {e}")

            # Create a fallback colored rectangle on error
            surface = pygame.Surface((width or 50, height or 50), pygame.SRCALPHA)
            surface.fill((255, 0, 255))  # Purple for errors

            # Cache and return the fallback image
            self.images[image_key] = surface
            return surface


# Create a global instance of the asset manager
game_asset_manager = AssetManager()
