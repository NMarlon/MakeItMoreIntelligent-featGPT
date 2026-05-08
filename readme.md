# MegaIA - Game and AI Architecture

This project implements a dungeon exploration game with AI agents that learn to survive and collect apples while avoiding monsters and pits.

## Architecture Overview

The codebase is separated into **Game Structure** and **AI Logic** for modularity and future development.

### Game Structure (main.py)
Contains all game mechanics, physics, and environment:
- `Dungeon` class: Game world with monsters, pits, apples
- `Bot` class: Player character with movement and actions
- Perception system: Vision cone, adjacency detection
- Rendering: ASCII visualization with ANSI colors
- Game loop: Action processing and state updates

### AI Interface (MegaIA.py)
Defines the contract for AI implementations:
- `AIAgent` abstract base class
- `DummyAI`: Simple test AI
- `BiologicalBrainAI`: Placeholder for neuroscience-inspired AI
- `get_legacy_ai()`: Access to archived Version 0.1 AI

### Archived AI Logic (Archive/Version 0.1/)
The original AI implementation has been moved here:
- `MegaCore` class with memory systems and learning
- Full training and simulation code
- Tutorial scenarios

## Running the Game

```bash
python main.py
```

By default, uses `DummyAI` for testing. To use different AIs, modify the `__main__` block in `main.py`:

```python
# Options:
ai_agent = DummyAI()           # Simple random AI
ai_agent = BiologicalBrainAI() # Placeholder for future implementation
ai_agent = get_legacy_ai()     # Load archived Version 0.1 AI
```

## Implementing New AI Agents

Create a class that inherits from `AIAgent` and implement the required methods:

```python
from MegaIA import AIAgent

class MyAI(AIAgent):
    def choose_action(self, perception, bot_pos, bot_dir, dungeon):
        # Your decision logic here
        return 'avancar'  # or other actions

    def learn_from_turn(self, p_before, action, result, p_after):
        # Your learning logic here
        pass

    def begin_life(self, label="vida"):
        # Initialize for new episode
        pass

    def finalizar_vida(self):
        # Clean up and save state
        pass
```

## Perception Format

The `perception` dictionary contains:
- `visible_items`: Dict of {(r,c): {'symbol': str, 'relative': (dr,dc)}}
- `near_monster/pit/apple`: bool (adjacent detection)
- `on_monster/pit/apple`: bool (current position)
- `position`: (r,c), `direction`: str, `alive`: bool

## Actions

Available actions: `'avancar'`, `'virar_esquerda'`, `'virar_direita'`, `'pegar'`, `'atacar'`

## Future Development

The `BiologicalBrainAI` class is prepared for implementation based on:
- Hippocampal episodic memory
- Prefrontal cortex working memory
- Amygdala emotional processing
- Cerebellar motor learning
- Thalamic attention systems

## Version History

- **Version 0.1**: Original AI implementation (archived)
- **Current**: Modular architecture with AI interfaces



