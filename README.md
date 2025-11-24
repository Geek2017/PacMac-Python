# PacMac

A competitive twist on the classic Pac-Man arcade game, where you navigate a maze while dodging tech company logos turned into ghosts. Collect pellets, activate power-ups, and strategically hunt down your competitors!

## Features

- **Classic Maze Navigation**: Smooth movement controls with collision detection
- **Power Pellet System**: Strategic power-up mechanics that temporarily turn the tables
- **Dynamic Ghost AI**: Four autonomous ghost enemies with randomized pathfinding
- **Score Tracking**: Points system rewarding both pellet collection and ghost elimination
- **Animated Sprites**: Pac-Man mouth animation and ghost edibility visual feedback
- **Game State Management**: Win/loss conditions with restart functionality

## Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Setup

1. Clone or download this repository:
   ```bash
   git clone <repository-url>
   cd PacMac-Python
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## How to Play

### Starting the Game
```bash
python main.py
```

### Controls
- **Arrow Keys**: Move Pac-Man in four directions (up, down, left, right)
- **R Key**: Restart game after game over or victory

### Gameplay Mechanics

#### Objective
Collect all white pellets scattered throughout the maze while avoiding ghost enemies.

#### Scoring System
- **Regular Pellets**: +1 point each
- **Power Pellets** (red squares): +5 points each
- **Ghosts** (during power mode): +10 points each

#### Power Mode
- Collect red power pellets to activate temporary invincibility (10 seconds)
- During power mode, ghosts become edible and turn blue
- Strategic use of power pellets is key to clearing the board and maximizing score

#### Win Condition
Collect all pellets and power pellets on the board

#### Lose Condition
Collide with a ghost while NOT in power mode

### Game Strategy Tips

1. **Power Pellet Positioning**: Power pellets spawn near the top of the maze - plan your route accordingly
2. **Ghost Patterns**: Ghosts follow random pathfinding - use the maze walls to your advantage
3. **Timing is Everything**: Save power pellets for when you're surrounded or need to clear an area
4. **Corner Traps**: Be cautious in narrow passages where ghosts can corner you
5. **Score Maximization**: Try to eat multiple ghosts during a single power mode activation

## Technical Details

### Architecture
- Built with Pygame for 2D rendering and game loop management
- Object-oriented design with sprite-based entities
- Collision detection using Pygame's sprite collision system
- Frame-rate independent game logic running at 60 FPS

### File Structure
```
PacMac-Python/
├── main.py              # Main game logic and entry point
├── imgs/                # Ghost sprite images
│   ├── ghl.png
│   ├── kajabi.png
│   ├── sk.png
│   └── sys.png
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

### Key Classes
- **Player**: Pac-Man entity with movement, collision, and animation
- **Ghost**: Enemy AI with autonomous pathfinding and edibility states
- **Pellet**: Collectible point items
- **PowerPellet**: Special collectibles that activate power mode
- **Wall**: Maze boundary collision objects

## Development

### Customization Options

You can easily modify game parameters in `main.py`:

- **Screen dimensions**: `SCREEN_WIDTH`, `SCREEN_HEIGHT`
- **Player speed**: Modify values in `player.changespeed()` calls
- **Ghost speed**: Adjust `self.speed` in Ghost class
- **Power mode duration**: Change `power_timer = 600` (frames at 60 FPS)
- **Maze layout**: Edit `wall_coords` array

### Adding New Features

Some ideas for extending the game:
- Multiple levels with increasing difficulty
- Different ghost AI personalities (chaser, ambusher, random)
- Bonus fruit items for extra points
- Sound effects and background music
- High score persistence
- Different maze layouts

## Troubleshooting

### Common Issues

**Game window doesn't appear**
- Ensure Pygame is properly installed: `pip install --upgrade pygame`
- Check Python version compatibility (3.7+)

**Ghosts appear stuck**
- The game includes anti-stuck logic with automatic teleportation after 60 frames
- If persistent, check maze layout for unreachable areas

**Performance issues**
- Reduce screen resolution by modifying `SCREEN_WIDTH` and `SCREEN_HEIGHT`
- Ensure no other heavy processes are running

## Credits

- Original Pac-Man concept by Namco
- Ghost images represent various tech company logos
- Built as a learning project demonstrating game development fundamentals

## License

This project is provided as-is for educational purposes.

---

**Enjoy the game and happy hunting!**
