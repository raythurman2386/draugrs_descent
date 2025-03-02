import pygame
from scenes import (
    SceneManager, 
    MainMenuScene, 
    GameScene, 
    PauseMenuScene, 
    GameOverScene
)
from utils.logger import GameLogger

# Get a logger for the main module
logger = GameLogger.get_logger("main")

def main():
    # Initialize Pygame
    pygame.init()
    pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Draugr's Descent")
    
    logger.info("Starting Draugr's Descent")
    
    # Create scene manager and scenes
    scene_manager = SceneManager()
    
    # Add all scenes
    scene_manager.add_scene("main_menu", MainMenuScene())
    scene_manager.add_scene("game", GameScene())
    scene_manager.add_scene("pause", PauseMenuScene())
    scene_manager.add_scene("game_over", GameOverScene())
    
    logger.info("All scenes initialized")
    
    # Set starting scene
    scene_manager.set_active_scene("main_menu")
    
    # Run the game
    logger.info("Starting game loop")
    scene_manager.run()
    logger.info("Game ended")

if __name__ == "__main__":
    main()