import pygame
from .scene import Scene
from managers import config
from managers.sound_manager import game_sound_manager
from utils.logger import GameLogger

# Get a logger for the options menu
logger = GameLogger.get_logger("options_menu")


class OptionsMenuScene(Scene):
    """Options menu scene for game settings."""

    def __init__(self):
        super().__init__()

        # Track which menu we came from to return properly
        self.previous_scene = "main_menu"

        # Menu sections and options
        self.sections = ["Audio", "Controls", "Display"]
        self.current_section = 0

        # Audio settings
        self.music_volume = game_sound_manager.music_volume
        self.sfx_volume = game_sound_manager.sfx_volume

        # Menu navigation state
        self.selected_option = 0
        self.adjusting_value = False
        self.audio_options = ["Music Volume", "Sound Effects Volume", "Back"]

        # Get screen dimensions from config
        self.screen_width = config.get("screen", "width", default=800)
        self.screen_height = config.get("screen", "height", default=600)

        # Create a semi-transparent overlay (similar to pause menu)
        self.overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 200))  # Black with opacity

        logger.info("Options menu initialized")

    def set_previous_scene(self, scene_name):
        """Set the previous scene to return to."""
        self.previous_scene = scene_name
        logger.debug(f"Previous scene set to: {scene_name}")

    def handle_event(self, event):
        """Handle menu navigation and option adjustment."""
        if event.type == pygame.KEYDOWN:
            if self.adjusting_value:
                self._handle_value_adjustment(event)
            else:
                self._handle_menu_navigation(event)

    def _handle_menu_navigation(self, event):
        """Handle navigation between menu options."""
        if event.key == pygame.K_UP:
            self.selected_option = (self.selected_option - 1) % len(self.audio_options)
            self.play_sound("menu_navigate")
        elif event.key == pygame.K_DOWN:
            self.selected_option = (self.selected_option + 1) % len(self.audio_options)
            self.play_sound("menu_navigate")
        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
            self.play_sound("button_click")
            if self.audio_options[self.selected_option] == "Back":
                # Return to the previous scene
                self.switch_to_scene(self.previous_scene)
            else:
                # Start adjusting the selected value
                self.adjusting_value = True
        elif event.key == pygame.K_ESCAPE:
            # Return to the previous scene
            self.play_sound("button_click")
            self.switch_to_scene(self.previous_scene)

    def _handle_value_adjustment(self, event):
        """Handle adjustment of volume values."""
        option = self.audio_options[self.selected_option]

        if event.key == pygame.K_LEFT:
            if option == "Music Volume":
                self.music_volume = max(0.0, self.music_volume - 0.1)
                game_sound_manager.set_music_volume(self.music_volume)
                # Play a sound to demonstrate the new volume
                self.play_sound("button_click")
            elif option == "Sound Effects Volume":
                self.sfx_volume = max(0.0, self.sfx_volume - 0.1)
                game_sound_manager.set_sfx_volume(self.sfx_volume)
                # Play a sound to demonstrate the new volume
                self.play_sound("button_click")
        elif event.key == pygame.K_RIGHT:
            if option == "Music Volume":
                self.music_volume = min(1.0, self.music_volume + 0.1)
                game_sound_manager.set_music_volume(self.music_volume)
                # Play a sound to demonstrate the new volume
                self.play_sound("button_click")
            elif option == "Sound Effects Volume":
                self.sfx_volume = min(1.0, self.sfx_volume + 0.1)
                game_sound_manager.set_sfx_volume(self.sfx_volume)
                # Play a sound to demonstrate the new volume
                self.play_sound("button_click")
        elif (
            event.key == pygame.K_RETURN
            or event.key == pygame.K_SPACE
            or event.key == pygame.K_ESCAPE
        ):
            # Exit adjustment mode
            self.adjusting_value = False
            self.play_sound("button_click")

    def update(self):
        """Update menu logic. Nothing complex needed here."""
        # Sync with current sound manager values
        self.music_volume = game_sound_manager.music_volume
        self.sfx_volume = game_sound_manager.sfx_volume

    def render(self):
        """Render the options menu."""
        # Apply background or overlay
        self.screen.fill(config.get_color("black"))
        self.screen.blit(self.overlay, (0, 0))

        # Draw title
        title = self.title_font.render("OPTIONS", True, config.get_color("white"))
        title_rect = title.get_rect(center=(self.screen_width // 2, self.screen_height // 6))
        self.screen.blit(title, title_rect)

        # Draw section title
        section_title = self.font.render("AUDIO SETTINGS", True, config.get_color("white"))
        section_rect = section_title.get_rect(
            center=(self.screen_width // 2, self.screen_height // 3)
        )
        self.screen.blit(section_title, section_rect)

        # Draw menu options
        option_y_start = self.screen_height // 2
        option_spacing = 60  # Match spacing with other menus

        for i, option in enumerate(self.audio_options):
            # Use same yellow color as other menus for selection
            color = (
                config.get_color("yellow")
                if i == self.selected_option
                else config.get_color("white")
            )

            # Highlight text when adjusting
            if self.adjusting_value and i == self.selected_option:
                color = config.get_color("green")  # Green when adjusting

            text = self.font.render(option, True, color)

            # Center the Back option, left-align volume controls
            if option == "Back":
                position = (self.screen_width // 2, option_y_start + i * option_spacing)
                text_rect = text.get_rect(center=position)
            else:
                # Position volume controls far to the left with clear spacing from bars
                position = (self.screen_width // 6, option_y_start + i * option_spacing)
                text_rect = text.get_rect(midleft=position)

            self.screen.blit(text, text_rect)

            # Draw value bars for volume options
            if option == "Music Volume":
                # Position volume bar far to the right
                bar_x = self.screen_width // 2 + 50
                self._draw_volume_bar(bar_x, position[1], self.music_volume, color)
            elif option == "Sound Effects Volume":
                # Position volume bar far to the right
                bar_x = self.screen_width // 2 + 50
                self._draw_volume_bar(bar_x, position[1], self.sfx_volume, color)
            elif option == "Back":
                pass  # Do nothing for "Back" option

            # Draw a selection indicator
            if i == self.selected_option:
                # Draw rectangle around selected option (same as other menus)
                pygame.draw.rect(self.screen, color, text_rect.inflate(20, 10), 2)

        # Draw instructions
        if self.adjusting_value:
            instructions = "Left/Right to adjust value, ENTER or ESC to confirm"
        else:
            instructions = "Up/Down to navigate, ENTER to select, ESC to go back"

        instructions_text = self.small_font.render(instructions, True, config.get_color("white"))
        instructions_rect = instructions_text.get_rect(
            center=(self.screen_width // 2, self.screen_height - 50)
        )
        self.screen.blit(instructions_text, instructions_rect)

    def _draw_volume_bar(self, x, y, value, color):
        """Draw a volume bar with the given value."""
        # Bar background
        bar_width = 200
        bar_height = 20
        pygame.draw.rect(
            self.screen,
            config.get_color("dark_gray"),
            (x, y - bar_height // 2, bar_width, bar_height),
        )

        # Bar fill based on value
        fill_width = int(bar_width * value)
        pygame.draw.rect(self.screen, color, (x, y - bar_height // 2, fill_width, bar_height))

        # Volume percentage
        percent_text = self.small_font.render(
            f"{int(value * 100)}%", True, config.get_color("white")
        )
        self.screen.blit(percent_text, (x + bar_width + 10, y - 12))
