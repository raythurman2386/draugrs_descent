# Draugr's Descent

A top-down arcade-style shooter where you battle against hordes of enemies in an unforgiving dungeon environment.

## Game Overview

In Draugr's Descent, you control a hero fighting against waves of relentless enemies. Move strategically, aim carefully, and survive as long as possible against the ever-increasing onslaught.

### Features

- Fast-paced arcade-style gameplay
- Automatic targeting and shooting mechanics
- Scene management system with menu, pause, and game over screens
- Progressively challenging enemy spawns
- Detailed in-game statistics tracking

## Installation

### Requirements

- Python 3.x
- Pygame 2.x

### Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/draugrs_descent.git
   cd draugrs_descent
   ```

2. Create and activate a virtual environment (recommended):
   ```
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the game:
   ```
   python main.py
   ```

## How to Play

### Controls

- **Arrow Keys**: Move the player character
- **ESC**: Pause game
- **Enter/Space**: Select menu option

### Debug Controls

- **F1**: Set logging to DEBUG level
- **F2**: Set logging to INFO level
- **F3**: Set logging to WARNING level

### Gameplay Mechanics

- Move to aim and shoot automatically at the closest enemy
- Avoid contact with enemies, as they will damage you on collision
- Projectiles will automatically target the nearest enemy
- Try to survive as long as possible and defeat as many enemies as you can

## Development

The game is built using Python and Pygame with a structured object-oriented architecture:

- **Scene Management**: Modular scene system for menu, gameplay, and game over screens
- **Entity Management**: Sprite-based entity system for player, enemies, and projectiles
- **Collision System**: Pixel-perfect collision detection
- **Logging System**: Comprehensive debug logging system with multiple verbosity levels

## Credits

Developed by: [Your Name]

## License

[Specify Your License Here - e.g., MIT, GPL, etc.]
