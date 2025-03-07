from enum import Enum, auto
from typing import Dict, Optional, Callable, Any


class GameState(Enum):
    """Enumeration of possible game states."""

    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    LOADING = auto()


class GameStateManager:
    """Manages game states and transitions between them."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GameStateManager, cls).__new__(cls)
            cls._instance._init_manager()
        return cls._instance

    def _init_manager(self) -> None:
        """Initialize the state manager."""
        self.current_state = GameState.MENU
        self.previous_state = None
        self._state_handlers: Dict[GameState, Callable] = {}
        self._state_data: Dict[GameState, Any] = {}
        self._transition_handlers: Dict[tuple[GameState, GameState], Callable] = {}

    def register_state_handler(self, state: GameState, handler: Callable) -> None:
        """
        Register a handler function for a game state.

        Args:
            state: The game state to handle
            handler: Function to call when in this state
        """
        self._state_handlers[state] = handler

    def register_transition_handler(
        self, from_state: GameState, to_state: GameState, handler: Callable
    ) -> None:
        """
        Register a handler for state transitions.

        Args:
            from_state: Starting state
            to_state: Ending state
            handler: Function to call during transition
        """
        self._transition_handlers[(from_state, to_state)] = handler

    def set_state_data(self, state: GameState, data: Any) -> None:
        """
        Set data associated with a game state.

        Args:
            state: The game state to store data for
            data: The data to store
        """
        self._state_data[state] = data

    def get_state_data(self, state: GameState) -> Optional[Any]:
        """
        Get data associated with a game state.

        Args:
            state: The game state to get data for

        Returns:
            The stored data or None if no data exists
        """
        return self._state_data.get(state)

    def change_state(self, new_state: GameState) -> None:
        """
        Change to a new game state.

        Args:
            new_state: The state to change to
        """
        if new_state == self.current_state:
            return

        # Store previous state
        self.previous_state = self.current_state

        # Handle transition if handler exists
        transition_key = (self.current_state, new_state)
        if transition_key in self._transition_handlers:
            self._transition_handlers[transition_key]()

        # Update current state
        self.current_state = new_state

        # Call new state's handler if it exists
        if new_state in self._state_handlers:
            self._state_handlers[new_state]()

    def update(self) -> None:
        """Update the current state."""
        if self.current_state in self._state_handlers:
            self._state_handlers[self.current_state]()

    def is_state(self, state: GameState) -> bool:
        """Check if the current state matches the given state."""
        return self.current_state == state

    def get_current_state(self) -> GameState:
        """Get the current game state."""
        return self.current_state

    def get_previous_state(self) -> Optional[GameState]:
        """Get the previous game state."""
        return self.previous_state


# Global state manager instance
game_state = GameStateManager()
