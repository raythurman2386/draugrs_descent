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
        sheet_path = os.path.normpath(os.path.join(self.INTERFACE_PATH, "Spritesheet", f"{sheet_name}.png"))
        xml_path = os.path.normpath(os.path.join(self.INTERFACE_PATH, "Spritesheet", f"{sheet_name}.xml"))

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
                    "height": height
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
        if (sheet_name not in self.spritesheet_data or 
            element_name not in self.spritesheet_data[sheet_name]):
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
        element.blit(spritesheet, (0, 0), 
                    (sprite_data["x"], sprite_data["y"], 
                     sprite_data["width"], sprite_data["height"]))
                     
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
        svg_path = os.path.normpath(os.path.join(self.INTERFACE_PATH, "Vector", theme, f"{element_name}.svg"))
        
        # Generate a unique key for the cached element
        element_key = f"svg_{theme}_{element_name}"
        if scale:
            element_key += f"_{scale[0]}x{scale[1]}"
        
        # Check if we already loaded this element
        if element_key in self.ui_elements:
            return self.ui_elements[element_key]
            
        try:
            if os.path.exists(svg_path):
                logger.debug(f"Loading SVG UI element: {svg_path}")
                
                # For SVG files, we need to use an external library or Pygame's built-in svg support
                # in newer versions. Here we'll use a basic approach that works with Pygame.
                try:
                    # Try to use pygame's built-in SVG support (Pygame 2.x+)
                    if hasattr(pygame, 'svg') and hasattr(pygame.svg, 'load_svg'):
                        svg_surface = pygame.svg.load_svg(svg_path)
                    elif scale:
                        # Fallback: render SVG using cairosvg if available
                        try:
                            import io
                            import cairosvg
                            
                            # Convert SVG to PNG in memory
                            png_data = cairosvg.svg2png(url=svg_path, 
                                                       output_width=scale[0], 
                                                       output_height=scale[1])
                            
                            # Load the PNG data into a Pygame surface
                            png_file = io.BytesIO(png_data)
                            svg_surface = pygame.image.load(png_file)
                        except ImportError:
                            logger.warning("cairosvg not available for SVG conversion. Using basic approach.")
                            # Very basic fallback - create a colored rectangle placeholder
                            if scale:
                                svg_surface = pygame.Surface(scale, pygame.SRCALPHA)
                            else:
                                svg_surface = pygame.Surface((100, 50), pygame.SRCALPHA)
                            
                            # Use a color based on the theme
                            theme_colors = {
                                "Blue": (66, 148, 255, 255),
                                "Green": (113, 201, 55, 255),
                                "Grey": (180, 180, 180, 255),
                                "Red": (255, 97, 87, 255),
                                "Yellow": (245, 230, 83, 255)
                            }
                            color = theme_colors.get(theme, (100, 100, 100, 255))
                            
                            # Fill with theme color
                            svg_surface.fill(color)
                    else:
                        # No scale specified and no SVG support
                        logger.warning("No SVG support available and no scale specified.")
                        svg_surface = pygame.Surface((100, 50), pygame.SRCALPHA)
                        svg_surface.fill((200, 200, 200, 255))
                        
                    # Scale if needed
                    if scale and hasattr(pygame, 'svg') and hasattr(pygame.svg, 'load_svg'):
                        svg_surface = pygame.transform.smoothscale(svg_surface, scale)
                        
                    # Cache the element
                    self.ui_elements[element_key] = svg_surface
                    return svg_surface
                    
                except Exception as e:
                    logger.error(f"Error loading SVG file {svg_path}: {e}")
                    
                    # Create a placeholder for the failed SVG
                    if scale:
                        placeholder = pygame.Surface(scale, pygame.SRCALPHA)
                    else:
                        placeholder = pygame.Surface((100, 50), pygame.SRCALPHA)
                    
                    placeholder.fill((255, 0, 255, 128))  # Magenta for error indication
                    return placeholder
            else:
                logger.warning(f"SVG UI element not found: {svg_path}")
                
                # Create a placeholder for the missing SVG
                if scale:
                    placeholder = pygame.Surface(scale, pygame.SRCALPHA)
                else:
                    placeholder = pygame.Surface((100, 50), pygame.SRCALPHA)
                
                placeholder.fill((255, 0, 0, 128))  # Red for missing files
                return placeholder
                
        except Exception as e:
            logger.error(f"Error processing SVG UI element {element_name}: {e}")
            
            # Create a placeholder for error cases
            if scale:
                placeholder = pygame.Surface(scale, pygame.SRCALPHA)
            else:
                placeholder = pygame.Surface((100, 50), pygame.SRCALPHA)
            
            placeholder.fill((255, 255, 0, 128))  # Yellow for general errors
            return placeholder

# Create a global instance of the asset manager
game_asset_manager = AssetManager()
