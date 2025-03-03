import pytest
import pygame
import os
from unittest.mock import patch, MagicMock, call
from managers.sound_manager import SoundManager


class TestSoundManager:
    """Test cases for the game's sound management system."""

    @pytest.fixture
    def mock_mixer(self):
        """Fixture to create mocked pygame.mixer for testing sound functionality."""
        with patch("pygame.mixer") as mock_mixer:
            # Mock the Sound class
            mock_sound = MagicMock()
            mock_mixer.Sound.return_value = mock_sound
            
            # Setup music module mock
            mock_mixer.music = MagicMock()
            
            yield mock_mixer
    
    @pytest.fixture
    def sound_manager_with_mocks(self, mock_mixer):
        """Fixture to create a sound manager with mocked dependencies."""
        with patch("os.path.exists", return_value=True):
            # Use a patched logger to avoid actual logging during tests
            with patch("utils.logger.GameLogger.get_logger") as mock_logger:
                mock_logger_instance = MagicMock()
                mock_logger.return_value = mock_logger_instance
                
                sound_manager = SoundManager()
                
                # Override the initialized flag since we're using mocks
                sound_manager.initialized = True
                
                yield sound_manager

    def test_initialization(self, mock_mixer):
        """Test that the sound manager initializes correctly."""
        # Test successful initialization
        with patch("os.path.exists", return_value=True):
            with patch("utils.logger.GameLogger.get_logger"):
                sound_manager = SoundManager()
                assert sound_manager.initialized is True
                assert sound_manager.music_volume == 0.5
                assert sound_manager.sfx_volume == 0.7
                mock_mixer.init.assert_called_once()
    
    def test_initialization_failure(self):
        """Test that the sound manager handles initialization failures gracefully."""
        with patch("pygame.mixer.init", side_effect=Exception("Mock initialization error")):
            with patch("utils.logger.GameLogger.get_logger"):
                sound_manager = SoundManager()
                assert sound_manager.initialized is False
    
    def test_load_sound_effects(self, mock_mixer):
        """Test loading sound effects."""
        with patch("os.path.exists", return_value=True):
            with patch("utils.logger.GameLogger.get_logger"):
                sound_manager = SoundManager()
                
                # Check that Sound was called for each sound effect
                expected_calls = [
                    call(os.path.join(SoundManager.SFX_PATH, filename)) 
                    for filename in SoundManager.SOUND_EFFECTS.values()
                ]
                mock_mixer.Sound.assert_has_calls(expected_calls, any_order=True)
                
                # Check that all sounds were loaded
                assert len(sound_manager.sounds) == len(SoundManager.SOUND_EFFECTS)
    
    def test_play_music(self, sound_manager_with_mocks, mock_mixer):
        """Test playing music for a scene."""
        sound_manager = sound_manager_with_mocks
        
        # Test playing music for a valid scene
        sound_manager.play_music("main_menu")
        
        # Check that the appropriate methods were called
        mock_mixer.music.stop.assert_called_once()
        mock_mixer.music.load.assert_called_once()
        mock_mixer.music.set_volume.assert_called_once_with(0.5)  # Default volume
        mock_mixer.music.play.assert_called_once_with(-1)  # Loop indefinitely
        
        # Check that current_music was updated
        assert sound_manager.current_music is not None
        
        # Test playing the same music again (should not reload)
        mock_mixer.reset_mock()
        sound_manager.play_music("main_menu")
        mock_mixer.music.load.assert_not_called()
        
        # Test playing different music
        mock_mixer.reset_mock()
        sound_manager.play_music("game")
        mock_mixer.music.load.assert_called_once()
    
    def test_stop_music(self, sound_manager_with_mocks, mock_mixer):
        """Test stopping music."""
        sound_manager = sound_manager_with_mocks
        
        # First play some music
        sound_manager.play_music("main_menu")
        assert sound_manager.current_music is not None
        
        # Now stop it
        mock_mixer.reset_mock()
        sound_manager.stop_music()
        
        # Check that stop was called and current_music was reset
        mock_mixer.music.stop.assert_called_once()
        assert sound_manager.current_music is None
    
    def test_play_sound(self, sound_manager_with_mocks, mock_mixer):
        """Test playing sound effects."""
        sound_manager = sound_manager_with_mocks
        mock_sound = MagicMock()
        
        # Add a mock sound to the sound manager
        sound_manager.sounds["test_sound"] = mock_sound
        
        # Test playing a valid sound
        sound_manager.play_sound("test_sound")
        mock_sound.set_volume.assert_called_once_with(sound_manager.sfx_volume)
        mock_sound.play.assert_called_once()
        
        # Test playing an invalid sound
        sound_manager.play_sound("nonexistent_sound")  # Should not raise an error
    
    def test_volume_control(self, sound_manager_with_mocks, mock_mixer):
        """Test volume control methods."""
        sound_manager = sound_manager_with_mocks
        
        # Test setting music volume
        sound_manager.set_music_volume(0.75)
        assert sound_manager.music_volume == 0.75
        mock_mixer.music.set_volume.assert_called_once_with(0.75)
        
        # Test setting sfx volume
        sound_manager.set_sfx_volume(0.3)
        assert sound_manager.sfx_volume == 0.3
        
        # Test volume limits (should clamp between 0 and 1)
        sound_manager.set_music_volume(1.5)
        assert sound_manager.music_volume == 1.0
        sound_manager.set_music_volume(-0.5)
        assert sound_manager.music_volume == 0.0
    
    def test_pause_unpause_music(self, sound_manager_with_mocks, mock_mixer):
        """Test pausing and unpausing music."""
        sound_manager = sound_manager_with_mocks
        
        # Test pausing
        sound_manager.pause_music()
        mock_mixer.music.pause.assert_called_once()
        
        # Test unpausing
        mock_mixer.reset_mock()
        sound_manager.unpause_music()
        mock_mixer.music.unpause.assert_called_once()
    
    def test_error_handling(self, sound_manager_with_mocks, mock_mixer):
        """Test error handling in various methods."""
        sound_manager = sound_manager_with_mocks
        
        # Test error in play_music
        mock_mixer.music.load.side_effect = Exception("Mock error")
        sound_manager.play_music("game")  # Should not raise an exception
        
        # Test error in stop_music
        mock_mixer.reset_mock()
        mock_mixer.music.stop.side_effect = Exception("Mock error")
        sound_manager.stop_music()  # Should not raise an exception
        
        # Test error in pause_music
        mock_mixer.reset_mock()
        mock_mixer.music.pause.side_effect = Exception("Mock error")
        sound_manager.pause_music()  # Should not raise an exception
        
        # Test error in unpause_music
        mock_mixer.reset_mock()
        mock_mixer.music.unpause.side_effect = Exception("Mock error")
        sound_manager.unpause_music()  # Should not raise an exception 