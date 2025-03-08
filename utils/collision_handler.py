"""Handle collisions between game objects."""

import pygame
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
    # Get current time for enemy collision cooldown check
    current_time = pygame.time.get_ticks()

    # Check if enemy can collide (based on its cooldown)
    if hasattr(enemy, "can_collide") and not enemy.can_collide(current_time):
        return False

    # Log detailed information about the collision and damage
    logger.debug(f"Player collided with Enemy {enemy.id} (type: {enemy.enemy_type})")
    logger.debug(f"Enemy damage: {enemy.damage}, Player current health: {player.current_health}")

    # Apply damage to player and return the result
    result = player.take_damage(enemy.damage)

    # Log the result of damage application
    logger.debug(f"Damage applied: {enemy.damage}, Player health after: {player.current_health}")

    return result


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
    if hasattr(player, "apply_visual_effects"):
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


# Spatial partitioning for optimized collision detection
class QuadTree:
    """
    QuadTree implementation for spatial partitioning.

    Divides the screen space into quadrants to reduce the number of collision checks needed.
    """

    def __init__(self, bounds, max_objects=10, max_levels=4, level=0):
        """
        Initialize a QuadTree node.

        Args:
            bounds: Tuple of (x, y, width, height) defining the quadtree area
            max_objects: Maximum number of objects a node can hold before splitting
            max_levels: Maximum depth of the quadtree
            level: Current level of this quadtree node (0 = root)
        """
        self.bounds = pygame.Rect(bounds)
        self.max_objects = max_objects
        self.max_levels = max_levels
        self.level = level
        self.objects = []
        self.nodes = []  # Four child nodes
        self.is_divided = False

    def clear(self):
        """Reset the quadtree by clearing all objects and child nodes."""
        self.objects.clear()

        for i in range(len(self.nodes)):
            if i < len(self.nodes):
                self.nodes[i].clear()

        self.nodes.clear()
        self.is_divided = False

    def divide(self):
        """Divide this node into four quadrants."""
        x = self.bounds.x
        y = self.bounds.y
        sub_width = self.bounds.width // 2
        sub_height = self.bounds.height // 2

        # Create four child nodes
        self.nodes.append(
            QuadTree(
                (x, y, sub_width, sub_height), self.max_objects, self.max_levels, self.level + 1
            )
        )
        self.nodes.append(
            QuadTree(
                (x + sub_width, y, sub_width, sub_height),
                self.max_objects,
                self.max_levels,
                self.level + 1,
            )
        )
        self.nodes.append(
            QuadTree(
                (x, y + sub_height, sub_width, sub_height),
                self.max_objects,
                self.max_levels,
                self.level + 1,
            )
        )
        self.nodes.append(
            QuadTree(
                (x + sub_width, y + sub_height, sub_width, sub_height),
                self.max_objects,
                self.max_levels,
                self.level + 1,
            )
        )

        self.is_divided = True

    def get_index(self, rect):
        """
        Determine which quadrant an object belongs to.

        Args:
            rect: The pygame.Rect of the object

        Returns:
            int: Index of the quadrant (0-3) or -1 if it spans multiple quadrants
        """
        index = -1

        # Calculate vertical and horizontal midpoints
        v_midpoint = self.bounds.x + (self.bounds.width / 2)
        h_midpoint = self.bounds.y + (self.bounds.height / 2)

        # Check if the object fits entirely in the top quadrants
        top_quadrant = rect.y < h_midpoint and rect.y + rect.height < h_midpoint
        # Check if the object fits entirely in the bottom quadrants
        bottom_quadrant = rect.y > h_midpoint

        # Check if the object fits entirely in the left quadrants
        if rect.x < v_midpoint and rect.x + rect.width < v_midpoint:
            if top_quadrant:
                index = 0  # Top-left
            elif bottom_quadrant:
                index = 2  # Bottom-left

        # Check if the object fits entirely in the right quadrants
        elif rect.x > v_midpoint:
            if top_quadrant:
                index = 1  # Top-right
            elif bottom_quadrant:
                index = 3  # Bottom-right

        return index

    def insert(self, sprite):
        """
        Insert a sprite into the quadtree.

        Args:
            sprite: A pygame.sprite.Sprite object with a rect attribute
        """
        # If this node has already been divided, insert the sprite into the appropriate child node
        if self.is_divided:
            index = self.get_index(sprite.rect)

            # If the sprite fits in a specific quadrant, insert it there
            if index != -1:
                self.nodes[index].insert(sprite)
                return

        # If the sprite doesn't fit in a specific quadrant or the node hasn't been divided,
        # add it to this node's objects
        self.objects.append(sprite)

        # Check if we need to divide this node
        if (
            not self.is_divided
            and len(self.objects) > self.max_objects
            and self.level < self.max_levels
        ):
            # Divide this node if it hasn't been divided already
            if not self.is_divided:
                self.divide()

            # Redistribute existing objects into child nodes where possible
            i = 0
            while i < len(self.objects):
                index = self.get_index(self.objects[i].rect)

                if index != -1:
                    # If the object fits in a specific quadrant, move it there
                    sprite_to_move = self.objects.pop(i)
                    self.nodes[index].insert(sprite_to_move)
                else:
                    # If the object spans multiple quadrants, keep it in this node
                    i += 1

    def retrieve(self, potential_collisions, sprite):
        """
        Retrieve all sprites that could potentially collide with the given sprite.

        Args:
            potential_collisions: List to populate with sprites that could collide
            sprite: The sprite to check potential collisions against

        Returns:
            list: Updated list of potential collisions
        """
        # Get the index of which quadrant the sprite belongs to
        index = self.get_index(sprite.rect)

        # If the sprite fits in a specific quadrant and this node is divided
        if index != -1 and self.is_divided:
            self.nodes[index].retrieve(potential_collisions, sprite)
        else:
            # If the sprite spans multiple quadrants or this node is not divided,
            # check against all child nodes
            if self.is_divided:
                for node in self.nodes:
                    # Checks if the sprite's rect intersects with the node's bounds
                    if node.bounds.colliderect(sprite.rect):
                        node.retrieve(potential_collisions, sprite)

        # Add all sprites in this node as potential collisions
        potential_collisions.extend(self.objects)

        return potential_collisions


class SpatialHashGrid:
    """
    Spatial hash grid implementation for collision detection optimization.

    Divides the screen into a grid of cells and assigns sprites to cells
    based on their position to reduce collision checks.
    """

    def __init__(self, width, height, cell_size=64):
        """
        Initialize the spatial hash grid.

        Args:
            width: Width of the game area
            height: Height of the game area
            cell_size: Size of each grid cell (smaller = more precise but more memory)
        """
        self.cell_size = cell_size
        self.width = width
        self.height = height
        self.grid = {}

    def clear(self):
        """Clear the grid."""
        self.grid.clear()

    def _get_cell_key(self, x, y):
        """
        Get the key for a cell at the given coordinates.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            tuple: (cell_x, cell_y) key
        """
        return (x // self.cell_size, y // self.cell_size)

    def _get_cells_for_rect(self, rect):
        """
        Get all cell keys that a rectangle occupies.

        Args:
            rect: pygame.Rect object

        Returns:
            list: List of cell keys
        """
        left = rect.left
        right = rect.right
        top = rect.top
        bottom = rect.bottom

        # Calculate the cell ranges
        start_x = left // self.cell_size
        end_x = right // self.cell_size
        start_y = top // self.cell_size
        end_y = bottom // self.cell_size

        # Generate all cell keys
        cell_keys = []
        for x in range(start_x, end_x + 1):
            for y in range(start_y, end_y + 1):
                cell_keys.append((x, y))

        return cell_keys

    def insert(self, sprite):
        """
        Insert a sprite into the grid.

        Args:
            sprite: A pygame.sprite.Sprite object with a rect attribute
        """
        # Get all cells the sprite occupies
        cell_keys = self._get_cells_for_rect(sprite.rect)

        # Add the sprite to each cell
        for key in cell_keys:
            if key not in self.grid:
                self.grid[key] = []

            self.grid[key].append(sprite)

    def retrieve(self, sprite):
        """
        Retrieve all sprites that could potentially collide with the given sprite.

        Args:
            sprite: The sprite to check potential collisions against

        Returns:
            list: List of potential collisions (without duplicates)
        """
        # Get all cells the sprite occupies
        cell_keys = self._get_cells_for_rect(sprite.rect)

        # Create a set to avoid duplicate sprites
        potential_collisions = set()

        # Add all sprites from each occupied cell
        for key in cell_keys:
            if key in self.grid:
                for potential_sprite in self.grid[key]:
                    # Don't add the sprite itself
                    if potential_sprite != sprite:
                        potential_collisions.add(potential_sprite)

        return list(potential_collisions)


class CollisionSystem:
    """
    Optimized collision detection system using spatial partitioning.

    Can use either QuadTree or SpatialHashGrid for optimization.
    """

    # Spatial partitioning algorithms
    QUADTREE = "quadtree"
    SPATIAL_HASH = "spatial_hash"

    def __init__(self, screen_width, screen_height, algorithm=SPATIAL_HASH, cell_size=64):
        """
        Initialize the collision system.

        Args:
            screen_width: Width of the game screen
            screen_height: Height of the game screen
            algorithm: Spatial partitioning algorithm to use (QUADTREE or SPATIAL_HASH)
            cell_size: Size of grid cells if using SPATIAL_HASH
        """
        self.algorithm = algorithm
        self.screen_width = screen_width
        self.screen_height = screen_height

        logger.info(f"Initializing optimized collision system using {algorithm} algorithm")

        # Create the appropriate spatial partitioning structure
        if algorithm == self.QUADTREE:
            self.spatial_structure = QuadTree((0, 0, screen_width, screen_height))
        else:  # SPATIAL_HASH
            self.spatial_structure = SpatialHashGrid(screen_width, screen_height, cell_size)

    def update(self, projectile_group, enemy_group, player, powerup_group):
        """
        Update the spatial structure with current game objects.

        Args:
            projectile_group: Group of projectile sprites
            enemy_group: Group of enemy sprites
            player: Player sprite
            powerup_group: Group of powerup sprites
        """
        # Clear the previous state
        self.spatial_structure.clear()

        # Insert all sprites into the spatial structure
        for projectile in projectile_group:
            self.spatial_structure.insert(projectile)

        for enemy in enemy_group:
            self.spatial_structure.insert(enemy)

        for powerup in powerup_group:
            self.spatial_structure.insert(powerup)

        # Insert player
        self.spatial_structure.insert(player)

    def check_projectile_enemy_collisions(self, projectile_group, enemy_group):
        """
        Check for collisions between projectiles and enemies.

        Args:
            projectile_group: Group of projectile sprites
            enemy_group: Group of enemy sprites

        Returns:
            dict: Dictionary mapping projectiles to lists of enemies they collided with
        """
        collisions = {}

        # Only consider player projectiles (not enemy projectiles)
        player_projectiles = [
            p
            for p in projectile_group
            if not hasattr(p, "is_enemy_projectile") or not p.is_enemy_projectile
        ]

        # Retrieve enemies for each projectile
        for projectile in player_projectiles:
            # Get potential collisions
            if self.algorithm == self.QUADTREE:
                potential_enemies = []
                self.spatial_structure.retrieve(potential_enemies, projectile)
                # Filter to only include enemies
                potential_enemies = [
                    sprite for sprite in potential_enemies if sprite in enemy_group
                ]
            else:  # SPATIAL_HASH
                potential_enemies = [
                    sprite
                    for sprite in self.spatial_structure.retrieve(projectile)
                    if sprite in enemy_group
                ]

            # Check for actual collisions
            enemies_hit = []
            for enemy in potential_enemies:
                if mask_collision(projectile, enemy):
                    enemies_hit.append(enemy)

            if enemies_hit:
                collisions[projectile] = enemies_hit

        return collisions

    def check_enemy_projectile_player_collision(self, player, projectile_group):
        """
        Check for collisions between enemy projectiles and the player.

        Args:
            player: Player sprite
            projectile_group: Group of projectile sprites

        Returns:
            list: List of projectiles that hit the player
        """
        # Skip if player is invincible
        if hasattr(player, "invincible") and player.invincible:
            return []

        # Only consider enemy projectiles
        enemy_projectiles = [
            p
            for p in projectile_group
            if hasattr(p, "is_enemy_projectile") and p.is_enemy_projectile
        ]

        # Get potential collisions
        if self.algorithm == self.QUADTREE:
            potential_projectiles = []
            self.spatial_structure.retrieve(potential_projectiles, player)
            # Filter to only include enemy projectiles
            potential_projectiles = [p for p in potential_projectiles if p in enemy_projectiles]
        else:  # SPATIAL_HASH
            potential_projectiles = [
                p for p in self.spatial_structure.retrieve(player) if p in enemy_projectiles
            ]

        # Check for actual collisions
        projectiles_hit = []
        for projectile in potential_projectiles:
            if mask_collision(player, projectile):
                projectiles_hit.append(projectile)

        return projectiles_hit

    def check_player_enemy_collisions(self, player, enemy_group):
        """
        Check for collisions between the player and enemies.

        Args:
            player: Player sprite
            enemy_group: Group of enemy sprites

        Returns:
            list: List of enemies that collided with the player
        """
        # Skip if player is invincible
        if hasattr(player, "invincible") and player.invincible:
            return []

        # Get potential collisions
        if self.algorithm == self.QUADTREE:
            potential_enemies = []
            self.spatial_structure.retrieve(potential_enemies, player)
            # Filter to only include enemies
            potential_enemies = [sprite for sprite in potential_enemies if sprite in enemy_group]
        else:  # SPATIAL_HASH
            potential_enemies = [
                sprite
                for sprite in self.spatial_structure.retrieve(player)
                if sprite in enemy_group
            ]

        # Check for actual collisions
        enemies_hit = []
        for enemy in potential_enemies:
            if mask_collision(player, enemy):
                enemies_hit.append(enemy)

        return enemies_hit

    def check_player_powerup_collisions(self, player, powerup_group):
        """
        Check for collisions between the player and powerups.

        Args:
            player: Player sprite
            powerup_group: Group of powerup sprites

        Returns:
            list: List of powerups that collided with the player
        """
        # Get potential collisions
        if self.algorithm == self.QUADTREE:
            potential_powerups = []
            self.spatial_structure.retrieve(potential_powerups, player)
            # Filter to only include powerups
            potential_powerups = [
                sprite for sprite in potential_powerups if sprite in powerup_group
            ]
        else:  # SPATIAL_HASH
            potential_powerups = [
                sprite
                for sprite in self.spatial_structure.retrieve(player)
                if sprite in powerup_group
            ]

        # Check for actual collisions
        powerups_hit = []
        for powerup in potential_powerups:
            if mask_collision(player, powerup) and hasattr(powerup, "active") and powerup.active:
                powerups_hit.append(powerup)

        return powerups_hit


def pixel_perfect_collision(sprite1, sprite2):
    """
    Check for pixel-perfect collision between two sprites.

    Args:
        sprite1: First sprite to check
        sprite2: Second sprite to check

    Returns:
        True if there's a pixel-perfect collision, False otherwise
    """
    # First check if the bounding rectangles collide
    if not sprite1.rect.colliderect(sprite2.rect):
        return False

    # If they do, perform pixel-perfect collision detection
    # Calculate the overlap rectangle between the two sprites
    x_offset = sprite2.rect.x - sprite1.rect.x
    y_offset = sprite2.rect.y - sprite1.rect.y

    # Loop through each pixel in the overlap area
    for x in range(max(0, -x_offset), min(sprite1.rect.width, sprite2.rect.width - x_offset)):
        for y in range(max(0, -y_offset), min(sprite1.rect.height, sprite2.rect.height - y_offset)):
            # Check if both pixels at this position are opaque
            try:
                mask1 = sprite1.image.get_at((x, y))[3] > 0  # Alpha > 0
                mask2 = sprite2.image.get_at((x + x_offset, y + y_offset))[3] > 0  # Alpha > 0
                if mask1 and mask2:
                    return True
            except IndexError:
                # Skip pixels that are out of bounds
                continue

    return False


def mask_collision(sprite1, sprite2):
    """
    More efficient pixel-perfect collision detection using Pygame masks.

    Args:
        sprite1: First sprite to check
        sprite2: Second sprite to check

    Returns:
        True if there's a mask collision, False otherwise
    """
    # Create masks for both sprites (if they don't already have them)
    if not hasattr(sprite1, "mask") or sprite1.mask is None:
        sprite1.mask = pygame.mask.from_surface(sprite1.image)

    if not hasattr(sprite2, "mask") or sprite2.mask is None:
        sprite2.mask = pygame.mask.from_surface(sprite2.image)

    # Calculate the offset between the two sprites
    offset = (sprite2.rect.x - sprite1.rect.x, sprite2.rect.y - sprite1.rect.y)

    # Check if the masks overlap at the given offset
    return sprite1.mask.overlap(sprite2.mask, offset) is not None
