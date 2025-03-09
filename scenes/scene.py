import pygame
from managers.sound_manager import game_sound_manager
from managers.asset_manager import game_asset_manager


class Scene:
    """Base class for all game scenes."""

    def __init__(self):
        self.next_scene = None
        self.done = False
        self.screen = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        self.scene_manager = None  # Will be set by SceneManager
        self.sound_manager = game_sound_manager
        self.asset_manager = game_asset_manager

        # Set up fonts using the asset manager
        self._setup_fonts()

    def _setup_fonts(self):
        """Set up fonts for the scene using the asset manager."""
        # Get fonts from asset manager
        self.title_font = self.asset_manager.get_font("default", "title")
        self.heading_font = self.asset_manager.get_font("default", "heading")
        self.font = self.asset_manager.get_font("default", "normal")
        self.ui_font = self.asset_manager.get_font("square", "ui")
        self.small_font = self.asset_manager.get_font("default", "small")
        self.extra_small_font = self.asset_manager.get_font("default", "extra_small")
        self.tiny_font = self.asset_manager.get_font("default", "tiny")
        self.narrow_font = self.asset_manager.get_font("narrow", "normal")

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
