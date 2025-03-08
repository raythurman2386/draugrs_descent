import pygame
import random

from .scene import Scene
from objects import Player, Enemy, Powerup, ParticleSystem
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

# Get a logger for the game scene
logger = GameLogger.get_logger("game_scene")


class GameScene(Scene):
    """Main gameplay scene."""

    def __init__(self):
        super().__init__()

        logger.info("Initializing GameScene")

        self.particle_system = ParticleSystem()

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

                # Store map dimensions directly on the GameScene
                self.map_width = self.map_renderer.width
                self.map_height = self.map_renderer.height
                logger.info(f"Set map dimensions to {self.map_width}x{self.map_height}")

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

        # Set fallback dimensions to screen dimensions
        screen_width = config.get("screen", "width", default=800)
        screen_height = config.get("screen", "height", default=600)

        # Set map dimensions directly on GameScene
        self.map_width = screen_width
        self.map_height = screen_height
        logger.info(f"Set fallback map dimensions to screen size: {screen_width}x{screen_height}")

        # Set player boundaries to screen dimensions as fallback
        if hasattr(self, "player") and self.player:
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

        # Get map dimensions if available, otherwise use screen dimensions
        map_width = getattr(self, "map_width", None) or config.get("screen", "width", default=800)
        map_height = getattr(self, "map_height", None) or config.get(
            "screen", "height", default=600
        )

        # Get margin from config
        margin = config.get("mechanics", "enemy_spawn", "margin", default=30)

        # Choose a random edge (0=top, 1=bottom, 2=left, 3=right)
        edge = random.randint(0, 3)
        if edge == 0:  # Top
            position = (
                random.randint(0, map_width),
                -margin,  # Slightly off-screen at the top
            )
        elif edge == 1:  # Bottom
            position = (
                random.randint(0, map_width),
                map_height + margin,  # Slightly off-screen at the bottom
            )
        elif edge == 2:  # Left
            position = (
                -margin,  # Slightly off-screen at the left
                random.randint(0, map_height),
            )
        else:  # Right
            position = (
                map_width + margin,  # Slightly off-screen at the right
                random.randint(0, map_height),
            )

        # Use the factory function to create an enemy (randomly selects type based on weights)
        enemy = create_enemy(position)

        # Set map dimensions on the enemy for use in its projectile creation
        enemy.map_width = map_width
        enemy.map_height = map_height

        self.enemy_group.add(enemy)
        self.all_sprites.add(enemy)
        self.last_spawn_time = current_time
        logger.debug(
            f"{enemy.enemy_type.capitalize()} enemy spawned at {position} (map: {map_width}x{map_height})"
        )

    def pause_game(self):
        """Pause the game and switch to the pause menu."""
        if not self.paused:
            logger.info("Game paused")
            self.paused = True

            # Stop the game music before switching to pause menu
            self.sound_manager.stop_music()

            # Change state to PAUSED and switch scene
            game_state.change_state(GameState.PAUSED)
            self.switch_to_scene("pause")

    def handle_event(self, event):
        """Handle a single game event."""
        # Check for quit event
        if event.type == pygame.QUIT:
            self.should_exit = True
            return True

        # Check for pause toggle
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if not self.paused:
                self.pause_game()
                return

    def _handle_collisions(self):
        """Check for and handle all collisions."""
        # Projectiles vs Enemies - using optimized collision system
        projectile_hits = self.collision_system.check_projectile_enemy_collisions(
            self.projectile_group, self.enemy_group
        )

        for projectile, enemies in projectile_hits.items():
            # Store projectile position before processing hits (it might get killed)
            projectile_pos = projectile.rect.center

            for enemy in enemies:
                # Calculate the exact collision point - use the intersection of the masks
                # For precision, use the direct position to create particles
                offset_x = enemy.rect.x - projectile.rect.x
                offset_y = enemy.rect.y - projectile.rect.y

                # Create hit particles at the best available impact position
                if hasattr(projectile, "mask") and hasattr(enemy, "mask"):
                    if projectile.mask.overlap(enemy.mask, (offset_x, offset_y)):
                        overlap_pos = projectile.mask.overlap(enemy.mask, (offset_x, offset_y))
                        if overlap_pos:
                            # Convert to world space - this is the exact collision point
                            impact_x = projectile.rect.x + overlap_pos[0]
                            impact_y = projectile.rect.y + overlap_pos[1]
                            self.particle_system.create_particles((impact_x, impact_y), "hit")
                        else:
                            # Fallback to projectile position if no specific overlap is found
                            self.particle_system.create_particles(projectile_pos, "hit")
                    else:
                        # No mask overlap but there was a collision - use projectile position
                        self.particle_system.create_particles(projectile_pos, "hit")
                else:
                    # No masks available - use projectile position
                    self.particle_system.create_particles(projectile_pos, "hit")

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
                # Store position before handling collision (projectile might be killed)
                projectile_pos = projectile.rect.center

                # Create hit particles - use simpler approach for player hits to reduce visual clutter
                self.particle_system.create_particles(projectile_pos, "hit")

                # Use the collision handler function
                if handle_enemy_projectile_player_collision(self.player, projectile):
                    # Play hit sound
                    self.play_sound("player_hit")

                    # Trigger screen shake when player is hit by projectile
                    if self.camera:
                        # Get screen shake settings from config
                        shake_duration = config.get(
                            "effects", "screen_shake", "duration", default=300
                        )
                        shake_intensity = config.get(
                            "effects", "screen_shake", "intensity", default=15
                        )
                        self.camera.start_screen_shake(shake_duration, shake_intensity)
                        logger.debug(
                            f"Screen shake triggered: duration={shake_duration}ms, intensity={shake_intensity}"
                        )

                    logger.debug(f"Player hit by projectile. Health: {self.player.current_health}")

        # Player vs Enemies - using optimized collision system
        if not self.player.invincible:
            enemy_hits = self.collision_system.check_player_enemy_collisions(
                self.player, self.enemy_group
            )

            for enemy in enemy_hits:
                # Use the collision handler function
                if handle_player_enemy_collision(self.player, enemy):
                    # Play sound
                    self.play_sound("player_hit")

                    # Trigger screen shake for direct enemy collision (stronger than projectile hits)
                    if self.camera:
                        # Get screen shake settings from config with higher intensity for direct hits
                        shake_duration = config.get(
                            "effects", "screen_shake", "duration", default=300
                        )
                        shake_intensity = (
                            config.get("effects", "screen_shake", "intensity", default=15) * 1.5
                        )
                        self.camera.start_screen_shake(int(shake_duration), shake_intensity * 1.5)
                        logger.debug(
                            f"Strong screen shake triggered: duration={shake_duration}ms, intensity={shake_intensity*1.5}"
                        )

                    logger.debug(
                        f"Player collided with enemy. Health: {self.player.current_health}"
                    )

        # Player vs Powerups - using optimized collision system
        powerup_hits = self.collision_system.check_player_powerup_collisions(
            self.player, self.powerup_group
        )

        for powerup in powerup_hits:
            if powerup.active:
                # Create powerup collection particles
                self.particle_system.create_particles(powerup.rect.center, "powerup")

                # Play powerup collection sound
                self.play_sound("powerup_collect")

                # Use the collision handler function to apply the powerup effect
                if handle_player_powerup_collision(self.player, powerup):
                    powerup.kill()  # Remove from all sprite groups
                    self.powerups_collected += 1

                    # Update score for collecting a powerup
                    self.score_manager.powerup_collected()

                    logger.info(
                        f"Powerup collected: {powerup.type}. Total collected: {self.powerups_collected}"
                    )

    def handle_enemy_death(self, enemy):
        """Handle an enemy's death, including potential powerup drops."""
        # Store the enemy position before killing it
        enemy_position = enemy.rect.center

        # Kill the enemy (remove from sprite groups)
        enemy.kill()
        self.enemies_killed += 1

        # Update score for killing an enemy
        self.score_manager.enemy_defeated()

        # Create death particles at stored enemy position
        self.particle_system.create_particles(enemy_position, "death")

        logger.debug(f"Enemy {enemy.id} killed. Total killed: {self.enemies_killed}")

        # Check for powerup drops
        if random.random() < 0.25:  # 25% chance
            self.drop_powerup(enemy_position)

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

        # Get number of projectiles before player update
        num_projectiles_before = len(self.projectile_group)

        # Update player
        self.player.update()

        # Check if a new projectile was created by comparing the number of projectiles
        num_projectiles_after = len(self.projectile_group)
        if num_projectiles_after > num_projectiles_before:
            # A new projectile was created, play a shooting sound with a random chance
            if random.random() < 0.3:  # Only play 30% of the time to avoid sound overload
                self.play_sound("player_hit")  # Using player_hit for now since we know it exists

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

        # Update particle effects
        self.particle_system.update()

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

        # We'll remove the sound effect here since it's now handled directly in
        # Player.update when a shot is actually fired

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

        # Update particle system with camera offset to ensure particles are drawn with the camera offset
        if self.camera:
            self.particle_system.set_camera_offset(self.camera.get_offset())

        # Draw particles with camera offset already applied in the particle system
        self.particle_system.draw(self.screen)

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
