import pygame
import os
from utils.logger import GameLogger

# Get a logger for the sound manager
logger = GameLogger.get_logger("sound")


class SoundManager:
    """Manages game sounds and music."""

    # Paths to audio files
    AUDIO_PATH = "assets/audio"
    SCENE_AUDIO_PATH = os.path.join(AUDIO_PATH, "scene_audio")
    SFX_PATH = AUDIO_PATH

    # Scene music mapping
    SCENE_MUSIC = {
        "main_menu": "main_menu.ogg",
        "game": "game_music.ogg",
        "pause": "pause_menu.ogg",
        "game_over": "game_over.ogg",
    }

    # Sound effect mapping
    SOUND_EFFECTS = {
        "player_hit": "hurt2.ogg",
        "enemy_hit": "hit3.ogg",
        "powerup_collect": "pickup1.ogg",
        "button_click": "click1.ogg",
        "game_lost": "gamelost.ogg",
        "menu_navigate": "switch1.ogg",
        "wave_start": "pickup2.ogg",
        "wave_complete": "pickup3.ogg",
        "boss_wave_start": "pickup4.ogg",
        "boss_encounter": "pickup5.ogg",
    }

    def __init__(self):
        """Initialize the sound manager."""
        self.initialized = False
        self.current_music = None
        self.sounds = {}
        self.music_volume = 0.5
        self.sfx_volume = 0.7

        # Initialize mixer
        try:
            pygame.mixer.init()
            self.initialized = True
            logger.info("Sound manager initialized successfully")
            self._load_sound_effects()
        except Exception as e:
            logger.error(f"Failed to initialize sound manager: {e}")

    def _load_sound_effects(self):
        """Load all sound effects into memory."""
        if not self.initialized:
            return

        try:
            for name, filename in self.SOUND_EFFECTS.items():
                filepath = os.path.join(self.SFX_PATH, filename)
                if os.path.exists(filepath):
                    self.sounds[name] = pygame.mixer.Sound(filepath)
                    logger.debug(f"Loaded sound effect: {name}")
                else:
                    logger.warning(f"Sound effect file not found: {filepath}")
        except Exception as e:
            logger.error(f"Error loading sound effects: {e}")

    def play_music(self, scene_key):
        """Play music for a specific scene."""
        if not self.initialized:
            return

        if scene_key in self.SCENE_MUSIC:
            music_file = os.path.join(self.SCENE_AUDIO_PATH, self.SCENE_MUSIC[scene_key])

            # Only change music if it's different from what's currently playing
            if self.current_music != music_file:
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(music_file)
                    pygame.mixer.music.set_volume(self.music_volume)
                    pygame.mixer.music.play(-1)  # Loop indefinitely
                    self.current_music = music_file
                    logger.info(f"Playing music for scene: {scene_key}")
                except Exception as e:
                    logger.error(f"Error playing music for scene {scene_key}: {e}")

    def stop_music(self):
        """Stop the currently playing music."""
        if not self.initialized:
            return

        try:
            pygame.mixer.music.stop()
            self.current_music = None
            logger.info("Music stopped")
        except Exception as e:
            logger.error(f"Error stopping music: {e}")

    def play_sound(self, sound_name):
        """Play a sound effect."""
        if not self.initialized:
            return

        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].set_volume(self.sfx_volume)
                self.sounds[sound_name].play()
                logger.debug(f"Playing sound effect: {sound_name}")
            except Exception as e:
                logger.error(f"Error playing sound effect {sound_name}: {e}")
        else:
            logger.warning(f"Sound effect not found: {sound_name}")

    def set_music_volume(self, volume):
        """Set the music volume (0.0 to 1.0)."""
        if not self.initialized:
            return

        self.music_volume = max(0.0, min(1.0, volume))
        try:
            pygame.mixer.music.set_volume(self.music_volume)
            logger.info(f"Music volume set to {self.music_volume}")
        except Exception as e:
            logger.error(f"Error setting music volume: {e}")

    def set_sfx_volume(self, volume):
        """Set the sound effects volume (0.0 to 1.0)."""
        if not self.initialized:
            return

        self.sfx_volume = max(0.0, min(1.0, volume))
        logger.info(f"SFX volume set to {self.sfx_volume}")

    def pause_music(self):
        """Pause the currently playing music."""
        if not self.initialized:
            return

        try:
            pygame.mixer.music.pause()
            logger.info("Music paused")
        except Exception as e:
            logger.error(f"Error pausing music: {e}")

    def unpause_music(self):
        """Unpause the currently playing music."""
        if not self.initialized:
            return

        try:
            pygame.mixer.music.unpause()
            logger.info("Music unpaused")
        except Exception as e:
            logger.error(f"Error unpausing music: {e}")


# Create a global instance of the sound manager
game_sound_manager = SoundManager()
