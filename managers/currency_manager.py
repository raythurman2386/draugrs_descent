import json
import os
from utils.logger import GameLogger

logger = GameLogger.get_logger("currency_manager")


class CurrencyManager:
    """
    Manages the player's currency (souls) that can be used to purchase upgrades.
    Handles saving and loading of currency and upgrade levels.
    """

    _instance = None
    SAVE_FILE = os.path.join("data", "save", "currency.json")

    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(CurrencyManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the currency manager."""
        self.currency = 0
        self.upgrades = {
            "health": 0,
            "speed": 0,
            "fire_rate": 0,
            "damage": 0,
            "crit_chance": 0,
            "crit_multiplier": 0,
        }
        self.load()
        logger.info("CurrencyManager initialized")

    def add_currency(self, amount):
        """Add currency to the player's total."""
        if amount <= 0:
            logger.warning(f"Invalid currency amount: {amount}")
            return

        self.currency += amount
        logger.debug(f"Added {amount} currency. New total: {self.currency}")
        self.save()

    def spend_currency(self, amount):
        """
        Spend currency if the player has enough.
        Returns True if successful, False otherwise.
        """
        if amount <= 0:
            logger.warning(f"Invalid spend amount: {amount}")
            return False

        if self.currency >= amount:
            self.currency -= amount
            logger.debug(f"Spent {amount} currency. Remaining: {self.currency}")
            self.save()
            return True
        else:
            logger.debug(f"Not enough currency. Required: {amount}, Available: {self.currency}")
            return False

    def get_currency(self):
        """Get the current currency amount."""
        return self.currency

    def upgrade(self, upgrade_type, cost):
        """
        Purchase an upgrade if the player has enough currency.
        Returns True if successful, False otherwise.
        """
        if upgrade_type not in self.upgrades:
            logger.warning(f"Invalid upgrade type: {upgrade_type}")
            return False

        if self.spend_currency(cost):
            self.upgrades[upgrade_type] += 1
            logger.info(f"Upgraded {upgrade_type} to level {self.upgrades[upgrade_type]}")
            self.save()
            return True
        return False

    def get_upgrade_level(self, upgrade_type):
        """Get the current level of an upgrade."""
        if upgrade_type not in self.upgrades:
            logger.warning(f"Invalid upgrade type: {upgrade_type}")
            return 0
        return self.upgrades[upgrade_type]

    def get_upgrades(self):
        """Get all upgrade levels."""
        return self.upgrades

    def save(self):
        """Save currency and upgrades to file."""
        try:
            # Ensure the save directory exists
            os.makedirs(os.path.dirname(self.SAVE_FILE), exist_ok=True)

            data = {"currency": self.currency, "upgrades": self.upgrades}

            with open(self.SAVE_FILE, "w") as f:
                json.dump(data, f)

            logger.debug(f"Currency data saved to {self.SAVE_FILE}")
        except Exception as e:
            logger.error(f"Error saving currency data: {e}")

    def load(self):
        """Load currency and upgrades from file if it exists."""
        try:
            if os.path.exists(self.SAVE_FILE):
                with open(self.SAVE_FILE, "r") as f:
                    data = json.load(f)

                self.currency = data.get("currency", 0)
                self.upgrades = data.get("upgrades", self.upgrades)

                logger.info(f"Loaded currency: {self.currency} and {len(self.upgrades)} upgrades")
            else:
                logger.info("No currency save file found. Starting with defaults.")
        except Exception as e:
            logger.error(f"Error loading currency data: {e}")
