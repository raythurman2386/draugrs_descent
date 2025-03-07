"""Handle collisions between game objects."""

from utils.logger import GameLogger

# Get a logger for the collision handler module
logger = GameLogger.get_logger("collision_handler")


def handle_player_enemy_collision(player, enemy):
    """Handle collision between player and enemy.

    Args:
        player: The player object.
        enemy: The enemy object.

    Returns:
        bool: True if player died, False otherwise.
    """
    logger.debug(f"Player collided with Enemy {enemy.id}")
    return player.take_damage(enemy.damage)


def handle_player_powerup_collision(player, powerup):
    """Handle collision between player and powerup.

    Args:
        player: The player object.
        powerup: The powerup object.

    Returns:
        bool: True if powerup was applied, False otherwise.
    """
    logger.debug(f"Player collided with {powerup.type} Powerup {powerup.id}")

    # Trigger visual effect with the powerup's color
    if hasattr(player, "start_flash_effect"):
        # Get the color for the visual effect from config - using lazy import
        from managers import config

        color = config.get_color(powerup.type)
        player.start_flash_effect(color)

    # Apply the powerup effect
    return powerup.apply_effect(player)


def handle_projectile_enemy_collision(projectile, enemy):
    """Handle collision between projectile and enemy.

    Args:
        projectile: The projectile object.
        enemy: The enemy object.

    Returns:
        bool: True if enemy was killed, False otherwise.
    """
    projectile.kill()
    return enemy.take_damage(projectile.damage)


def handle_enemy_projectile_player_collision(player, projectile):
    """Handle collision between enemy projectile and player.

    Args:
        player: The player object.
        projectile: The projectile object.

    Returns:
        bool: True if player was damaged, False otherwise.
    """
    logger.debug(f"Player hit by enemy projectile, dealing {projectile.damage} damage")
    projectile.kill()
    return player.take_damage(projectile.damage)
