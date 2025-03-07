import pygame
from scenes import MainMenuScene, GameScene, PauseMenuScene, GameOverScene, OptionsMenuScene
from managers import SceneManager, config
from utils.logger import GameLogger

# Get a logger for the main module
logger = GameLogger.get_logger("main")


def main():
    # Initialize Pygame
    pygame.init()

    # Debug the config loading
    logger.info("Printing configuration for debugging")
    config.debug_print_config()

    # Get screen configuration from config manager
    screen_width = config.get("screen", "width", default=800)
    screen_height = config.get("screen", "height", default=600)
    game_caption = config.get("screen", "caption", default="Draugr's Descent")

    # Create the game window
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption(game_caption)

    # Ensure the background is properly initialized
    screen.fill(config.get_color("black"))
    pygame.display.flip()

    logger.info(f"Starting {game_caption} with resolution {screen_width}x{screen_height}")

    # Create scene manager and scenes
    scene_manager = SceneManager()

    # Add all scenes
    scene_manager.add_scene("main_menu", MainMenuScene())
    scene_manager.add_scene("game", GameScene())
    scene_manager.add_scene("pause", PauseMenuScene())
    scene_manager.add_scene("game_over", GameOverScene())
    scene_manager.add_scene("options", OptionsMenuScene())

    logger.info("All scenes initialized")

    # Set starting scene
    scene_manager.set_active_scene("main_menu")

    # Run the game
    logger.info("Starting game loop")
    scene_manager.run()
    logger.info("Game ended")


if __name__ == "__main__":
    main()
