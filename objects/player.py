import pygame
import math
from utils import find_closest_enemy, GameLogger
from .projectile import Projectile
from managers import config, game_asset_manager, CurrencyManager
import random

logger = GameLogger.get_logger("player")


class Player(pygame.sprite.Sprite):
    def __init__(self, position=None):
        super().__init__()

        # Get player dimensions from config
        width = config.get("player", "dimensions", "width", default=50)
        height = config.get("player", "dimensions", "height", default=50)

        # Get player color from config
        player_color = config.get("player", "appearance", "color", default="green")

        # Load the character sprite
        self.image = game_asset_manager.get_character_sprite(player_color, width, height)
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)

        # Set initial position
        start_x = config.get("player", "start_position", "x", default=400)
        start_y = config.get("player", "start_position", "y", default=300)
        self.rect.center = position if position else (start_x, start_y)

        # Currency manager for upgrades
        self.currency_manager = CurrencyManager()

        # Player attributes - before upgrades
        self.max_health = config.get("player", "attributes", "max_health", default=100)
        self.current_health = self.max_health
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = config.get(
            "player", "attributes", "invincibility_duration", default=1000
        )

        # Shot cooldown
        config_shot_cooldown = config.get("player", "attributes", "shot_cooldown", default=500)
        logger.info(f"Player initialized with shot cooldown: {config_shot_cooldown}ms")
        self.last_shot_time = 0
        self.shot_cooldown = config_shot_cooldown
        self.base_shot_cooldown = config_shot_cooldown
        logger.debug(f"Base shot cooldown set to: {self.base_shot_cooldown}ms")

        # Weapon boost properties
        self.weapon_boost_active = False
        self.weapon_boost_timer = 0
        self.weapon_boost_duration = 0

        # Speed boost properties
        self.base_movement_speed = config.get("player", "attributes", "movement_speed", default=5)
        self.movement_speed = self.base_movement_speed
        self.speed_boost_active = False
        self.speed_boost_timer = 0
        self.speed_boost_duration = 0
        self.speed_boost_factor = 1.0

        # Damage boost properties
        self.damage_boost_active = False
        self.damage_boost_timer = 0
        self.damage_boost_duration = 0
        self.damage_boost_factor = 1.0

        # Visual effect properties
        self.flash_effect = False
        self.flash_duration = 200
        self.flash_timer = 0
        self.flash_color = None
        self.original_image = self.image.copy()

        # Game references
        self.screen = None
        self.enemy_group = None
        self.projectile_group = None
        self.all_sprites = None
        self.map_width = None
        self.map_height = None

        # Cached config values
        self.shooting_range = config.get("mechanics", "player", "shooting_range", default=250)
        self.projectile_speed = config.get("projectile", "attributes", "speed", default=10)
        self.crit_chance = config.get("player", "attributes", "crit_chance", default=0.05)
        self.crit_multiplier = config.get("player", "attributes", "crit_multiplier", default=2)
        self.base_damage = config.get("projectile", "attributes", "damage", default=10)

        # Apply purchased upgrades
        self.apply_upgrades()

        logger.info(f"Player initialized with {player_color} character sprite")

    def apply_upgrades(self):
        """Apply permanent upgrades from the currency manager to the player."""
        upgrades = self.currency_manager.get_upgrades()
        logger.info(f"Applying player upgrades: {upgrades}")

        # Apply health upgrade
        if "health" in upgrades:
            health_level = upgrades["health"]
            health_per_level = config.get(
                "player", "upgrades", "types", "health", "effect_per_level", default=10
            )
            health_increase = health_level * health_per_level
            self.max_health += health_increase
            self.current_health = self.max_health
            logger.info(f"Applied health upgrade: +{health_increase} health (Level {health_level})")

        # Apply speed upgrade
        if "speed" in upgrades:
            speed_level = upgrades["speed"]
            speed_per_level = config.get(
                "player", "upgrades", "types", "speed", "effect_per_level", default=0.2
            )
            speed_increase = speed_level * speed_per_level
            self.base_movement_speed += speed_increase
            self.movement_speed = self.base_movement_speed
            logger.info(f"Applied speed upgrade: +{speed_increase} speed (Level {speed_level})")

        # Apply fire rate upgrade (reduces cooldown)
        if "fire_rate" in upgrades:
            fire_rate_level = upgrades["fire_rate"]
            cooldown_reduction_per_level = config.get(
                "player", "upgrades", "types", "fire_rate", "effect_per_level", default=0.1
            )
            cooldown_reduction = fire_rate_level * cooldown_reduction_per_level
            # Apply as a percentage reduction (e.g., level 1 = 10% faster)
            reduction_factor = 1.0 - cooldown_reduction
            if reduction_factor < 0.3:  # Cap at 70% reduction to prevent too fast firing
                reduction_factor = 0.3
            self.base_shot_cooldown = (
                config.get("player", "attributes", "shot_cooldown", default=500) * reduction_factor
            )
            self.shot_cooldown = self.base_shot_cooldown
            logger.info(
                f"Applied fire rate upgrade: {int((1-reduction_factor)*100)}% faster (Level {fire_rate_level})"
            )

        # Apply damage upgrade
        if "damage" in upgrades:
            damage_level = upgrades["damage"]
            damage_per_level = config.get(
                "player", "upgrades", "types", "damage", "effect_per_level", default=2
            )
            damage_increase = damage_level * damage_per_level
            self.base_damage += damage_increase
            logger.info(f"Applied damage upgrade: +{damage_increase} damage (Level {damage_level})")

    def apply_visual_effects(self):
        """Apply visual effects like flashing to the player sprite."""
        update_mask = False

        if self.flash_effect:
            current_time = pygame.time.get_ticks()
            if current_time - self.flash_timer > self.flash_duration:
                self.flash_effect = False
                self.image = self.original_image.copy()
                update_mask = True
            else:
                flash_interval = 50
                if (current_time // flash_interval) % 2 == 0:
                    self.image = self.original_image.copy()
                else:
                    overlay = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
                    flash_color_with_alpha = self.flash_color + (150,)
                    overlay.fill(flash_color_with_alpha)
                    temp_image = self.original_image.copy()
                    temp_image.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    self.image = temp_image
                update_mask = True

        elif self.invincible:
            current_time = pygame.time.get_ticks()
            if (current_time // 100) % 2 == 0:
                self.image.set_alpha(100)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

        if update_mask:
            self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        """Update player state including movement, shooting, and effects."""
        keys = pygame.key.get_pressed()
        moving = False
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.movement_speed
            moving = True
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.movement_speed
            moving = True
        if keys[pygame.K_UP]:
            self.rect.y -= self.movement_speed
            moving = True
        if keys[pygame.K_DOWN]:
            self.rect.y += self.movement_speed
            moving = True

        if self.map_width and self.map_height:
            self.rect.clamp_ip((0, 0, self.map_width, self.map_height))

        current_time = pygame.time.get_ticks()
        time_since_last_shot = current_time - self.last_shot_time

        if self.shot_cooldown < 100:
            logger.warning(f"Shot cooldown too low: {self.shot_cooldown}ms, resetting")
            self.shot_cooldown = self.base_shot_cooldown

        if moving and time_since_last_shot >= self.shot_cooldown:
            projectile = self.shoot()
            if projectile:
                logger.debug(f"Projectile created with ID: {projectile.id}")
                logger.debug(f"Projectile velocity: {projectile.velocity}")
                self.projectile_group.add(projectile)
                self.all_sprites.add(projectile)
                self.last_shot_time = current_time
                logger.debug(
                    f"Shot cooldown: {self.shot_cooldown}ms, next shot at: {current_time + self.shot_cooldown}"
                )

        if self.invincible:
            if current_time - self.invincible_timer > self.invincible_duration:
                self.invincible = False
                logger.debug("Player invincibility ended")

        if self.speed_boost_active:
            if current_time - self.speed_boost_timer > self.speed_boost_duration:
                self.deactivate_speed_boost()

        if self.damage_boost_active:
            if current_time - self.damage_boost_timer > self.damage_boost_duration:
                self.deactivate_damage_boost()

        if self.weapon_boost_active:
            if current_time - self.weapon_boost_timer > self.weapon_boost_duration:
                self.deactivate_weapon_boost()

        self.apply_visual_effects()

    def shoot(self):
        current_time = pygame.time.get_ticks()
        time_since_last_shot = current_time - self.last_shot_time
        if time_since_last_shot < self.shot_cooldown:
            return None

        if self.enemy_group:
            closest_enemy = find_closest_enemy(self.rect.center, self.enemy_group)
            if closest_enemy:
                dx = closest_enemy.rect.centerx - self.rect.centerx
                dy = closest_enemy.rect.centery - self.rect.centery
                distance = math.sqrt(dx**2 + dy**2)

                if distance <= self.shooting_range:
                    velocity = (
                        dx / distance * self.projectile_speed,
                        dy / distance * self.projectile_speed,
                    )
                    is_crit = random.random() < self.crit_chance
                    damage_multiplier = self.crit_multiplier if is_crit else 1
                    base_damage = self.base_damage * self.damage_boost_factor
                    damage = base_damage * damage_multiplier

                    projectile = Projectile(
                        self.rect.center,
                        velocity,
                        damage=damage,
                        map_width=self.map_width,
                        map_height=self.map_height,
                        is_crit=is_crit,
                    )

                    if is_crit:
                        logger.info(f"Critical hit! Damage increased to {damage}")
                    self.last_shot_time = current_time
                    return projectile
        return None

    def take_damage(self, amount):
        """Handle player taking damage."""
        if not self.invincible:
            self.current_health -= amount
            self.invincible = True
            self.invincible_timer = pygame.time.get_ticks()
            logger.info(
                f"Player took {amount} damage. Health: {self.current_health}/{self.max_health}"
            )
            self.start_flash_effect((255, 0, 0))
            if self.current_health <= 0:
                logger.warning("Player died!")
                return True
        return False

    def start_flash_effect(self, color):
        """Start a flash effect with the given color."""
        self.flash_effect = True
        self.flash_timer = pygame.time.get_ticks()
        self.flash_color = color
        logger.debug(f"Started flash effect with color {color}")

    def activate_speed_boost(self, boost_factor, duration):
        """Activate the speed boost power-up."""
        self.speed_boost_active = True
        self.speed_boost_timer = pygame.time.get_ticks()
        self.speed_boost_duration = duration
        self.speed_boost_factor = boost_factor
        self.movement_speed = self.base_movement_speed * boost_factor
        logger.debug(f"Speed boost activated: {boost_factor}x for {duration}ms")
        self.start_flash_effect(config.get_color("yellow"))

    def deactivate_speed_boost(self):
        """Deactivate the speed boost effect."""
        self.speed_boost_active = False
        self.movement_speed = self.base_movement_speed
        logger.debug("Speed boost deactivated")

    def activate_damage_boost(self, boost_factor, duration):
        """Activate the damage boost power-up."""
        self.damage_boost_active = True
        self.damage_boost_timer = pygame.time.get_ticks()
        self.damage_boost_duration = duration
        self.damage_boost_factor = boost_factor
        logger.debug(f"Damage boost activated: {boost_factor}x for {duration}ms")
        self.start_flash_effect(config.get_color("magenta"))

    def deactivate_damage_boost(self):
        """Deactivate the damage boost effect."""
        self.damage_boost_active = False
        self.damage_boost_factor = 1.0
        logger.debug("Damage boost deactivated")

    def activate_weapon_boost(
        self,
        boost_factor=2.0,
        duration=config.get("powerups", "weapon_boost", "duration", default=5000),
    ):
        """Activate the weapon boost power-up, reducing shot cooldown."""
        self.weapon_boost_active = True
        self.weapon_boost_timer = pygame.time.get_ticks()
        self.weapon_boost_duration = duration
        self.shot_cooldown = self.base_shot_cooldown / boost_factor
        logger.debug(f"Weapon boost activated: fire rate x{boost_factor} for {duration}ms")
        self.start_flash_effect(config.get_color("yellow"))

    def deactivate_weapon_boost(self):
        """Deactivate the weapon boost effect."""
        self.weapon_boost_active = False
        self.shot_cooldown = self.base_shot_cooldown
        logger.debug(f"Weapon boost deactivated. Cooldown restored to {self.shot_cooldown}ms")
