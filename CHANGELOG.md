# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Scene management system with main menu, game, pause, and game over scenes
- Basic player movement and controls
- Enemy spawning system
- Automatic projectile targeting system
- Collision detection
- Health tracking
- Logging system with configurable verbosity
- Enemy and projectile tracking with unique IDs
- Game stats (enemies killed, time survived)
- Project documentation (README, ROADMAP)
- GitHub workflows for code formatting and testing
- Issue and PR templates
- Contributing guidelines
- Asset Manager for improved resource management
- Options Menu for audio settings (music and sound effects volume)
- Different enemy types with unique behaviors (chargers, ranged attackers)
- UI assets in place and working
- Initial sprites and placeholder map in place
- Particle effects system for projectile hits, enemy deaths, and powerup collection
- Screen shake effect when player takes damage
- Unit tests for particle system to ensure proper behavior
- Wave management system for Endless Mode with dynamic difficulty scaling
- Enemy attribute scaling based on wave progression
- Wave transition UI with announcements for upcoming waves
- Boss wave mechanics with enhanced enemy attributes
- Wave information display in game HUD showing current wave and remaining enemies
- Comprehensive unit and integration tests for wave system functionality
- Enemy movement enhancement
- Player upgrade system with permanent stat improvements
- Currency system for collecting and spending souls
- Upgrade menu for purchasing player upgrades
- Enemy currency drops when defeated

### Changed
- Refactored monolithic game class into scene-based architecture
- Improved projectile system with proper map boundary checking
- Enhanced player shooting mechanism with configurable shooting range
- Fixed enemy spawning to use map dimensions instead of hardcoded screen values
- Added safeguards to prevent shot cooldown issues during long gameplay sessions
- Improved sound effect logic for player shooting
- Improved configuration access for screen dimensions and colors

### Fixed
- Projectile issues where projectiles weren't appearing on screen

## [0.9.0] - In Development

### Added
- Wave management system to handle enemy spawning and difficulty progression
- Enhanced collision detection between players and enemies
- Separation behavior for enemies to prevent bunching up during movement
- Wave transition UI elements and effects

### Fixed
- Corrected collision test to ensure proper damage application
- Fixed wave transition timer issues in the game scene
- Improved score display by using the correct property name

## [0.1.0] - 2025-03-02

### Added
- Initial project setup
- Basic game loop
- Player character with movement
- Simple enemies
- Initial collision detection 
- Unit and Integration tests
- Global Sound Manager for all sound states
- Initial assets including scene music and some menu and other sound effects
- Fonts and other assets from [KennyNL](https://kenney.nl/)