import pygame
import random

from .scene import Scene
from objects import Player, Enemy, Powerup
from objects.enemy import create_enemy
from utils import (
    CollisionSystem,
    handle_projectile_enemy_collision,
    handle_enemy_projectile_player_collision,
    handle_player_enemy_collision,
    handle_player_powerup_collision,
)
from utils.camera import Camera
from utils.tiledmap import TiledMapRenderer
from managers import config, game_state, ScoreManager, game_asset_manager
from managers.game_state_manager import GameState
from utils.logger import GameLogger
import logging

# Get a logger for the game scene
logger = GameLogger.get_logger("game_scene")


class GameScene(Scene):
    """Main gameplay scene."""

    def __init__(self):
        super().__init__()

        logger.info("Initializing GameScene")

        self._initialize_game()

        # Start the game music
        self.play_scene_music("game")

    def _initialize_game(self):
        """Initialize or reinitialize all game objects and state."""
        # Create game object groups
        self.player = Player()
        self.all_sprites = pygame.sprite.Group(self.player)
        self.enemy_group = pygame.sprite.Group()
        self.projectile_group = pygame.sprite.Group()
        self.powerup_group = pygame.sprite.Group()

        # Set player references
        self.player.screen = self.screen
        self.player.all_sprites = self.all_sprites
        self.player.enemy_group = self.enemy_group
        self.player.projectile_group = self.projectile_group

        # Enemy spawn timer
        self.last_spawn_time = pygame.time.get_ticks()

        # Pause flag
        self.paused = False

        # Initialize score manager
        self.score_manager = ScoreManager()

        # Last time score was updated for time survived
        self.last_time_score_update = pygame.time.get_ticks()

        # Game stats
        self.enemies_killed = 0
        self.time_survived = 0
        self.start_time = pygame.time.get_ticks()
        self.powerups_collected = 0

        # Get screen dimensions from config for collision system
        screen_width = config.get("screen", "width", default=800)
        screen_height = config.get("screen", "height", default=600)

        # Initialize the collision system
        self.collision_system = CollisionSystem(
            screen_width=screen_width,
            screen_height=screen_height,
            algorithm=CollisionSystem.SPATIAL_HASH,
            cell_size=64,
        )

        # Load the tiled map
        self._load_map()

        # Set game state to PLAYING
        game_state.change_state(GameState.PLAYING)

        logger.info("Game state initialized/reinitialized")

    def _load_map(self):
        """Load the tiled map and initialize camera."""
        # Load the map from the asset manager
        logger.info("Loading tiled map")
        try:
            tiled_map = game_asset_manager.load_tiled_map("Tiled/sampleMap.tmx")

            if tiled_map:
                # Create a map renderer
                self.map_renderer = TiledMapRenderer(tiled_map)

                # Get screen dimensions for camera
                screen_width = config.get("screen", "width", default=800)
                screen_height = config.get("screen", "height", default=600)

                # Create camera with map dimensions and screen dimensions
                self.camera = Camera(
                    self.map_renderer.width, self.map_renderer.height, screen_width, screen_height
                )

                # Set player map boundaries if player exists
                if hasattr(self, "player") and self.player:
                    self.player.map_width = self.map_renderer.width
                    self.player.map_height = self.map_renderer.height
                    logger.info(
                        f"Set player map boundaries to {self.map_renderer.width}x{self.map_renderer.height}"
                    )

                logger.info(
                    f"Map loaded successfully - dimensions: {self.map_renderer.width}x{self.map_renderer.height}"
                )
            else:
                logger.warning("Tiled map could not be loaded, using fallback background")
                self._setup_fallback_background()
        except Exception as e:
            # This will catch any issues with map loading, including in test environments
            logger.warning(f"Error loading map, using fallback background: {e}")
            self._setup_fallback_background()

    def _setup_fallback_background(self):
        """Set up a fallback colored background if map loading fails."""
        logger.info("Setting up fallback background")
        self.map_renderer = None
        self.camera = None

        # Set player boundaries to screen dimensions as fallback
        if hasattr(self, "player") and self.player:
            screen_width = config.get("screen", "width", default=800)
            screen_height = config.get("screen", "height", default=600)
            self.player.map_width = screen_width
            self.player.map_height = screen_height
            logger.info(f"Set player fallback boundaries to screen: {screen_width}x{screen_height}")

    def reset(self):
        """Reset the game scene to initial state when returning to this scene."""
        logger.info("Resetting GameScene")
        self._initialize_game()
        # Restart the game music when resetting
        self.play_scene_music("game")

    def spawn_enemy(self):
        """Spawn an enemy at a random screen edge."""
        current_time = pygame.time.get_ticks()
        enemy_spawn_interval = config.get("gameplay", "enemy_spawn_interval", default=1500)

        if current_time - self.last_spawn_time > enemy_spawn_interval:
            screen_width = config.get("screen", "width", default=800)
            screen_height = config.get("screen", "height", default=600)

            edge = random.randint(0, 3)
            if edge == 0:  # Top
                position = (
                    random.randint(0, screen_width),
                    0,  # Top edge
                )
            elif edge == 1:  # Bottom
                position = (
                    random.randint(0, screen_width),
                    screen_height,  # Bottom edge
                )
            elif edge == 2:  # Left
                position = (
                    0,  # Left edge
                    random.randint(0, screen_height),
                )
            else:  # Right
                position = (
                    screen_width,  # Right edge
                    random.randint(0, screen_height),
                )

            # Use the factory function to create an enemy (randomly selects type based on weights)
            enemy = create_enemy(position)

            self.enemy_group.add(enemy)
            self.all_sprites.add(enemy)
            self.last_spawn_time = current_time
            logger.debug(f"{enemy.enemy_type.capitalize()} enemy spawned at {position}")

    def handle_event(self, event):
        """Handle game-specific events."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                logger.info("Game paused")
                self.paused = True

                # Stop the game music before switching to pause menu
                self.sound_manager.stop_music()

                # Change state to PAUSED and switch scene
                game_state.change_state(GameState.PAUSED)
                self.switch_to_scene("pause")

    def update(self):
        """Update game state for the current frame."""
        if self.paused:
            return

        # Get key presses
        keys = pygame.key.get_pressed()
        self._handle_input(keys)

        # Spawn enemies on a timer
        current_time = pygame.time.get_ticks()
        enemy_spawn_interval = config.get("gameplay", "enemy_spawn_interval", default=1500)
        if current_time - self.last_spawn_time > enemy_spawn_interval:
            self.spawn_enemy()
            self.last_spawn_time = current_time

        # Update all sprites - enemy update needs player position
        self.player.update()

        # Update camera to follow player
        if self.camera:
            self.camera.update(self.player)

        current_time = pygame.time.get_ticks()
        for enemy in self.enemy_group:
            if hasattr(enemy, "enemy_type") and enemy.enemy_type == Enemy.TYPE_RANGED:
                # RangedEnemy needs additional parameters
                enemy.update(
                    self.player.rect.center, current_time, self.projectile_group, self.all_sprites
                )
            else:
                # Basic and Charger enemies just need player position
                enemy.update(self.player.rect.center, current_time)
        self.projectile_group.update()
        self.powerup_group.update()

        # Update the collision system with current game objects
        self.collision_system.update(
            self.projectile_group, self.enemy_group, self.player, self.powerup_group
        )

        # Check for collisions
        self._handle_collisions()

        # Check for dead enemies and create powerups
        for enemy in self.enemy_group.copy():
            if not enemy.alive():
                self.enemies_killed += 1
                self.score_manager.enemy_defeated()

                # Random chance to drop a powerup when an enemy is defeated
                if random.random() < 0.25:  # 25% chance
                    self.drop_powerup(enemy.rect.center)

        # Clean up off-screen projectiles
        screen_width = config.get("screen", "width", default=800)
        screen_height = config.get("screen", "height", default=600)
        for projectile in self.projectile_group.copy():
            if (
                projectile.rect.right < 0
                or projectile.rect.left > screen_width
                or projectile.rect.bottom < 0
                or projectile.rect.top > screen_height
            ):
                projectile.kill()

        # Update time survived
        self.time_survived = (current_time - self.start_time) // 1000

        # Add points for time survived (every 5 seconds)
        if current_time - self.last_time_score_update >= 5000:  # 5 seconds
            seconds_since_last_update = (current_time - self.last_time_score_update) // 1000
            self.score_manager.add_time_survived_points(seconds_since_last_update)
            self.last_time_score_update = current_time

        # Check for game over
        if self.player.current_health <= 0:
            # Save high score before game over
            self.score_manager.save_high_score()

            logger.info(
                f"Game over. Score: {self.score_manager.current_score}, High Score: {self.score_manager.high_score}, "
                f"Enemies killed: {self.enemies_killed}, Powerups: {self.powerups_collected}, Time survived: {self.time_survived}s"
            )

            # Change game state to GAME_OVER
            game_state.change_state(GameState.GAME_OVER)

            # Pass game stats to the game over scene
            game_over_scene = self.scene_manager.scenes["game_over"]
            game_over_scene.final_score = self.score_manager.current_score
            game_over_scene.high_score = self.score_manager.high_score
            game_over_scene.enemies_killed = self.enemies_killed
            game_over_scene.powerups_collected = self.powerups_collected
            game_over_scene.time_survived = self.time_survived

            self.switch_to_scene("game_over")

    def _handle_input(self, keys):
        """Handle player input that isn't already handled in Player.update()"""
        # Player movement and shooting is handled in Player.update()

        # If arrow keys are pressed (player is moving) and space is pressed (firing),
        # occasionally play sound
        player_moving = (
            keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_UP] or keys[pygame.K_DOWN]
        )

        if (
            player_moving
            and pygame.time.get_ticks() - self.player.last_shot_time > self.player.shot_cooldown
        ):
            if random.random() < 0.3:  # Don't play on every shot to avoid sound overload
                # Use asset manager to play sound
                self.play_sound("player_hit")

    def _handle_collisions(self):
        """Check for and handle all collisions."""
        # Projectiles vs Enemies - using optimized collision system
        projectile_hits = self.collision_system.check_projectile_enemy_collisions(
            self.projectile_group, self.enemy_group
        )

        for projectile, enemies in projectile_hits.items():
            for enemy in enemies:
                # Use the collision handler function
                if handle_projectile_enemy_collision(projectile, enemy):
                    self.play_sound("enemy_hit")
                    self.handle_enemy_death(enemy)
                    logger.debug(f"Enemy killed. Total killed: {self.enemies_killed}")

        # Enemy Projectiles vs Player - using optimized collision system
        if not self.player.invincible:
            projectile_hits = self.collision_system.check_enemy_projectile_player_collision(
                self.player, self.projectile_group
            )

            for projectile in projectile_hits:
                # Use the collision handler function
                if handle_enemy_projectile_player_collision(self.player, projectile):
                    self.play_sound("player_hit")

                    # Check if player died from this projectile hit
                    if self.player.current_health <= 0:
                        self.play_sound("game_lost")

        # Player vs Enemies - using optimized collision system
        if not self.player.invincible:
            enemy_collisions = self.collision_system.check_player_enemy_collisions(
                self.player, self.enemy_group
            )

            for enemy in enemy_collisions:
                if handle_player_enemy_collision(self.player, enemy):
                    self.play_sound("player_hit")

                    # Check if player died from this collision
                    if self.player.current_health <= 0:
                        self.play_sound("game_lost")

        # Player vs Powerups - using optimized collision system
        powerup_collisions = self.collision_system.check_player_powerup_collisions(
            self.player, self.powerup_group
        )

        for powerup in powerup_collisions:
            if powerup.active:
                # Play powerup collection sound
                self.play_sound("powerup_collect")

                # Apply powerup effect
                handle_player_powerup_collision(self.player, powerup)
                powerup.kill()  # Remove from all sprite groups
                self.powerups_collected += 1

                # Update score
                self.score_manager.powerup_collected()

                logger.info(
                    f"Powerup collected: {powerup.type}. Total collected: {self.powerups_collected}"
                )

    def handle_enemy_death(self, enemy):
        """Handle an enemy's death, including potential powerup drops."""
        # Remove enemy
        enemy.kill()
        self.enemies_killed += 1

        # Update score
        self.score_manager.enemy_defeated()

        # Random chance to drop a powerup (25% chance)
        if random.random() < 0.25:  # 25% chance
            self.drop_powerup(enemy.rect.center)

    def drop_powerup(self, position):
        """Create a random powerup at the given position and add it to the game."""
        # Select a random powerup type
        powerup_type = random.choice(["health", "shield", "weapon"])

        # Create the powerup
        powerup = Powerup(position, powerup_type)

        # Add to sprite groups
        self.powerup_group.add(powerup)
        self.all_sprites.add(powerup)

        logger.debug(f"Dropped {powerup_type} powerup at {position}")

    def render(self):
        """Render all game objects to the screen."""
        # Get screen color from config
        screen_color = config.get("screen", "background_color", default="#222222")

        # Fill the screen with background color
        self.screen.fill(pygame.Color(screen_color))

        # Render the tiled map if available
        if self.map_renderer and self.camera:
            self.map_renderer.render(self.screen, self.camera)

        # Render all sprites with camera offset if available
        if self.camera:
            for sprite in self.all_sprites:
                self.screen.blit(sprite.image, self.camera.apply(sprite))
        else:
            # Fallback to regular sprite drawing if no camera
            self.all_sprites.draw(self.screen)

        # Display game stats
        self._render_ui()

    def _render_ui(self):
        """Draw the game UI elements."""
        # Get health bar dimensions from config
        health_bar_width = config.get("ui", "health_bar_width", default=200)
        health_bar_height = config.get("ui", "health_bar_height", default=20)

        # Draw health bar
        health_ratio = self.player.current_health / self.player.max_health
        pygame.draw.rect(
            self.screen, (255, 0, 0), (10, 10, health_bar_width, health_bar_height)
        )  # Background
        pygame.draw.rect(
            self.screen,
            (0, 255, 0),
            (10, 10, health_bar_width * health_ratio, health_bar_height),
        )  # Health

        # Use small font for side UI elements to avoid cutoff
        ui_font = self.small_font if hasattr(self, "small_font") else self.font

        # Get screen dimensions from config
        screen_width = config.get("screen", "width", default=800)

        # Right-aligned game stats - moved further from the edge
        right_margin = 140  # Increased from 100 to give more space
        self.draw_text(
            f"Enemies: {self.enemies_killed}",
            (255, 255, 255),
            screen_width - right_margin,
            20,
            ui_font,
        )
        self.draw_text(
            f"Powerups: {self.powerups_collected}",
            (255, 255, 255),
            screen_width - right_margin,
            50,
            ui_font,
        )
        self.draw_text(
            f"Time: {self.time_survived}s",
            (255, 255, 255),
            screen_width - right_margin,
            80,
            ui_font,
        )

        # Draw score - centered
        score_text = f"Score: {self.score_manager.get_formatted_score()}"
        high_score_text = f"High: {self.score_manager.get_formatted_high_score()}"

        self.draw_text(score_text, (255, 255, 0), screen_width // 2, 20)  # Yellow color for score
        self.draw_text(
            high_score_text, (255, 165, 0), screen_width // 2, 50
        )  # Orange color for high score

    def resume_from_pause(self):
        """Resume the game after returning from pause menu."""
        self.paused = False

        # Reset game state to PLAYING
        game_state.change_state(GameState.PLAYING)

        # Play game music again (since we might have stopped it when pausing)
        self.play_scene_music("game")

        logger.info("Game resumed from pause")
        high_score_text = f"High: {self.score_manager.get_formatted_high_score()}"

        self.draw_text(score_text, (255, 255, 0), screen_width // 2, 20)  # Yellow color for score
        self.draw_text(
            high_score_text, (255, 165, 0), screen_width // 2, 50
        )  # Orange color for high score

    def resume_from_pause(self):
        """Resume the game after returning from pause menu."""
        self.paused = False

        # Reset game state to PLAYING
        game_state.change_state(GameState.PLAYING)

        # Play game music again (since we might have stopped it when pausing)
        self.play_scene_music("game")

        logger.info("Game resumed from pause")
