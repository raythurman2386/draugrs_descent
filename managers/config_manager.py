from pathlib import Path
import yaml
from typing import Any, Dict, Optional, Tuple


class ConfigManager:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._config = {}
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        config_path = Path(__file__).parent.parent / "config" / "game_config.yaml"
        try:
            with open(config_path, "r") as config_file:
                self._config = yaml.safe_load(config_file)
            print(f"Config loaded successfully from {config_path}")
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self._config = {}

    def debug_print_config(self) -> None:
        """Print the loaded configuration for debugging."""
        print("\n=== CONFIG CONTENTS ===")
        print(f"Config data: {self._config}")
        print("=== END CONFIG ===\n")

    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            *keys: Variable number of keys to access nested config values
            default: Default value if key doesn't exist

        Returns:
            Configuration value or default if not found

        Example:
            config.get("screen", "width")  # returns 800
            config.get("player", "attributes", "max_health")  # returns 100
        """
        current = self._config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen width and height as a tuple."""
        return (self.get("screen", "width", default=800), self.get("screen", "height", default=600))

    def get_color(self, color_name: str) -> Tuple[int, int, int]:
        """Get RGB color tuple by name."""
        color = self.get("colors", color_name)
        if not color or not isinstance(color, list) or len(color) != 3:
            # Check if it's a powerup type
            powerup_color = self.get("powerups", "colors", color_name)
            if powerup_color and isinstance(powerup_color, list) and len(powerup_color) == 3:
                return tuple(powerup_color)

            # Provide hardcoded defaults for common colors
            defaults = {
                "black": (0, 0, 0),
                "white": (255, 255, 255),
                "red": (255, 0, 0),
                "green": (0, 255, 0),
                "blue": (0, 0, 255),
                "yellow": (255, 255, 0),
                "health": (0, 255, 0),  # Green for health powerups
                "shield": (0, 0, 255),  # Blue for shield powerups
                "speed": (255, 255, 0),  # Yellow for speed powerups
                "weapon": (255, 0, 255),  # Purple for weapon powerups
            }
            return defaults.get(color_name.lower(), (0, 0, 0))  # Default to black
        return tuple(color)

    def get_asset_path(self, asset_type: str, asset_name: str) -> str:
        """
        Get the full path for an asset.

        Args:
            asset_type: Type of asset ("images", "sounds", "fonts")
            asset_name: Name of the specific asset

        Returns:
            Full path to the asset
        """
        base_path = self.get("assets", asset_type, "path", default=f"assets/{asset_type}")
        return str(Path(base_path) / asset_name)


# Global configuration instance
config = ConfigManager()
