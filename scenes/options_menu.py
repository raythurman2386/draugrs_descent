import pygame
from .scene import Scene
from managers import config, game_sound_manager, game_asset_manager
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
        
        # UI theme from config
        self.ui_theme = config.get("ui", "default_theme", default="blue")
        
        # Load UI assets before creating overlay
        self.load_ui_assets()

        # Create a semi-transparent overlay (similar to pause menu)
        overlay_color = config.get("ui", "options_menu", "overlay_color", default=[0, 0, 0, 200])
        self.overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        self.overlay.fill(tuple(overlay_color))  # Black with opacity

        logger.info("Options menu initialized")

    def load_ui_assets(self):
        """Load UI assets for the options menu."""
        logger.debug(f"Loading options menu UI assets with theme: {self.ui_theme}")
        
        # Load the panel and buttons
        self.panel = game_asset_manager.get_ui_element(f"{self.ui_theme}_panel.png", self.ui_theme)
        self.button_normal = game_asset_manager.get_ui_element(f"{self.ui_theme}_button00.png", self.ui_theme)
        self.button_hover = game_asset_manager.get_ui_element(f"{self.ui_theme}_button01.png", self.ui_theme)
        
        # Get slider dimensions from config
        slider_width = config.get("ui", "options_menu", "sliders", "width", default=200)
        slider_height = config.get("ui", "options_menu", "sliders", "height", default=20)
        knob_size = config.get("ui", "options_menu", "sliders", "knob_size", default=30)
        
        # Get slider colors from config
        slider_theme = config.get("ui", "options_menu", "sliders", "track_color", default="blue")
        knob_theme = config.get("ui", "options_menu", "sliders", "knob_color", default="blue")
        
        # Load slider track (using SVG) - specify scale dimensions
        self.slider_back = game_asset_manager.get_svg_ui_element(
            "slide_horizontal_color", 
            slider_theme, 
            scale=(slider_width, slider_height)
        )
        
        # Load slider knob (using SVG) - specify scale dimensions
        self.slider_knob = game_asset_manager.get_svg_ui_element(
            "slide_hangle", 
            knob_theme, 
            scale=(knob_size, knob_size)
        )
        
        # Get panel dimensions from config
        panel_width_ratio = config.get("ui", "options_menu", "panel", "width_ratio", default=0.5)
        panel_height_ratio = config.get("ui", "options_menu", "panel", "height_ratio", default=0.7)
        panel_width = int(self.screen_width * panel_width_ratio)
        panel_height = int(self.screen_height * panel_height_ratio)
        
        # Scale the panel to fit our menu needs
        self.panel = pygame.transform.scale(self.panel, (panel_width, panel_height))
        
        # Calculate panel position
        self.panel_rect = self.panel.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        
        # Get button configuration from config
        button_width_ratio = config.get("ui", "options_menu", "buttons", "width_ratio", default=0.6)
        button_height = config.get("ui", "options_menu", "buttons", "height", default=45)
        self.button_spacing = config.get("ui", "options_menu", "buttons", "spacing", default=60)
        
        # Create the back button
        button_width = int(panel_width * button_width_ratio)
        self.scaled_button_normal = pygame.transform.scale(self.button_normal, (button_width, button_height))
        self.scaled_button_hover = pygame.transform.scale(self.button_hover, (button_width, button_height))
        
        # Calculate back button position (centered at bottom of panel)
        back_button_y = self.panel_rect.bottom - 70  # 70px from bottom of panel
        self.back_button_rect = self.scaled_button_normal.get_rect(
            center=(self.panel_rect.centerx, back_button_y)
        )
        
        # Create slider rects
        self.slider_rects = []
        self.slider_values = [self.music_volume, self.sfx_volume]
        
        # Position sliders - with vertical stacking
        # Start from after the section title with more spacing
        slider_start_y = self.panel_rect.top + 140
        slider_vertical_spacing = 100  # Increased spacing for stacked layout
        
        for i in range(2):  # 2 sliders (music and sfx)
            slider_y = slider_start_y + i * slider_vertical_spacing
            slider_rect = self.slider_back.get_rect(
                center=(self.panel_rect.centerx, slider_y + 50)  # Move slider below label
            )
            self.slider_rects.append(slider_rect)
        
        # Load fonts
        # Map font sizes based on config or defaults
        title_font_size = config.get("ui", "options_menu", "title", "font_size", default=32)
        option_font_size = config.get("ui", "options_menu", "options", "font_size", default=24)
        button_font_size = config.get("ui", "options_menu", "buttons", "font_size", default=24)
        
        # Map numeric font sizes to asset manager's predefined sizes
        title_size_name = "title" if title_font_size >= 36 else "heading"
        option_size_name = "heading" if option_font_size >= 30 else "normal"
        button_size_name = "ui" if button_font_size <= 20 else "normal"
        
        # Get appropriate fonts
        self.title_font = game_asset_manager.get_font("default", title_size_name)
        self.option_font = game_asset_manager.get_font("default", option_size_name)
        self.button_font = game_asset_manager.get_font("default", button_size_name)
        
        # Get a smaller font for instructions
        self.instruction_font = game_asset_manager.get_font("default", "small")
        
        logger.debug(f"Options menu UI assets loaded")

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
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                mouse_pos = pygame.mouse.get_pos()
                
                # Check if back button clicked
                if self.back_button_rect.collidepoint(mouse_pos):
                    self.selected_option = 2  # "Back" option
                    self.select_current_option()
                
                # Check if sliders clicked
                for i, rect in enumerate(self.slider_rects):
                    if rect.collidepoint(mouse_pos):
                        self.selected_option = i
                        self.handle_slider_click(mouse_pos, i)
        
        elif event.type == pygame.MOUSEMOTION:
            # Handle slider dragging
            if event.buttons[0] == 1:  # Left mouse button held down
                mouse_pos = pygame.mouse.get_pos()
                
                # Check if we're adjusting a slider
                if self.adjusting_value and self.selected_option < 2:
                    self.handle_slider_click(mouse_pos, self.selected_option)

    def handle_slider_click(self, mouse_pos, slider_index):
        """Handle clicking or dragging on a slider."""
        rect = self.slider_rects[slider_index]
        
        # Calculate relative position (0.0 to 1.0)
        rel_x = (mouse_pos[0] - rect.left) / rect.width
        rel_x = max(0.0, min(1.0, rel_x))  # Clamp between 0 and 1
        
        if slider_index == 0:  # Music volume
            self.music_volume = rel_x
            game_sound_manager.set_music_volume(self.music_volume)
            self.play_sound("button_click")
        elif slider_index == 1:  # SFX volume
            self.sfx_volume = rel_x
            game_sound_manager.set_sfx_volume(self.sfx_volume)
            self.play_sound("button_click")
            
        # Update slider values array
        self.slider_values[slider_index] = rel_x
        
        # Enable adjusting mode
        self.adjusting_value = True

    def _handle_menu_navigation(self, event):
        """Handle navigation between menu options."""
        if event.key == pygame.K_UP:
            self.selected_option = (self.selected_option - 1) % len(self.audio_options)
            self.play_sound("menu_navigate")
        elif event.key == pygame.K_DOWN:
            self.selected_option = (self.selected_option + 1) % len(self.audio_options)
            self.play_sound("menu_navigate")
        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
            self.select_current_option()
        elif event.key == pygame.K_ESCAPE:
            # Return to the previous scene
            self.play_sound("button_click")
            self.switch_to_scene(self.previous_scene)

    def select_current_option(self):
        """Handle selection of the current option."""
        self.play_sound("button_click")
        if self.audio_options[self.selected_option] == "Back":
            # Return to the previous scene
            self.switch_to_scene(self.previous_scene)
        else:
            # Start adjusting the selected value
            self.adjusting_value = True

    def _handle_value_adjustment(self, event):
        """Handle adjustment of volume values."""
        option = self.audio_options[self.selected_option]

        if event.key == pygame.K_LEFT:
            if option == "Music Volume":
                self.music_volume = max(0.0, self.music_volume - 0.1)
                game_sound_manager.set_music_volume(self.music_volume)
                # Update slider values array
                self.slider_values[0] = self.music_volume
                # Play a sound to demonstrate the new volume
                self.play_sound("button_click")
            elif option == "Sound Effects Volume":
                self.sfx_volume = max(0.0, self.sfx_volume - 0.1)
                game_sound_manager.set_sfx_volume(self.sfx_volume)
                # Update slider values array
                self.slider_values[1] = self.sfx_volume
                # Play a sound to demonstrate the new volume
                self.play_sound("button_click")
        elif event.key == pygame.K_RIGHT:
            if option == "Music Volume":
                self.music_volume = min(1.0, self.music_volume + 0.1)
                game_sound_manager.set_music_volume(self.music_volume)
                # Update slider values array
                self.slider_values[0] = self.music_volume
                # Play a sound to demonstrate the new volume
                self.play_sound("button_click")
            elif option == "Sound Effects Volume":
                self.sfx_volume = min(1.0, self.sfx_volume + 0.1)
                game_sound_manager.set_sfx_volume(self.sfx_volume)
                # Update slider values array
                self.slider_values[1] = self.sfx_volume
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
        """Update menu logic."""
        # Sync with current sound manager values
        self.music_volume = game_sound_manager.music_volume
        self.sfx_volume = game_sound_manager.sfx_volume
        
        # Keep slider values array in sync
        self.slider_values[0] = self.music_volume
        self.slider_values[1] = self.sfx_volume

    def render(self):
        """Render the options menu."""
        # Apply background or overlay
        self.screen.fill(config.get_color("black"))
        self.screen.blit(self.overlay, (0, 0))
        
        # Draw the panel background
        self.screen.blit(self.panel, self.panel_rect)

        # Draw title
        title_text = "OPTIONS"
        title_color = config.get("ui", "options_menu", "title", "color", default="white")
        title = self.title_font.render(title_text, True, config.get_color(title_color))
        title_rect = title.get_rect(center=(self.screen_width // 2, self.panel_rect.top + 40))
        self.screen.blit(title, title_rect)

        # Draw section title
        section_title = "AUDIO SETTINGS"
        section_color = config.get("ui", "options_menu", "sections", "audio", "color", default="white")
        section = self.option_font.render(section_title, True, config.get_color(section_color))
        section_rect = section.get_rect(
            center=(self.screen_width // 2, self.panel_rect.top + 100)
        )
        self.screen.blit(section, section_rect)

        # Draw volume labels and sliders - with vertical stacking
        option_names = ["MUSIC VOLUME", "SOUND EFFECTS VOLUME"]
        
        # Calculate starting position and spacing for stacked layout
        start_y = self.panel_rect.top + 140
        vertical_spacing = 100
        
        for i in range(2):
            option_text = option_names[i]
            
            # Determine text color based on selection
            if i == self.selected_option:
                if self.adjusting_value:
                    color = config.get_color("green")  # Green when adjusting
                else:
                    color = config.get_color("yellow")  # Yellow when selected
            else:
                color = config.get_color("white")  # White for unselected

            # Position the option text (centered above the slider)
            y_position = start_y + i * vertical_spacing
            label = self.option_font.render(option_text, True, color)
            label_rect = label.get_rect(center=(self.panel_rect.centerx, y_position))
            self.screen.blit(label, label_rect)

            # Draw slider track (below the label)
            rect = self.slider_rects[i]
            self.screen.blit(self.slider_back, rect)
            
            # Draw knob at correct position based on value
            knob_x = rect.left + int(self.slider_values[i] * rect.width)
            knob_rect = self.slider_knob.get_rect(center=(knob_x, rect.centery))
            self.screen.blit(self.slider_knob, knob_rect)
            
            # Draw percentage text (to the right of the slider)
            percentage = f"{int(self.slider_values[i] * 100)}%"
            percent_text = self.button_font.render(percentage, True, color)
            percent_rect = percent_text.get_rect(midleft=(rect.right + 15, rect.centery))
            self.screen.blit(percent_text, percent_rect)

        # Draw the Back button
        back_button_index = 2  # "Back" is the 3rd option (index 2)
        selected = self.selected_option == back_button_index
        
        # Choose button image based on selection
        button_img = self.scaled_button_hover if selected else self.scaled_button_normal
        self.screen.blit(button_img, self.back_button_rect)
        
        # Choose text color based on selection
        button_text_color = config.get_color("yellow") if selected else config.get_color("white")
        back_text = self.button_font.render("BACK", True, button_text_color)
        back_text_rect = back_text.get_rect(center=self.back_button_rect.center)
        self.screen.blit(back_text, back_text_rect)
        
        # Draw instructions at the bottom with smaller font
        instruction_text = "Arrow keys to navigate, ENTER to select, ESC to return"
        if self.adjusting_value:
            instruction_text = "LEFT/RIGHT to adjust, ENTER to confirm"
            
        instructions = self.instruction_font.render(instruction_text, True, config.get_color("white"))
        instructions_rect = instructions.get_rect(center=(self.screen_width // 2, self.screen_height - 20))
        self.screen.blit(instructions, instructions_rect)
