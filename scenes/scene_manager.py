import pygame

class SceneManager:
    """Manages all game scenes and transitions between them."""
    
    def __init__(self):
        self.scenes = {}
        self.current_scene = None
        self.running = True
        
    def add_scene(self, scene_name, scene_instance):
        """Add a scene to the manager."""
        self.scenes[scene_name] = scene_instance
        
    def set_active_scene(self, scene_name):
        """Set the active scene."""
        if scene_name in self.scenes:
            self.current_scene = self.scenes[scene_name]
            pygame.display.set_caption(f"Draugr's Descent - {scene_name}")
        else:
            raise ValueError(f"Scene '{scene_name}' not found.")
            
    def run(self):
        """Main game loop."""
        if not self.current_scene:
            raise ValueError("No active scene set.")
            
        frame_rate = 60
        
        while self.running:
            events = pygame.event.get()
            
            # Check for quit event
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    break
            
            # Process scene events
            if self.current_scene.process_events(events):
                self.running = False
                
            # Update scene
            self.current_scene.update()
            
            # Render scene
            self.current_scene.render()
            pygame.display.flip()
            
            # Handle scene transition
            if self.current_scene.done:
                if self.current_scene.next_scene:
                    self.set_active_scene(self.current_scene.next_scene)
                    self.current_scene.done = False
                    self.current_scene.next_scene = None
                else:
                    self.running = False
                    
            # Control frame rate
            self.current_scene.clock.tick(frame_rate)
            
        # Clean up
        pygame.quit() 