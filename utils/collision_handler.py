"""Handle collisions between game objects."""

from utils.logger import GameLogger
from constants import POWERUP_COLORS

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
        # Get the color for the visual effect
        color = POWERUP_COLORS.get(powerup.type, (255, 255, 255))
        player.start_flash_effect(color)

    # Apply the powerup effect
    return powerup.apply_effect(player)


def handle_projectile_enemy_collision(projectile, enemy):
    """Handle collision between projectile and enemy.

    Args:
        projectile: The projectile object.
        enemy: The enemy object.

    Returns:
        bool: True if enemy died, False otherwise.
    """
    logger.debug(f"Projectile {projectile.id} hit Enemy {enemy.id}")

    # Check if projectile is active to prevent double hits
    if not hasattr(projectile, "active") or projectile.active:
        # Deactivate projectile if it has that attribute
        if hasattr(projectile, "active"):
            projectile.active = False
        else:
            projectile.kill()  # Remove from sprite groups

        # Apply damage to enemy
        return enemy.take_damage(projectile.damage)

    return False
