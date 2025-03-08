import pygame
from utils.logger import GameLogger

# Get a logger for the tiled map renderer
logger = GameLogger.get_logger("tiledmap")


class TiledMapRenderer:
    """Renders Tiled maps efficiently with camera support."""

    def __init__(self, tiled_map):
        """
        Initialize the map renderer.

        Args:
            tiled_map: A pytmx.TiledMap object loaded from the asset manager
        """
        self.tiled_map = tiled_map

        # Default dimensions in case of issues
        self.width = 800
        self.height = 600

        # Update with actual dimensions if available
        if hasattr(tiled_map, "width") and hasattr(tiled_map, "tilewidth"):
            self.width = tiled_map.width * tiled_map.tilewidth
        if hasattr(tiled_map, "height") and hasattr(tiled_map, "tileheight"):
            self.height = tiled_map.height * tiled_map.tileheight

        # Cache for map surfaces
        self.map_layers = {}

        # Prerender the map layers that don't change
        try:
            self._prerender_map_layers()
            logger.info(f"TiledMapRenderer initialized for map size: {self.width}x{self.height}")
        except Exception as e:
            logger.warning(f"Failed to prerender map layers: {e}")
            # Create a simple checkerboard pattern as fallback
            self._create_fallback_layer()

    def _create_fallback_layer(self):
        """Create a fallback checkerboard pattern when map rendering fails."""
        fallback = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Draw a checkerboard pattern
        colors = [(50, 50, 50, 255), (70, 70, 70, 255)]
        tile_size = 64

        for y in range(0, self.height, tile_size):
            for x in range(0, self.width, tile_size):
                color_index = ((x // tile_size) + (y // tile_size)) % 2
                rect = pygame.Rect(x, y, tile_size, tile_size)
                pygame.draw.rect(fallback, colors[color_index], rect)

        # Store as default layer
        self.map_layers["fallback"] = fallback
        logger.info("Created fallback checkerboard pattern for map")

    def _prerender_map_layers(self):
        """Pre-render static map layers for better performance."""
        if not hasattr(self.tiled_map, "visible_layers"):
            raise ValueError("Tiled map does not have visible_layers attribute")

        layers_rendered = 0
        for layer in self.tiled_map.visible_layers:
            # Skip object layers, only render tile layers
            if hasattr(layer, "data"):
                logger.debug(f"Pre-rendering layer: {layer.name}")
                # Create surface for this layer
                layer_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

                # Draw all tiles for this layer
                for x in range(self.tiled_map.width):
                    for y in range(self.tiled_map.height):
                        try:
                            tile = self.tiled_map.get_tile_image(x, y, layer.id)
                            if tile:
                                # Calculate pixel position
                                px = x * self.tiled_map.tilewidth
                                py = y * self.tiled_map.tileheight
                                layer_surface.blit(tile, (px, py))
                        except Exception as e:
                            # Skip problematic tiles
                            logger.debug(f"Error rendering tile at ({x}, {y}): {e}")

                # Store the rendered layer
                self.map_layers[layer.name] = layer_surface
                layers_rendered += 1

        if layers_rendered == 0:
            # If no layers were successfully rendered, create a fallback
            self._create_fallback_layer()
        else:
            logger.info(f"Pre-rendered {layers_rendered} map layers")

    def render(self, surface, camera=None):
        """
        Render the map to the provided surface with optional camera support.

        Args:
            surface: Pygame surface to render the map onto
            camera: Optional Camera object to apply offset
        """
        if not self.map_layers:
            # If no layers are available, just return
            return

        if camera:
            # With camera, draw only the visible portion
            for layer_name, layer_surface in self.map_layers.items():
                # Calculate the source rect (area of the map to draw)
                src_rect = pygame.Rect(
                    -camera.camera.x, -camera.camera.y, surface.get_width(), surface.get_height()
                )

                # Calculate the dest position (where to draw on screen)
                dest_pos = (0, 0)

                # Draw the visible portion of the map
                surface.blit(layer_surface, dest_pos, src_rect)
        else:
            # Without camera, draw the entire map
            for layer_name, layer_surface in self.map_layers.items():
                surface.blit(layer_surface, (0, 0))

        logger.debug("Map rendered")

    def get_tile_properties(self, x, y, layer_id=0):
        """
        Get properties of a specific tile.

        Args:
            x: Tile x coordinate
            y: Tile y coordinate
            layer_id: Layer ID (default: 0 for first layer)

        Returns:
            Properties dictionary or None if no tile
        """
        try:
            tile = self.tiled_map.get_tile_properties(x, y, layer_id)
            return tile
        except Exception as e:
            logger.debug(f"Error getting tile properties at ({x}, {y}): {e}")
            return None
