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

logger = GameLogger.get_logger("game_scene")


class GameScene(Scene):
    """Main gameplay scene managing game objects, rendering, and state."""

    def __init__(self):
        super().__init__()
        logger.info("Initializing GameScene")
        self.particle_system = ParticleSystem()
        self._initialize_game()
        self.play_scene_music("game")

    def _initialize_game(self):
        """Set up or reset game objects and state."""
        # Initialize sprite groups and player
        self.player = Player()
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

    def spawn_enemy(self):
        """Spawn an enemy at a random map edge."""
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

        enemy = create_enemy(position)
        enemy.map_width = map_width
        enemy.map_height = map_height
        self.enemy_group.add(enemy)
        self.all_sprites.add(enemy)
        self.last_spawn_time = current_time
        logger.debug(f"{enemy.enemy_type.capitalize()} enemy spawned at {position}")

    def pause_game(self):
        """Pause the game and switch to pause scene."""
        if game_state.current_state == GameState.PLAYING:
            game_state.change_state(GameState.PAUSED)
            self.switch_to_scene("pause")

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
        powerup_type = random.choice(["health", "shield", "weapon"])
        powerup = Powerup(position, powerup_type)
        self.powerup_group.add(powerup)
        self.all_sprites.add(powerup)
        logger.debug(f"Dropped {powerup_type} powerup at {position}")

    def update(self):
        """Update game state each frame."""
        if self.paused:
            return

        current_time = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()

        # Spawn enemies
        enemy_spawn_interval = config.get("gameplay", "enemy_spawn_interval", default=1500)
        if current_time - self.last_spawn_time > enemy_spawn_interval:
            self.spawn_enemy()

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
                    self.player.rect.center, current_time, self.projectile_group, self.all_sprites
                )
            else:
                enemy.update(self.player.rect.center, current_time)
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
            game_over.final_score = self.score_manager.current_score
            game_over.high_score = self.score_manager.high_score
            game_over.enemies_killed = self.enemies_killed
            game_over.powerups_collected = self.powerups_collected
            game_over.time_survived = self.time_survived
            self.switch_to_scene("game_over")

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

    def _render_ui(self):
        """Draw UI elements like health bar and stats."""
        health_bar_width = config.get("ui", "health_bar_width", default=200)
        health_bar_height = config.get("ui", "health_bar_height", default=20)
        health_ratio = self.player.current_health / self.player.max_health
        pygame.draw.rect(self.screen, (255, 0, 0), (10, 10, health_bar_width, health_bar_height))
        pygame.draw.rect(
            self.screen, (0, 255, 0), (10, 10, health_bar_width * health_ratio, health_bar_height)
        )

        ui_font = self.small_font if hasattr(self, "small_font") else self.font
        screen_width = config.get("screen", "width", default=800)
        right_margin = 140
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
        self.draw_text(
            f"Score: {self.score_manager.get_formatted_score()}",
            (255, 255, 0),
            screen_width // 2,
            20,
        )
        self.draw_text(
            f"High: {self.score_manager.get_formatted_high_score()}",
            (255, 165, 0),
            screen_width // 2,
            50,
        )
