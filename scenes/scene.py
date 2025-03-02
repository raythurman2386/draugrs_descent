import pygame


class Scene:
    """Base class for all game scenes."""

    def __init__(self):
        self.next_scene = None
        self.done = False
        self.screen = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 32)

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

    def draw_text(self, text, color, x, y):
        """Helper method to draw text on the screen."""
        text_surface = self.font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.center = (x, y)
        self.screen.blit(text_surface, text_rect)
