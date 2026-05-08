# Project Overview

This project, "MegaIA," is a Python-based AI simulation inspired by MegaMan Battle Network. The goal is to create a simple, conceptual AI that learns from a few examples, has a persistent memory, and evolves its behavior over time. The AI, a `Bot` in a `Dungeon` environment, learns to navigate, find apples, and avoid monsters and pits.

The core of the project is the `MegaCore` class, which acts as the AI's brain. It uses a "sensory memory" system, where it stores knowledge about the world in relation to its own position. This memory is persisted in a `megaia_memoria.json` file, allowing the AI to learn across multiple runs.

The project is designed to be highly conceptual, focusing on ideas like "one-glance learning," "mental simulation," and evolving "identity" rather than using traditional machine learning models.

## Building and Running

The project is written in Python and has no external dependencies listed. To run the simulation, execute the `main.py` file:

```bash
python main.py
```

This will start the simulation, which includes a training phase and then a more detailed, interactive simulation where the AI's actions and the game state are printed to the console.

## Development Conventions

The project follows a set of principles outlined in `AGENTS.md` and the `.github/instructions` files. The key ideas are:

*   **Simplicity:** The AI logic should be simple and conceptual, avoiding complex machine learning frameworks.
*   **One-Glance Learning:** The AI should be able to learn from a single experience.
*   **Mental Simulation:** The AI should "think" before it acts, simulating the consequences of its actions.
*   **Persistent Memory:** The AI's knowledge should be saved between runs.
*   **Evolving Identity:** The AI's behavior and "personality" should change based on its experiences.

The code is structured into two main files:
*   `main.py`: Contains the environment simulation (the `Dungeon` and the `Bot`).
*   `MegaIA.py`: Contains the AI's "brain" (the `MegaCore` class), which handles learning and decision-making.
