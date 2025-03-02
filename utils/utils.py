import math
from .logger import GameLogger

# Get a logger for utils
logger = GameLogger.get_logger("utils")


def find_closest_enemy(player_pos, enemies):
    """Find the closest enemy to the player.

    Args:
        player_pos: Tuple (x, y) of player position
        enemies: Group or list of Enemy objects

    Returns:
        Closest enemy or None if no enemies
    """
    if not enemies:
        logger.debug("No enemies found when looking for closest enemy")
        return None

    closest = min(
        enemies,
        key=lambda e: math.hypot(e.rect.centerx - player_pos[0], e.rect.centery - player_pos[1]),
    )

    logger.debug(
        f"Found closest enemy at {closest.rect.center}, distance: {math.hypot(closest.rect.centerx - player_pos[0], closest.rect.centery - player_pos[1]):.2f}"
    )
    return closest


def adjust_log_level(level):
    """Adjust the log level for all loggers.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    GameLogger.set_all_loggers_level(level)
    logger.info(f"Set log level to {level}")


def distance(pos1, pos2):
    """Calculate distance between two positions.

    Args:
        pos1: Tuple (x, y) of first position
        pos2: Tuple (x, y) of second position

    Returns:
        Float distance between the positions
    """
    return math.hypot(pos2[0] - pos1[0], pos2[1] - pos1[1])
