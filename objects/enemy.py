import pygame
from managers import config
from utils.logger import GameLogger

# Get a logger for the enemy module
logger = GameLogger.get_logger("enemy")


class Enemy(pygame.sprite.Sprite):
    # Counter for unique enemy IDs
    next_id = 1

    def __init__(self, position):
        super().__init__()
        # Assign a unique ID to each enemy
        self.id = Enemy.next_id
        Enemy.next_id += 1

        # Get enemy dimensions from config
        width = config.get("enemy", "dimensions", "width", default=30)
        height = config.get("enemy", "dimensions", "height", default=30)

        self.image = pygame.Surface((width, height))
        self.image.fill(config.get_color("red"))
        self.rect = self.image.get_rect()
        self.rect.center = position
        self.position = list(position)  # For precise positioning

        # Get enemy attributes from config
        self.max_health = config.get("enemy", "attributes", "max_health", default=30)
        self.health = self.max_health
        self.damage = config.get("enemy", "attributes", "damage", default=10)
        self.speed = config.get("enemy", "attributes", "speed", default=2)

        logger.debug(f"Enemy {self.id} created at {position}")

    def move_towards(self, target_position):
        """Move the enemy towards the target position."""
        # Calculate direction vector
        dx = target_position[0] - self.position[0]
        dy = target_position[1] - self.position[1]

        # Normalize the direction
        distance = max(1, (dx**2 + dy**2) ** 0.5)  # Avoid division by zero
        dx = dx / distance
        dy = dy / distance

        # Move in the normalized direction
        self.position[0] += dx * self.speed
        self.position[1] += dy * self.speed

        # Update rect position
        self.rect.center = (int(self.position[0]), int(self.position[1]))

    def take_damage(self, amount):
        """
        Apply damage to the enemy.

        Args:
            amount: Amount of damage to apply

        Returns:
            bool: True if the enemy died, False otherwise
        """
        self.health -= amount
        logger.debug(
            f"Enemy {self.id} took {amount} damage. Health: {self.health}/{self.max_health}"
        )

        if self.health <= 0:
            self.kill()
            logger.debug(f"Enemy {self.id} died")
            return True
        return False

    def update(self, player_position=None):
        """
        Update enemy state.

        Args:
            player_position: Optional position to move towards
        """
        if player_position:
            self.move_towards(player_position)
