# Draugr's Descent Development Roadmap

This document outlines the planned development path for Draugr's Descent, organized by priority and timeline.

## Short-term Goals (1-2 months)

### Gameplay Improvements
- [x] Add different enemy types with unique behaviors (chargers, ranged attackers, etc.)
- [ ] Implement player character upgrades (increased health, speed, fire rate)
- [x] Create a basic item/power-up system (health pack, shield, weapon boost)
- [x] Add a scoring system with high scores table

### Visual Enhancements
- [ ] Replace placeholder graphics with proper sprites
- [ ] Add animations for player, enemies, and projectiles
- [ ] Implement basic particle effects (explosions, damage indicators)
- [ ] Add screen shake and visual feedback

### Audio
- [x] Add background music for different scenes
- [x] Implement sound effects for player actions, enemies, and collisions
- [x] Create audio settings menu

### Technical Improvements
- [ ] Optimize collision detection for improved performance
- [x] Add configuration file for game settings
- [ ] Create a proper installation package

## Mid-term Goals (3-6 months)

### Gameplay Expansion
- [ ] Create multiple game levels/environments
- [ ] Implement boss enemies with complex patterns
- [ ] Add weapon variety with different projectile behaviors
- [ ] Design an upgrade/progression system
- [ ] Implement multiple game modes (Endless and Story)
  - **Endless Mode**:
    - Wave-based progression with increasing difficulty
    - Boss waves every 5-10 regular waves
    - Dynamic enemy spawning and scaling
    - High score system for longest survival
  - **Story Mode**:
    - Level-based progression with distinct environments
    - Narrative elements between levels
    - Unique boss encounters
    - Unlockable content through progression

### Game Modes Implementation Details

#### Endless Mode Architecture
- Create a `WaveManager` class to handle:
  - Progressive wave difficulty
  - Enemy count scaling
  - Spawn rate adjustment
  - Boss wave integration
- Required components:
  - New `managers/wave_manager.py` file
  - UI elements for wave indicators
  - Wave transition effects
  - Dynamic difficulty scaling

#### Story Mode Architecture
- Create a `LevelManager` to handle:
  - Level configurations and loading
  - Progress tracking
  - Environment transitions
  - Narrative sequences
- Required components:
  - New `managers/level_manager.py` file
  - Level data files (JSON/YAML)
  - Cutscene system
  - Level selection interface
  - Save/load functionality for progress

#### Required File Structure Changes
```
draugrs_descent/
├── scenes/
│   ├── game_modes/
│   │   ├── endless_scene.py
│   │   ├── level_scene.py
│   │   ├── cutscene_scene.py
│   │   └── level_select_scene.py
├── managers/
│   ├── wave_manager.py
│   └── level_manager.py
├── data/
│   ├── levels/
│   │   ├── level1.json
│   │   └── level2.json
│   └── story/
│       └── cutscenes.json
```

### Features
- [ ] Create a tutorial level
- [ ] Implement difficulty settings
- [ ] Add controller support
- [ ] Create a proper settings menu with customizable controls
- [ ] Add achievements system

### Technical
- [ ] Implement save/load system
- [ ] Add telemetry for gameplay analytics
- [ ] Optimize for different screen resolutions

## Long-term Goals (6+ months)

### Major Features
- [ ] Create a story mode with narrative elements
- [ ] Implement a procedural level generation system
- [ ] Add multiplayer cooperative gameplay
- [ ] Design a character/class selection system

### Technical Evolution
- [ ] Port to other platforms (mobile, consoles)
- [ ] Create a level editor for custom content
- [ ] Implement online leaderboards
- [ ] Add mod support

### Community
- [ ] Set up a community forum
- [ ] Create documentation for modding
- [ ] Establish regular update schedule

## Backlog (Ideas for Future Consideration)

- [ ] PvP battle mode
- [ ] Daily/weekly challenges
- [ ] Seasonal events
- [ ] Meta-progression between game sessions
- [ ] Alternative game modes (survival, time attack, etc.)
- [ ] Interactive environments with destructible elements
- [ ] Stealth mechanics
- [ ] Endless Mode enhancements:
  - Special wave types (speed waves, elite waves, horde waves)
  - Environment changes every X waves
  - Random events and mutators between waves
  - Prestige system with permanent upgrades
  - Challenge modes with special rules
- [ ] Story Mode enhancements:
  - Side quests and optional objectives
  - Multiple story paths and endings
  - Character customization with visual effects
  - NPC allies with unique abilities
  - Environmental puzzles and interactive elements

## Release Plan

### v0.1 - Current Prototype
- Basic gameplay loop with placeholder graphics
- Scene management system
- Logging and debug features

### v0.2 - Enhanced Prototype
- Improved graphics
- Basic sound effects
- Multiple enemy types

### v0.3 - Alpha Release
- Complete core gameplay
- Progression system
- Basic UI and menus

### v0.4 - Game Modes Prototype
- Endless Mode with wave system
- Initial Story Mode framework
- Boss enemy prototypes
- Save/load system for game progress

### v0.5 - Game Modes Alpha
- Refined Endless Mode with full wave scaling
- Expanded Story Mode with multiple levels
- Complete boss battle system
- Enhanced UI for game mode selection

### v1.0 - Full Release
- Complete feature set
- Polished visuals and audio
- Tutorial and documentation
- Balanced gameplay across all modes

## Contribution Guidelines

If you're interested in contributing to Draugr's Descent, please check the following:

1. Review the open issues in our issue tracker
2. For new features, create a proposal issue first
3. Follow the code style guidelines in our documentation
4. Submit pull requests against the development branch 