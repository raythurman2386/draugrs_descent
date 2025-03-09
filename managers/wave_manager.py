"""Wave Manager for handling enemy wave spawning and progression."""

import pygame
import random
from utils.logger import GameLogger
from managers import config

# Get a logger for the wave manager module
logger = GameLogger.get_logger("wave_manager")


class WaveManager:
    """
    Manages waves of enemies with progressive difficulty.

    Handles:
    - Wave progression and tracking
    - Enemy count scaling
    - Enemy attribute scaling
    - Spawn rate adjustments
    - Boss wave integration
    """

    def __init__(self, game_scene):
        """
        Initialize the wave manager.

        Args:
            game_scene: Reference to the game scene for spawning enemies
        """
        self.game_scene = game_scene
        self.current_wave = 0
        self.wave_in_progress = False
        self.enemies_remaining = 0
        self.last_enemy_spawn_time = 0
        self.current_wave_start_time = 0

        # Load wave configuration from config
        self.wave_config = self._load_wave_config()

        # Cache frequently accessed configuration values
        self.boss_wave_frequency = self.wave_config.get("boss_wave_frequency", 5)
        self.base_enemies_per_wave = self.wave_config.get("base_enemies_per_wave", 10)
        self.enemies_increase_per_wave = self.wave_config.get("enemies_increase_per_wave", 3)
        self.max_enemies_per_wave = self.wave_config.get("max_enemies_per_wave", 50)
        self.base_spawn_interval = self.wave_config.get("base_spawn_interval", 1000)
        self.min_spawn_interval = self.wave_config.get("min_spawn_interval", 200)
        self.spawn_interval_decrease = self.wave_config.get("spawn_interval_decrease", 50)

        # Enemy scaling factors
        self.enemy_health_scaling = self.wave_config.get("enemy_health_scaling", 0.1)
        self.enemy_damage_scaling = self.wave_config.get("enemy_damage_scaling", 0.05)
        self.enemy_speed_scaling = self.wave_config.get("enemy_speed_scaling", 0.03)

        # Enemy type distribution by wave number
        self.enemy_distribution = self.wave_config.get("enemy_distribution", {})

        logger.info("Wave Manager initialized")

    def _load_wave_config(self):
        """Load wave configuration from the game config."""
        wave_config = config.get("waves", default={})

        # If wave config doesn't exist, create default configuration
        if not wave_config:
            logger.warning("Wave configuration not found in game_config.yaml, using defaults")
            wave_config = {
                "boss_wave_frequency": 5,
                "base_enemies_per_wave": 10,
                "enemies_increase_per_wave": 3,
                "max_enemies_per_wave": 50,
                "base_spawn_interval": 1000,
                "min_spawn_interval": 200,
                "spawn_interval_decrease": 50,
                "enemy_health_scaling": 0.1,
                "enemy_damage_scaling": 0.05,
                "enemy_speed_scaling": 0.03,
                "enemy_distribution": {
                    "wave1": {"basic": 100, "ranged": 0, "charger": 0},
                    "wave5": {"basic": 60, "ranged": 30, "charger": 10},
                    "wave10": {"basic": 40, "ranged": 40, "charger": 20},
                    "wave20": {"basic": 30, "ranged": 40, "charger": 30},
                },
            }

        return wave_config

    def start_next_wave(self):
        """Start the next wave of enemies."""
        self.current_wave += 1
        self.wave_in_progress = True
        self.current_wave_start_time = pygame.time.get_ticks()
        self.last_enemy_spawn_time = self.current_wave_start_time

        # Calculate number of enemies for this wave
        self.enemies_remaining = self.get_enemy_count_for_wave(self.current_wave)

        # Determine if this is a boss wave
        is_boss = self.is_boss_wave(self.current_wave)

        # Log wave start
        if is_boss:
            logger.info(
                f"Starting boss wave {self.current_wave} with {self.enemies_remaining} enemies"
            )
        else:
            logger.info(f"Starting wave {self.current_wave} with {self.enemies_remaining} enemies")

        return is_boss

    def update(self, current_time):
        """
        Update wave progress and spawn enemies as needed.

        Args:
            current_time: Current game time in milliseconds
        """
        if not self.wave_in_progress:
            return

        # Check if wave is complete
        if self.is_wave_complete():
            self.wave_in_progress = False
            logger.info(f"Wave {self.current_wave} completed!")
            return

        # Check if it's time to spawn a new enemy
        spawn_interval = self.get_spawn_interval(self.current_wave)
        if (
            current_time - self.last_enemy_spawn_time >= spawn_interval
            and self.enemies_remaining > 0
        ):
            # Get enemy type distribution for this wave
            enemy_types = self.get_enemy_type_distribution(self.current_wave)

            # Choose enemy type based on distribution
            enemy_type = self._choose_enemy_type(enemy_types)

            # Get attribute multipliers for this wave
            attr_multipliers = self.get_enemy_attributes_multiplier(self.current_wave)

            # Spawn the enemy
            self._spawn_enemy(enemy_type, attr_multipliers)

            # Update spawn time and enemy count
            self.last_enemy_spawn_time = current_time
            self.enemies_remaining -= 1

    def _spawn_enemy(self, enemy_type, attr_multipliers):
        """
        Spawn an enemy of the given type with scaled attributes.

        Args:
            enemy_type: Type of enemy to spawn ('basic', 'ranged', 'charger')
            attr_multipliers: Dictionary of attribute multipliers
        """
        # If this is a boss wave and it's the first enemy, spawn a boss
        if self.is_boss_wave(
            self.current_wave
        ) and self.enemies_remaining == self.get_enemy_count_for_wave(self.current_wave):
            logger.debug("Spawning boss enemy")
            # We would implement boss spawning logic here
            if hasattr(self.game_scene, "spawn_boss"):
                self.game_scene.spawn_boss(attr_multipliers)
            else:
                # If no boss spawning method exists, spawn a stronger regular enemy
                self.game_scene.spawn_enemy(enemy_type, attr_multipliers)
        else:
            # Spawn regular enemy
            logger.debug(f"Spawning {enemy_type} enemy with multipliers: {attr_multipliers}")
            self.game_scene.spawn_enemy(enemy_type, attr_multipliers)

    def _choose_enemy_type(self, type_distribution):
        """
        Choose an enemy type based on the probability distribution.

        Args:
            type_distribution: Dictionary mapping enemy types to spawn weights

        Returns:
            String representing the chosen enemy type
        """
        # Convert distribution to a list for random.choices
        enemy_types = list(type_distribution.keys())
        weights = list(type_distribution.values())

        # If no valid weights, default to basic
        if not weights or sum(weights) == 0:
            return "basic"

        # Choose enemy type based on weights
        chosen_type = random.choices(enemy_types, weights=weights, k=1)[0]
        return chosen_type

    def is_boss_wave(self, wave_number):
        """
        Check if the given wave number is a boss wave.

        Args:
            wave_number: Wave number to check

        Returns:
            True if it's a boss wave, False otherwise
        """
        return wave_number % self.boss_wave_frequency == 0

    def get_enemy_count_for_wave(self, wave_number):
        """
        Get the number of enemies for the given wave.

        Args:
            wave_number: Wave number to get enemy count for

        Returns:
            Number of enemies for the wave
        """
        # Calculate base enemy count with scaling
        enemy_count = (
            self.base_enemies_per_wave + (wave_number - 1) * self.enemies_increase_per_wave
        )

        # Apply maximum limit
        enemy_count = min(enemy_count, self.max_enemies_per_wave)

        # Reduce count for boss waves (fewer but stronger enemies)
        if self.is_boss_wave(wave_number):
            # For boss waves, reduce the count but ensure it's still more than earlier waves
            # Calculate what the count would be for the previous wave
            prev_wave_count = (
                self.base_enemies_per_wave
                + ((wave_number - 1) - 1) * self.enemies_increase_per_wave
            )
            # Ensure boss wave has at least as many enemies as previous wave
            enemy_count = max(prev_wave_count, enemy_count // 2)

        return enemy_count

    def get_spawn_interval(self, wave_number):
        """
        Get the enemy spawn interval for the given wave.

        Args:
            wave_number: Wave number to get spawn interval for

        Returns:
            Spawn interval in milliseconds
        """
        # Calculate spawn interval with reduction per wave
        interval = self.base_spawn_interval - (wave_number - 1) * self.spawn_interval_decrease

        # Apply minimum limit
        interval = max(interval, self.min_spawn_interval)

        return interval

    def get_enemy_attributes_multiplier(self, wave_number):
        """
        Get multipliers for enemy attributes based on wave number.

        Args:
            wave_number: Wave number to get multipliers for

        Returns:
            Dictionary of attribute multipliers
        """
        # Calculate base multiplier (wave 1 = 1.0)
        wave_factor = wave_number - 1

        # Calculate individual attribute multipliers
        health_multiplier = 1.0 + (wave_factor * self.enemy_health_scaling)
        damage_multiplier = 1.0 + (wave_factor * self.enemy_damage_scaling)
        speed_multiplier = 1.0 + (wave_factor * self.enemy_speed_scaling)

        # Boost multipliers for boss waves
        if self.is_boss_wave(wave_number):
            boss_health_multiplier = self.wave_config.get("boss_health_multiplier", 5.0)
            boss_damage_multiplier = self.wave_config.get("boss_damage_multiplier", 2.0)

            health_multiplier *= boss_health_multiplier
            damage_multiplier *= boss_damage_multiplier

        return {"health": health_multiplier, "damage": damage_multiplier, "speed": speed_multiplier}

    def get_enemy_type_distribution(self, wave_number):
        """
        Get the enemy type distribution for the given wave.

        Args:
            wave_number: Wave number to get distribution for

        Returns:
            Dictionary mapping enemy types to spawn weights
        """
        # Default distribution - all basic enemies
        default_distribution = {"basic": 100, "ranged": 0, "charger": 0}

        # Get predefined distributions from config
        distributions = self.enemy_distribution

        # Convert string wave keys to integers for comparison
        wave_points = {}
        for wave_key in distributions.keys():
            if wave_key.startswith("wave"):
                try:
                    wave_num = int(wave_key[4:])
                    wave_points[wave_num] = distributions[wave_key]
                except ValueError:
                    logger.warning(f"Invalid wave key in config: {wave_key}")

        # If no wave points defined, return default
        if not wave_points:
            return default_distribution

        # Sort wave points by wave number
        sorted_points = sorted(wave_points.items())

        # If wave_number is less than first defined point, use first defined distribution
        if wave_number <= sorted_points[0][0]:
            return sorted_points[0][1]

        # If wave_number is greater than last defined point, use last defined distribution
        if wave_number >= sorted_points[-1][0]:
            return sorted_points[-1][1]

        # Find the two points to interpolate between
        lower_point = None
        upper_point = None

        for i, (point_wave, _) in enumerate(sorted_points):
            if point_wave <= wave_number:
                lower_point = sorted_points[i]
            if point_wave >= wave_number and upper_point is None:
                upper_point = sorted_points[i]
                break

        # If we couldn't find two points to interpolate (shouldn't happen), use default
        if lower_point is None or upper_point is None or lower_point == upper_point:
            return lower_point[1] if lower_point else default_distribution

        # Interpolate between the two closest wave points
        lower_wave, lower_dist = lower_point
        upper_wave, upper_dist = upper_point

        # Linear interpolation factor
        factor = (wave_number - lower_wave) / (upper_wave - lower_wave)

        # Interpolate values for each enemy type
        result = {}
        for enemy_type in set(lower_dist.keys()).union(upper_dist.keys()):
            lower_value = lower_dist.get(enemy_type, 0)
            upper_value = upper_dist.get(enemy_type, 0)
            interpolated = lower_value + factor * (upper_value - lower_value)
            result[enemy_type] = int(interpolated)

        return result

    def is_wave_complete(self):
        """
        Check if the current wave is complete.

        Returns:
            True if wave is complete, False otherwise
        """
        return self.enemies_remaining <= 0 and self.wave_in_progress
