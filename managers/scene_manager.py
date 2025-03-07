import pygame
from utils.performance import performance
from utils.logger import GameLogger
from utils.utils import adjust_log_level
import logging

logger = GameLogger.get_logger("scene_manager")


class SceneManager:
    """Manages all game scenes and transitions between them."""

    def __init__(self):
        self.scenes = {}
        self.current_scene = None
        self.running = True

    def add_scene(self, scene_name, scene_instance):
        """Add a scene to the manager."""
        self.scenes[scene_name] = scene_instance
        # Set scene_manager reference in the scene
        scene_instance.scene_manager = self

    def set_active_scene(self, scene_name):
        """Set the active scene."""
        if scene_name in self.scenes:
            self.current_scene = self.scenes[scene_name]

            # We no longer automatically reset scenes here
            # This allows the game to properly resume from pause

            pygame.display.set_caption(f"Draugr's Descent - {scene_name}")
        else:
            raise ValueError(f"Scene '{scene_name}' not found.")

    def run(self):
        """Main game loop."""
        if not self.current_scene:
            raise ValueError("No active scene set.")

        frame_rate = 60
        logger.info("Starting game loop with performance monitoring enabled")

        while self.running:
            # Start timing the frame
            performance.start_frame()

            # Process events section
            performance.start_section("events")
            events = pygame.event.get()

            # Check for quit event
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                # Toggle performance metrics display with F4
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                    performance.toggle_metrics_display()
                    logger.debug("Performance metrics display toggled")
                # Log level adjustment keybinds
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                    adjust_log_level(logging.DEBUG)
                    logger.debug("Debug logging enabled")
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
                    adjust_log_level(logging.INFO)
                    logger.info("Info logging enabled")
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
                    adjust_log_level(logging.WARNING)
                    logger.warning("Warning logging enabled")

            # Process scene events
            if self.current_scene.process_events(events):
                self.running = False
            performance.end_section()

            # Update scene section
            performance.start_section("update")
            self.current_scene.update()
            performance.end_section()

            # Render scene section
            performance.start_section("render")
            self.current_scene.render()

            # Draw performance metrics if enabled
            performance.draw_metrics(pygame.display.get_surface())

            pygame.display.flip()
            performance.end_section()

            # Handle scene transition
            performance.start_section("scene_transition")
            if self.current_scene.done:
                if self.current_scene.next_scene:
                    self.set_active_scene(self.current_scene.next_scene)
                    self.current_scene.done = False
                    self.current_scene.next_scene = None
                else:
                    self.running = False
            performance.end_section()

            # Control frame rate
            self.current_scene.clock.tick(frame_rate)

        logger.info("Game loop ended")
        # Clean up
        pygame.quit()
