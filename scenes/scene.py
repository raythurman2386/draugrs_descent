import pygame
import os
from managers.sound_manager import game_sound_manager

# Font file paths
FONT_PATH = "assets/fonts"
DEFAULT_FONT = os.path.join(FONT_PATH, "kenney_future.ttf")
NARROW_FONT = os.path.join(FONT_PATH, "kenney_future_narrow.ttf")
SQUARE_FONT = os.path.join(FONT_PATH, "kenney_future_square.ttf")


class Scene:
    """Base class for all game scenes."""

    def __init__(self):
        self.next_scene = None
        self.done = False
        self.screen = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        self.scene_manager = None  # Will be set by SceneManager
        self.sound_manager = game_sound_manager

        # Load custom fonts
        self._load_fonts()

    def _load_fonts(self):
        """Load custom fonts for the scene."""
        try:
            # Default system font fallback
            self.font = pygame.font.SysFont("Arial", 32)

            # Try to load custom fonts if they exist
            if os.path.exists(DEFAULT_FONT):
                self.title_font = pygame.font.Font(DEFAULT_FONT, 64)
                self.font = pygame.font.Font(DEFAULT_FONT, 32)
                self.small_font = pygame.font.Font(DEFAULT_FONT, 24)

            if os.path.exists(NARROW_FONT):
                self.narrow_font = pygame.font.Font(NARROW_FONT, 32)

            if os.path.exists(SQUARE_FONT):
                self.ui_font = pygame.font.Font(SQUARE_FONT, 28)
        except Exception as e:
            print(f"Error loading fonts: {e}")
            # Fallback to system fonts if custom fonts fail
            self.title_font = pygame.font.SysFont("Arial", 64)
            self.small_font = pygame.font.SysFont("Arial", 24)
            self.narrow_font = pygame.font.SysFont("Arial", 32)
            self.ui_font = pygame.font.SysFont("Arial", 28)

    def process_events(self, events):
        """Process all events."""
        for event in events:
            if event.type == pygame.QUIT:
                return True
            self.handle_event(event)
        return False

    def handle_event(self, event):
        """Handle a single event. To be overridden by subclasses."""
        pass

    def update(self):
        """Update scene logic. To be overridden by subclasses."""
        pass

    def render(self):
        """Render the scene. To be overridden by subclasses."""
        pass

    def switch_to_scene(self, scene_name):
        """Signal the scene manager to switch to a different scene."""
        self.next_scene = scene_name
        self.done = True

    def draw_text(self, text, color, x, y, font=None):
        """Helper method to draw text on the screen."""
        if font is None:
            font = self.font

        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.center = (x, y)
        self.screen.blit(text_surface, text_rect)

    def play_scene_music(self, scene_key):
        """Play music appropriate for this scene."""
        self.sound_manager.play_music(scene_key)

    def play_sound(self, sound_name):
        """Play a sound effect."""
        self.sound_manager.play_sound(sound_name)
