import pygame
import random
import math
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
from managers.wave_manager import WaveManager
from utils.logger import GameLogger

logger = GameLogger.get_logger("game_scene")


class GameScene(Scene):
    """Main gameplay scene managing game objects, rendering, and state."""

    def __init__(self):
        super().__init__()
        logger.info("Initializing GameScene")
        self._initialize_game()
        self.play_scene_music("game")

    def _initialize_game(self):
        """Set up or reset game objects and state."""
        # Initialize sprite groups and player
        self.player = Player()
        self.particle_system = ParticleSystem()
        self.all_sprites = pygame.sprite.Group(self.player)
        self.enemy_group = pygame.sprite.Group()
        self.projectile_group = pygame.sprite.Group()
        self.powerup_group = pygame.sprite.Group()

        # Configure player references
        self.player.screen = self.screen
        self.player.all_sprites = self.all_sprites
        self.player.enemy_group = self.enemy_group
        self.player.projectile_group = self.projectile_group

        # Timing and state variables
        self.last_spawn_time = pygame.time.get_ticks()
        self.paused = False
        self.score_manager = ScoreManager()
        self.last_time_score_update = pygame.time.get_ticks()
        self.enemies_killed = 0
        self.time_survived = 0
        self.start_time = pygame.time.get_ticks()
        self.powerups_collected = 0

        # Spawn rate scaling variables
        self.base_spawn_interval = config.get("mechanics", "enemy_spawn", "interval", default=1000)
        self.min_spawn_interval = config.get(
            "mechanics", "enemy_spawn", "min_interval", default=250
        )  # Fastest spawn rate
        self.spawn_rate_increase_factor = config.get(
            "mechanics", "enemy_spawn", "scaling_factor", default=0.85
        )  # How quickly spawn rate increases
        self.spawn_rate_increase_interval = config.get(
            "mechanics", "enemy_spawn", "scaling_interval", default=30000
        )  # Time in ms between difficulty increases
        self.last_spawn_rate_increase = pygame.time.get_ticks()
        self.current_spawn_interval = self.base_spawn_interval
        self.difficulty_level = 1

        # Collision system setup
        screen_width = config.get("screen", "width", default=800)
        screen_height = config.get("screen", "height", default=600)
        self.collision_system = CollisionSystem(
            screen_width=screen_width,
            screen_height=screen_height,
            algorithm=CollisionSystem.SPATIAL_HASH,
            cell_size=64,
        )

        # Load map and set initial state
        self._load_map()
        game_state.change_state(GameState.PLAYING)
        logger.info("Game state initialized")

        # Initialize the wave manager
        self.wave_manager = WaveManager(self)
        self.wave_in_progress = False
        self.wave_transition_timer = 0
        self.wave_transition_duration = config.get(
            "waves", "transition_duration", default=3000
        )  # 3 seconds
        self.wave_transition_text = "Prepare for the next wave!"
        self.is_boss_wave = False

        # UI Config elements
        self.health_bar_width = config.get("ui", "health_bar_width", default=200)
        self.health_bar_height = config.get("ui", "health_bar_height", default=20)
        self.health_bar_background = config.get(
            "ui", "health_bar", "background_color", default=(80, 80, 80)
        )
        self.health_bar_foreground = config.get(
            "ui", "health_bar", "fill_color", default=(255, 0, 0)
        )
        self.health_bar_border = config.get("ui", "health_bar", "border_color", default=(0, 0, 0))

    def _load_map(self):
        """Load tiled map and configure camera, with fallback if loading fails."""
        logger.info("Loading tiled map")
        try:
            tiled_map = game_asset_manager.load_tiled_map("Tiled/sampleMap.tmx")
            if tiled_map:
                self.map_renderer = TiledMapRenderer(tiled_map)
                screen_width = config.get("screen", "width", default=800)
                screen_height = config.get("screen", "height", default=600)
                self.camera = Camera(
                    self.map_renderer.width, self.map_renderer.height, screen_width, screen_height
                )
                self.map_width = self.map_renderer.width
                self.map_height = self.map_renderer.height
                self.player.map_width = self.map_width
                self.player.map_height = self.map_height
                logger.info(f"Map loaded: {self.map_width}x{self.map_height}")
            else:
                raise ValueError("Tiled map not found")
        except Exception as e:
            logger.warning(f"Map loading failed: {e}. Using fallback background")
            self._setup_fallback_background()

    def _setup_fallback_background(self):
        """Configure fallback background when map loading fails."""
        self.map_renderer = None
        self.camera = None
        self.map_width = config.get("screen", "width", default=800)
        self.map_height = config.get("screen", "height", default=600)
        self.player.map_width = self.map_width
        self.player.map_height = self.map_height
        logger.info(f"Fallback background set: {self.map_width}x{self.map_height}")

    def reset(self):
        """Reset game state and restart music."""
        logger.info("Resetting GameScene")
        self._initialize_game()
        self.play_scene_music("game")

    def pause_game(self):
        """Pause the game and switch to pause scene."""
        if game_state.current_state == GameState.PLAYING:
            game_state.change_state(GameState.PAUSED)
            self.switch_to_scene("pause")

    def spawn_enemy(self, enemy_type="basic", attr_multipliers=None):
        """
        Spawn an enemy of the specified type with attribute multipliers.

        Args:
            enemy_type: Type of enemy to spawn ('basic', 'ranged', 'charger')
            attr_multipliers: Dictionary of attribute multipliers (health, damage, speed)
        """
        current_time = pygame.time.get_ticks()
        map_width = self.map_width
        map_height = self.map_height
        margin = config.get("mechanics", "enemy_spawn", "margin", default=30)

        edge = random.randint(0, 3)
        if edge == 0:  # Top
            position = (random.randint(0, map_width), -margin)
        elif edge == 1:  # Bottom
            position = (random.randint(0, map_width), map_height + margin)
        elif edge == 2:  # Left
            position = (-margin, random.randint(0, map_height))
        else:  # Right
            position = (map_width + margin, random.randint(0, map_height))

        # Create the enemy with the specified type and attribute multipliers
        enemy = create_enemy(position, enemy_type, attr_multipliers)
        enemy.map_width = map_width
        enemy.map_height = map_height
        self.enemy_group.add(enemy)
        self.all_sprites.add(enemy)
        self.last_spawn_time = current_time
        logger.debug(
            f"{enemy.enemy_type.capitalize()} enemy spawned at {position} with multipliers: {attr_multipliers}"
        )

        # Add points for spawning an enemy (for testing)
        self.score_manager.add_score(1)

    def spawn_boss(self, attr_multipliers=None):
        current_time = pygame.time.get_ticks()
        map_width = self.map_width
        map_height = self.map_height

        # Spawn boss at the center of the top edge
        position = (map_width // 2, -50)

        # Create a boss enemy (e.g., a stronger charger)
        enemy = create_enemy(position, "charger", attr_multipliers)
        enemy.map_width = map_width
        enemy.map_height = map_height

        # Define scale factor for the boss
        scale_factor = 2

        # Scale both original_image and image to maintain size consistently
        if hasattr(enemy, "original_image"):
            original_size = enemy.original_image.get_size()
            new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
            enemy.original_image = pygame.transform.scale(enemy.original_image, new_size)
            enemy.image = enemy.original_image.copy()  # Update current image to scaled version

        # Update rect to match the scaled image
        enemy.rect = enemy.image.get_rect(center=enemy.rect.center)

        # Add enemy to groups
        self.enemy_group.add(enemy)
        self.all_sprites.add(enemy)
        self.last_spawn_time = current_time

        logger.info(f"Boss spawned at {position} with multipliers: {attr_multipliers}")
        self.score_manager.add_score(50)
        self.play_sound("boss_encounter")

    def update(self):
        """Update game state each frame."""
        if self.paused:
            return

        current_time = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()

        # Update difficulty based on time played
        self._update_difficulty(current_time)

        # Handle wave management
        if not self.wave_in_progress and not self.wave_transition_timer:
            # Start first wave or next wave, but only if no enemies remain
            if len(self.enemy_group) == 0:
                self.wave_transition_timer = current_time
                self.wave_transition_text = (
                    "Get Ready!"
                    if self.wave_manager.current_wave == 0
                    else f"Wave {self.wave_manager.current_wave} complete! Prepare for the next wave!"
                )

        # Handle wave transitions
        if (
            self.wave_transition_timer
            and current_time - self.wave_transition_timer >= self.wave_transition_duration
        ):
            self.wave_transition_timer = 0
            self.is_boss_wave = self.wave_manager.start_next_wave()
            self.wave_in_progress = True

            # Play wave start sound
            if self.is_boss_wave:
                self.play_sound("boss_wave_start")
            else:
                self.play_sound("wave_start")

        # Update wave manager if a wave is in progress
        if self.wave_in_progress:
            self.wave_manager.update(current_time)

            # Check if wave is complete
            if not self.wave_manager.wave_in_progress and len(self.enemy_group) == 0:
                self.wave_in_progress = False
                # Add wave completion bonus
                self.score_manager.add_score(self.wave_manager.current_wave * 100)
                # Play wave complete sound
                self.play_sound("wave_complete")

        # Update game objects
        num_projectiles = len(self.projectile_group)
        self.player.update()
        if len(self.projectile_group) > num_projectiles and random.random() < 0.3:
            self.play_sound("player_hit")

        if self.camera:
            self.camera.update(self.player)
        for enemy in self.enemy_group:
            if hasattr(enemy, "enemy_type") and enemy.enemy_type == Enemy.TYPE_RANGED:
                enemy.update(
                    self.player.rect.center,
                    current_time,
                    self.projectile_group,
                    self.all_sprites,
                    self.enemy_group,
                )
            else:
                enemy.update(self.player.rect.center, current_time, None, None, self.enemy_group)
        self.projectile_group.update()
        self.powerup_group.update()
        self.particle_system.update()

        # Collision and cleanup
        self.collision_system.update(
            self.projectile_group, self.enemy_group, self.player, self.powerup_group
        )
        self._handle_collisions()
        for enemy in self.enemy_group.copy():
            if not enemy.alive():
                self.handle_enemy_death(enemy)

        # Update scoring and time
        self.time_survived = (current_time - self.start_time) // 1000
        if current_time - self.last_time_score_update >= 5000:
            seconds = (current_time - self.last_time_score_update) // 1000
            self.score_manager.add_time_survived_points(seconds)
            self.last_time_score_update = current_time

        # Check game over
        if self.player.current_health <= 0:
            self.score_manager.save_high_score()
            game_state.change_state(GameState.GAME_OVER)
            game_over = self.scene_manager.scenes["game_over"]
            self.play_sound("game_lost")
            game_over.final_score = self.score_manager.current_score
            game_over.high_score = self.score_manager.high_score
            game_over.enemies_killed = self.enemies_killed
            game_over.powerups_collected = self.powerups_collected
            game_over.time_survived = self.time_survived
            self.switch_to_scene("game_over")

    def _update_difficulty(self, current_time):
        """Update game difficulty based on time played."""
        # Check if it's time to increase difficulty
        if current_time - self.last_spawn_rate_increase > self.spawn_rate_increase_interval:
            # Increase difficulty level
            self.difficulty_level += 1

            # Calculate new spawn interval with exponential decrease over time
            self.current_spawn_interval = max(
                self.min_spawn_interval,
                self.base_spawn_interval
                * (self.spawn_rate_increase_factor ** (self.difficulty_level - 1)),
            )

            # Log the difficulty increase
            logger.info(
                f"Difficulty increased to level {self.difficulty_level}. New spawn interval: {self.current_spawn_interval}ms"
            )

            # Reset timer for next difficulty increase
            self.last_spawn_rate_increase = current_time

            # Optional: Show difficulty increase to player
            self.particle_system.create_particles(self.player.rect.center, "powerup")
            self.play_sound("powerup_collect")  # Reuse existing sound for now

    def _render_ui(self):
        """Draw UI elements like health bar, score, and wave information."""
        # Get display dimensions
        display_width, display_height = self.screen.get_size()

        # --- Health Bar ---
        health_bar_width = self.health_bar_width
        health_bar_height = self.health_bar_height
        health_ratio = self.player.current_health / self.player.max_health
        # Background
        pygame.draw.rect(
            self.screen, self.health_bar_background, (10, 10, health_bar_width, health_bar_height)
        )
        # Foreground (health)
        pygame.draw.rect(
            self.screen,
            self.health_bar_foreground,
            (10, 10, int(health_bar_width * health_ratio), health_bar_height),
        )
        # Border
        pygame.draw.rect(
            self.screen, self.health_bar_border, (10, 10, health_bar_width, health_bar_height), 2
        )

        # Health text
        health_text = f"Health: {int(self.player.current_health)}/{self.player.max_health}"
        self.draw_text(
            health_text,
            24,
            (255, 255, 255),
            10 + health_bar_width + 10,
            10 + health_bar_height // 2,
        )

        # --- Score ---
        score_text = f"Score: {self.score_manager.current_score}"
        self.draw_text(score_text, 24, (255, 255, 255), display_width - 10, 10, align="right")

        # --- Wave Information ---
        self._render_wave_info()

        # Wave transition message
        if self.wave_transition_timer:
            # Calculate fade-in/fade-out alpha
            elapsed = pygame.time.get_ticks() - self.wave_transition_timer
            if elapsed < self.wave_transition_duration / 2:
                # Fade in
                alpha = int(255 * (elapsed / (self.wave_transition_duration / 2)))
            else:
                # Fade out
                alpha = int(
                    255
                    * (
                        1
                        - (elapsed - self.wave_transition_duration / 2)
                        / (self.wave_transition_duration / 2)
                    )
                )

            # Render wave transition text with pulsating size
            pulse = 1.0 + 0.1 * abs(math.sin(elapsed / 200))  # Subtle pulse
            size = int(36 * pulse)

            # Draw with shadow for better visibility
            self.draw_text(
                self.wave_transition_text,
                size,
                (0, 0, 0),
                display_width // 2 + 2,
                display_height // 2 + 2,
                align="center",
                alpha=alpha,
            )
            self.draw_text(
                self.wave_transition_text,
                size,
                (255, 255, 0),
                display_width // 2,
                display_height // 2,
                align="center",
                alpha=alpha,
            )

            # Draw wave number if not the first wave
            if self.wave_manager.current_wave > 0:
                next_wave = self.wave_manager.current_wave + 1
                if next_wave % self.wave_manager.boss_wave_frequency == 0:
                    next_wave_text = f"BOSS WAVE {next_wave} INCOMING!"
                    color = (255, 50, 50)
                else:
                    next_wave_text = f"Wave {next_wave}"
                    color = (200, 255, 200)

                self.draw_text(
                    next_wave_text,
                    28,
                    color,
                    display_width // 2,
                    display_height // 2 + 50,
                    align="center",
                    alpha=alpha,
                )

    def _render_wave_info(self):
        """Render wave information UI elements including wave number and enemies remaining."""
        # Get display dimensions
        display_width, display_height = self.screen.get_size()

        # Wave status
        if self.wave_manager.current_wave > 0:
            # Wave number and enemies remaining
            if self.is_boss_wave:
                wave_text = f"BOSS WAVE {self.wave_manager.current_wave}"
                text_color = (255, 100, 100)  # Red for boss waves
            else:
                wave_text = f"Wave {self.wave_manager.current_wave}"
                text_color = (255, 255, 255)  # White for normal waves

            self.draw_text(wave_text, 28, text_color, display_width // 2, 15, align="center")

            # Enemies remaining
            if self.wave_in_progress:
                enemies_text = f"Enemies: {self.wave_manager.enemies_remaining}"
                self.draw_text(
                    enemies_text, 20, (200, 200, 200), display_width // 2, 45, align="center"
                )

    def draw_text(self, text, size, color, x, y, align="left", alpha=255):
        """
        Draw text on the screen with the specified parameters.

        Args:
            text: The text to display
            size: Font size
            color: RGB color tuple
            x, y: Position coordinates
            align: Text alignment ('left', 'center', 'right')
            alpha: Transparency (0-255)
        """
        font = pygame.font.Font(None, size)
        text_surface = font.render(text, True, color)

        # Apply alpha if needed
        if alpha < 255:
            text_surface.set_alpha(alpha)

        text_rect = text_surface.get_rect()
        if align == "center":
            text_rect.center = (x, y)
        elif align == "right":
            text_rect.right = x
            text_rect.centery = y
        else:  # left align
            text_rect.left = x
            text_rect.centery = y

        self.screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        """Process game events like quitting or pausing."""
        if event.type == pygame.QUIT:
            self.should_exit = True
            self.score_manager.save_high_score()
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not self.paused:
            self.pause_game()
            return True
        return False

    def switch_to_scene(self, scene_name):
        """Switch scenes, cleaning up only if not pausing/options."""
        if scene_name not in ["pause", "options"]:
            logger.info(f"Switching to {scene_name}, saving high score")
            self.score_manager.save_high_score()
            self.cleanup()
        super().switch_to_scene(scene_name)

    def cleanup(self):
        """Release resources when leaving the scene."""
        logger.info("Cleaning up GameScene resources")

        # Clear references to tiledmap and renderer
        self.map_renderer = None

        # Clear sprite groups to prevent memory leaks
        for group in [
            self.all_sprites,
            self.enemy_group,
            self.projectile_group,
            self.powerup_group,
        ]:
            if group:  # Simply check if the group exists
                group.empty()

        # Reset camera
        if self.camera:
            self.camera.reset()
        self.sound_manager.stop_music()

    def resume_from_pause(self):
        """Resume game from pause state."""
        self.paused = False
        game_state.change_state(GameState.PLAYING)
        self.play_scene_music("game")
        logger.info("Game resumed")

    def _handle_collisions(self):
        """Manage all collision interactions."""
        # Projectiles vs Enemies
        projectile_hits = self.collision_system.check_projectile_enemy_collisions(
            self.projectile_group, self.enemy_group
        )
        for projectile, enemies in projectile_hits.items():
            pos = projectile.rect.center
            for enemy in enemies:
                self.particle_system.create_particles(pos, "hit")
                if handle_projectile_enemy_collision(projectile, enemy):
                    self.play_sound("enemy_hit")
                    self.handle_enemy_death(enemy)

        # Enemy Projectiles vs Player
        if not self.player.invincible:
            projectile_hits = self.collision_system.check_enemy_projectile_player_collision(
                self.player, self.projectile_group
            )
            for projectile in projectile_hits:
                self.particle_system.create_particles(projectile.rect.center, "hit")
                if handle_enemy_projectile_player_collision(self.player, projectile):
                    self.play_sound("player_hit")
                    if self.camera:
                        self.camera.start_screen_shake(
                            config.get("effects", "screen_shake", "duration", default=300),
                            config.get("effects", "screen_shake", "intensity", default=15),
                        )

        # Player vs Enemies
        if not self.player.invincible:
            enemy_hits = self.collision_system.check_player_enemy_collisions(
                self.player, self.enemy_group
            )
            for enemy in enemy_hits:
                if handle_player_enemy_collision(self.player, enemy):
                    self.play_sound("player_hit")
                    if self.camera:
                        self.camera.start_screen_shake(
                            config.get("effects", "screen_shake", "duration", default=300),
                            config.get("effects", "screen_shake", "intensity", default=15) * 1.5,
                        )

        # Player vs Powerups
        powerup_hits = self.collision_system.check_player_powerup_collisions(
            self.player, self.powerup_group
        )
        for powerup in powerup_hits:
            if powerup.active:
                self.particle_system.create_particles(powerup.rect.center, "powerup")
                self.play_sound("powerup_collect")
                if handle_player_powerup_collision(self.player, powerup):
                    powerup.kill()
                    self.powerups_collected += 1
                    self.score_manager.powerup_collected()

    def handle_enemy_death(self, enemy):
        """Process enemy death and potential powerup drop."""
        pos = enemy.rect.center
        enemy.kill()
        self.enemies_killed += 1
        self.score_manager.enemy_defeated()
        self.particle_system.create_particles(pos, "death")
        if random.random() < 0.25:
            self.drop_powerup(pos)

    def drop_powerup(self, position):
        """Spawn a random powerup at the given position."""
        powerup_type = random.choice(["health", "shield", "weapon", "speed", "damage"])
        powerup = Powerup(position, powerup_type)
        self.powerup_group.add(powerup)
        self.all_sprites.add(powerup)
        logger.debug(f"Dropped {powerup_type} powerup at {position}")

    def render(self):
        """Render all game elements to the screen."""
        self.screen.fill(pygame.Color(config.get("screen", "background_color", default="#222222")))
        if self.map_renderer and self.camera:
            self.map_renderer.render(self.screen, self.camera)
        (
            self.all_sprites.draw(self.screen)
            if not self.camera
            else [
                self.screen.blit(sprite.image, self.camera.apply(sprite))
                for sprite in self.all_sprites
            ]
        )
        if self.camera:
            self.particle_system.set_camera_offset(self.camera.get_offset())
        self.particle_system.draw(self.screen)
        self._render_ui()
