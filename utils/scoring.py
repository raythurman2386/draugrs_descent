import os
import json
import pygame
from utils.logger import GameLogger

# Get a logger for the scoring module
logger = GameLogger.get_logger("scoring")


class ScoreManager:
    """Manages game scoring and high score tracking."""

    # Score values for different game events
    ENEMY_DEFEAT_POINTS = 100
    POWERUP_COLLECTED_POINTS = 50
    POINTS_PER_SECOND = 1  # Points per second survived

    def __init__(self):
        """Initialize the score manager."""
        self.current_score = 0
        self.high_score = 0
        self.score_multiplier = 1.0

        # Attempt to load high score from file
        self.load_high_score()

        logger.info("ScoreManager initialized")

    def add_score(self, points):
        """Add points to the current score, affected by multiplier."""
        points_to_add = int(points * self.score_multiplier)
        self.current_score += points_to_add

        # Update high score if needed
        if self.current_score > self.high_score:
            self.high_score = self.current_score
            logger.info(f"New high score: {self.high_score}")

        logger.debug(f"Added {points_to_add} points to score (multiplier: {self.score_multiplier})")

    def enemy_defeated(self):
        """Add points for defeating an enemy."""
        self.add_score(self.ENEMY_DEFEAT_POINTS)
        logger.debug(f"Enemy defeated: +{self.ENEMY_DEFEAT_POINTS} points")

    def powerup_collected(self):
        """Add points for collecting a powerup."""
        self.add_score(self.POWERUP_COLLECTED_POINTS)
        logger.debug(f"Powerup collected: +{self.POWERUP_COLLECTED_POINTS} points")

    def add_time_survived_points(self, seconds):
        """Add points based on time survived."""
        points = seconds * self.POINTS_PER_SECOND
        self.add_score(points)
        logger.debug(f"Time survived: +{points} points for {seconds} seconds")

    def reset_current_score(self):
        """Reset the current score back to zero."""
        self.current_score = 0
        logger.info("Score reset to 0")

    def set_multiplier(self, multiplier):
        """Set the score multiplier."""
        self.score_multiplier = multiplier
        logger.debug(f"Score multiplier set to {multiplier}")

    def reset_multiplier(self):
        """Reset the score multiplier to 1.0."""
        self.score_multiplier = 1.0
        logger.debug("Score multiplier reset to 1.0")

    def save_high_score(self):
        """Save the high score to a file."""
        try:
            data = {"high_score": self.high_score}
            with open("data/high_score.json", "w") as f:
                json.dump(data, f)
            logger.info(f"High score {self.high_score} saved successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save high score: {e}")
            return False

    def load_high_score(self):
        """Load the high score from a file."""
        try:
            # Create data directory if it doesn't exist
            os.makedirs("data", exist_ok=True)

            # Check if high score file exists
            if os.path.exists("data/high_score.json"):
                with open("data/high_score.json", "r") as f:
                    data = json.load(f)
                    self.high_score = data.get("high_score", 0)
                logger.info(f"High score loaded: {self.high_score}")
            else:
                logger.info("No high score file found, starting with 0")
            return self.high_score
        except Exception as e:
            logger.error(f"Failed to load high score: {e}")
            return 0

    def get_formatted_score(self):
        """Return the current score formatted as a string."""
        return f"{self.current_score:,}"

    def get_formatted_high_score(self):
        """Return the high score formatted as a string."""
        return f"{self.high_score:,}"
