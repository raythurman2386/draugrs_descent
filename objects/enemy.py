import pygame
import math
import random
from managers import config, game_asset_manager
from utils.logger import GameLogger
from objects.projectile import Projectile

# Get a logger for the enemy module
logger = GameLogger.get_logger("enemy")


class Enemy(pygame.sprite.Sprite):
    # Counter for unique enemy IDs
    next_id = 1

    # Enemy type constants
    TYPE_BASIC = "basic"
    TYPE_RANGED = "ranged"
    TYPE_CHARGER = "charger"

    def __init__(self, position, enemy_type=TYPE_BASIC):
        super().__init__()
        # Assign a unique ID to each enemy
        self.id = Enemy.next_id
        Enemy.next_id += 1

        # Store enemy type
        self.enemy_type = enemy_type

        # Cache dimensions from config
        self.width = config.get("enemy", "dimensions", "width", default=30)
        self.height = config.get("enemy", "dimensions", "height", default=30)

        # Map enemy types to colors
        color_map = {
            self.TYPE_BASIC: config.get("enemy", "appearance", "basic", "color", default="purple"),
            self.TYPE_RANGED: config.get("enemy", "appearance", "ranged", "color", default="red"),
            self.TYPE_CHARGER: config.get(
                "enemy", "appearance", "charger", "color", default="yellow"
            ),
        }
        self.color = color_map.get(enemy_type, "purple")

        # Load character sprite
        self.image = game_asset_manager.get_character_sprite(self.color, self.width, self.height)
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)

        # Set initial position
        self.rect.x = position[0]
        self.rect.y = position[1]
        self.position = [float(position[0]), float(position[1])]

        # Cache enemy attributes from config
        self.max_health = config.get("enemy", "attributes", "max_health", default=30)
        self.health = self.max_health
        self.damage = config.get("enemy", "attributes", "damage", default=10)
        self.speed = config.get("enemy", "attributes", "speed", default=5)
        self.collision_cooldown = config.get(
            "enemy", "attributes", "collision_cooldown", default=1000
        )
        self.last_collision_time = 0

        # Separation settings for preventing bunching
        self.separation_radius = config.get("enemy", "behavior", "separation_radius", default=60)
        self.separation_weight = config.get("enemy", "behavior", "separation_weight", default=1.0)
        self.target_approach_weight = config.get(
            "enemy", "behavior", "target_approach_weight", default=1.0
        )

        # Add a slight randomness to movement to prevent perfect alignment
        self.position_jitter = config.get("enemy", "behavior", "position_jitter", default=0.3)

        # Store original image for effects
        self.original_image = self.image.copy()

        # Flash effect properties
        self.flash_effect = False
        self.flash_timer = 0
        self.flash_duration = config.get("enemy", "effects", "flash_duration", default=200)
        self.flash_color = (255, 0, 0)  # Red by default

        logger.debug(f"Enemy {self.id} of type {self.enemy_type} created at {position}")

    def can_collide(self, current_time: int) -> bool:
        """Check if the enemy can collide based on cooldown."""
        if current_time - self.last_collision_time > self.collision_cooldown:
            self.last_collision_time = current_time
            return True
        return False

    def move_towards(self, target_position: tuple[float, float], nearby_enemies=None) -> float:
        """Move the enemy towards the target position while avoiding other enemies.

        Args:
            target_position: Position to move towards
            nearby_enemies: List of nearby enemies to avoid

        Returns:
            Distance to target
        """
        # Calculate direction to target
        dx = target_position[0] - self.position[0]
        dy = target_position[1] - self.position[1]
        distance = math.sqrt(dx**2 + dy**2)

        if distance > 0:
            # Normalize direction vector
            dx = dx / distance
            dy = dy / distance

            # Add separation behavior if we have nearby enemies
            separation_dx, separation_dy = 0, 0

            if nearby_enemies:
                for enemy in nearby_enemies:
                    if enemy.id != self.id:  # Don't avoid self
                        # Calculate vector from other enemy to this enemy
                        sep_dx = self.position[0] - enemy.position[0]
                        sep_dy = self.position[1] - enemy.position[1]
                        sep_dist = math.sqrt(sep_dx**2 + sep_dy**2)

                        # Only apply separation if within radius
                        if 0 < sep_dist < self.separation_radius:
                            # The closer they are, the stronger the separation
                            separation_factor = 1.0 - (sep_dist / self.separation_radius)

                            # Normalize and weight by how close they are
                            if sep_dist > 0:  # Avoid division by zero
                                separation_dx += (sep_dx / sep_dist) * separation_factor
                                separation_dy += (sep_dy / sep_dist) * separation_factor

            # Normalize separation vector if it's not zero
            sep_magnitude = math.sqrt(separation_dx**2 + separation_dy**2)
            if sep_magnitude > 0:
                separation_dx /= sep_magnitude
                separation_dy /= sep_magnitude

            # Combine approach and separation vectors with weights
            combined_dx = (dx * self.target_approach_weight) + (
                separation_dx * self.separation_weight
            )
            combined_dy = (dy * self.target_approach_weight) + (
                separation_dy * self.separation_weight
            )

            # Normalize the combined vector
            combined_magnitude = math.sqrt(combined_dx**2 + combined_dy**2)
            if combined_magnitude > 0:
                combined_dx /= combined_magnitude
                combined_dy /= combined_magnitude

            # Add small random variation to prevent perfect alignment
            combined_dx += (random.random() * 2 - 1) * self.position_jitter
            combined_dy += (random.random() * 2 - 1) * self.position_jitter

            # Apply speed
            self.position[0] += combined_dx * self.speed
            self.position[1] += combined_dy * self.speed

            # Update rect position
            self.rect.x = round(self.position[0])
            self.rect.y = round(self.position[1])

        return distance

    def update(
        self,
        player_position=None,
        current_time=None,
        projectile_group=None,
        all_sprites=None,
        enemy_group=None,
    ):
        """Update enemy state."""
        if player_position:
            self.move_towards(player_position, enemy_group)
        self.apply_visual_effects()

    def apply_visual_effects(self):
        """Apply visual effects like flashing to the sprite."""
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
        if update_mask:
            self.mask = pygame.mask.from_surface(self.image)

    def start_flash_effect(self, color: tuple[int, int, int]):
        """Start a flash effect with the given color."""
        self.flash_effect = True
        self.flash_timer = pygame.time.get_ticks()
        self.flash_color = color
        logger.debug(f"Enemy {self.id} started flash effect with color {color}")

    def flash_red(self):
        """Trigger a red flash effect (legacy method)."""
        self.start_flash_effect((255, 0, 0))

    def take_damage(self, amount: int) -> bool:
        """Apply damage and return True if enemy dies."""
        self.health -= amount
        logger.debug(
            f"Enemy {self.id} took {amount} damage. Health: {self.health}/{self.max_health}"
        )
        self.flash_red()
        if self.health <= 0:
            self.kill()
            logger.debug(f"Enemy {self.id} died")
            return True
        return False


class RangedEnemy(Enemy):
    """Enemy that maintains distance and shoots projectiles."""

    def __init__(self, position):
        super().__init__(position, Enemy.TYPE_RANGED)
        # Cache ranged-specific attributes
        self.preferred_distance = config.get("enemy", "ranged", "preferred_distance", default=200)
        self.attack_cooldown = config.get("enemy", "ranged", "attack_cooldown", default=2000)
        self.projectile_speed = config.get("enemy", "ranged", "projectile_speed", default=3)
        self.projectile_damage = config.get("enemy", "ranged", "projectile_damage", default=5)
        self.speed = config.get("enemy", "ranged", "speed", default=4)
        self.last_shot_time = 0
        logger.debug(f"Ranged Enemy {self.id} created")

    def update(
        self,
        player_position=None,
        current_time=None,
        projectile_group=None,
        all_sprites=None,
        enemy_group=None,
    ):
        """Update ranged enemy behavior."""
        if (
            not player_position
            or current_time is None
            or projectile_group is None
            or all_sprites is None
        ):
            super().move_towards(player_position, enemy_group)
            return
        dx = player_position[0] - self.position[0]
        dy = player_position[1] - self.position[1]
        distance = math.sqrt(dx**2 + dy**2)
        if distance > self.preferred_distance + 50:
            super().move_towards(player_position, enemy_group)
        elif distance < self.preferred_distance - 50:
            away_position = (self.position[0] - dx * 2, self.position[1] - dy * 2)
            self.move_towards(away_position, enemy_group)
        if current_time - self.last_shot_time > self.attack_cooldown:
            self.shoot_at_player(player_position, projectile_group, all_sprites)
            self.last_shot_time = current_time
        super().apply_visual_effects()

    def shoot_at_player(self, player_position, projectile_group, all_sprites):
        """Shoot a projectile at the player."""
        dx = player_position[0] - self.position[0]
        dy = player_position[1] - self.position[1]
        distance = max(1, math.sqrt(dx**2 + dy**2))
        normalized_dx = dx / distance
        normalized_dy = dy / distance
        velocity = (normalized_dx * self.projectile_speed, normalized_dy * self.projectile_speed)
        start_pos = (
            self.rect.centerx + normalized_dx * self.rect.width * 0.6,
            self.rect.centery + normalized_dy * self.rect.height * 0.6,
        )
        map_width = getattr(self, "map_width", None)
        map_height = getattr(self, "map_height", None)
        projectile = Projectile(
            start_pos,
            velocity,
            damage=self.projectile_damage,
            is_enemy_projectile=True,
            map_width=map_width,
            map_height=map_height,
        )
        projectile_group.add(projectile)
        all_sprites.add(projectile)
        logger.debug(f"Ranged Enemy {self.id} fired projectile with velocity {velocity}")
        return projectile


class ChargerEnemy(Enemy):
    """Enemy that charges at the player when in range."""

    def __init__(self, position):
        super().__init__(position, Enemy.TYPE_CHARGER)
        # Cache charger-specific attributes
        self.charge_distance = config.get("enemy", "charger", "charge_distance", default=150)
        self.charge_cooldown = config.get("enemy", "charger", "charge_cooldown", default=3000)
        self.charge_duration = config.get("enemy", "charger", "charge_duration", default=1000)
        self.charge_speed_multiplier = config.get(
            "enemy", "charger", "charge_speed_multiplier", default=3
        )
        self.normal_speed = config.get("enemy", "charger", "speed", default=4.5)
        self.speed = self.normal_speed
        self.max_health = config.get("enemy", "charger", "max_health", default=50)
        self.health = self.max_health
        self.is_charging = False
        self.charge_start_time = 0
        self.last_charge_time = 0
        self.charge_direction = (0, 0)
        logger.debug(f"Charger Enemy {self.id} created")

    def update(
        self,
        player_position=None,
        current_time=None,
        projectile_group=None,
        all_sprites=None,
        enemy_group=None,
    ):
        """Update charger enemy behavior."""
        if not player_position or current_time is None:
            super().move_towards(player_position, enemy_group)
            return
        if self.is_charging:
            if current_time - self.charge_start_time > self.charge_duration:
                self.end_charge()
            else:
                self.position[0] += self.charge_direction[0] * self.speed
                self.position[1] += self.charge_direction[1] * self.speed
                self.rect.x = round(self.position[0])
                self.rect.y = round(self.position[1])
                super().apply_visual_effects()
                return
        dx = player_position[0] - self.position[0]
        dy = player_position[1] - self.position[1]
        distance = math.sqrt(dx**2 + dy**2)
        if (
            distance < self.charge_distance
            and current_time - self.last_charge_time > self.charge_cooldown
        ):
            self.start_charge(player_position, current_time)
        else:
            super().move_towards(player_position, enemy_group)
        super().apply_visual_effects()

    def start_charge(self, player_position, current_time: int):
        """Initiate a charge towards the player."""
        self.is_charging = True
        self.charge_start_time = current_time
        self.last_charge_time = current_time
        dx = player_position[0] - self.position[0]
        dy = player_position[1] - self.position[1]
        distance = max(1, math.sqrt(dx**2 + dy**2))
        self.charge_direction = (dx / distance, dy / distance)
        self.speed = self.normal_speed * self.charge_speed_multiplier
        logger.debug(f"Charger Enemy {self.id} started charge attack")

    def end_charge(self):
        """End the charge and reset speed."""
        self.is_charging = False
        self.speed = self.normal_speed
        logger.debug(f"Charger Enemy {self.id} ended charge attack")


def create_enemy(position, enemy_type=None, attr_multipliers=None):
    """
    Factory function to create an enemy instance.

    Args:
        position: Initial (x, y) position of the enemy
        enemy_type: Type of enemy to create ("basic", "ranged", "charger"). If None, a random type is chosen.
        attr_multipliers: Dictionary of attribute multipliers (health, damage, speed) to apply

    Returns:
        Enemy instance of the specified type with attributes scaled by the multipliers
    """
    # Default multipliers
    if attr_multipliers is None:
        attr_multipliers = {"health": 1.0, "damage": 1.0, "speed": 1.0}

    # Choose a random enemy type if none specified
    if enemy_type is None:
        weights = config.get(
            "enemy",
            "spawn_weights",
            default={Enemy.TYPE_BASIC: 60, Enemy.TYPE_RANGED: 20, Enemy.TYPE_CHARGER: 20},
        )
        enemy_type = random.choices(list(weights.keys()), list(weights.values()), k=1)[0]

    # Create the enemy based on type
    if enemy_type == Enemy.TYPE_RANGED:
        enemy = RangedEnemy(position)
    elif enemy_type == Enemy.TYPE_CHARGER:
        enemy = ChargerEnemy(position)
    else:
        enemy = Enemy(position)

    # Apply attribute multipliers
    health_multiplier = attr_multipliers.get("health", 1.0)
    damage_multiplier = attr_multipliers.get("damage", 1.0)
    speed_multiplier = attr_multipliers.get("speed", 1.0)

    # Scale health
    if hasattr(enemy, "max_health"):
        enemy.max_health = int(enemy.max_health * health_multiplier)
        enemy.health = enemy.max_health

    # Scale damage
    if hasattr(enemy, "damage"):
        enemy.damage = int(enemy.damage * damage_multiplier)
    if hasattr(enemy, "projectile_damage"):
        enemy.projectile_damage = int(enemy.projectile_damage * damage_multiplier)

    # Scale speed
    if hasattr(enemy, "speed"):
        enemy.speed = enemy.speed * speed_multiplier
    if hasattr(enemy, "normal_speed"):  # For charger enemies
        enemy.normal_speed = enemy.normal_speed * speed_multiplier

    logger.debug(f"Created {enemy_type} enemy with multipliers: {attr_multipliers}")
    return enemy
