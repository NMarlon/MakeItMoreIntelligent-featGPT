"""
AI Interface and Biological Brain Preparation for MegaIA.

This module defines the interfaces for AI agents that interact with the game environment.
It includes a dummy AI for testing and placeholders for future biological brain-inspired implementations.

The game structure (Dungeon, Bot, perception, etc.) is in main.py.
The old AI logic (MegaCore) has been moved to Archive/Version 0.1/.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import random

# Cores ANSI para terminal (shared with game)
ANSI_RESET = '\x1b[0m'
ANSI_RED = '\x1b[91m'
ANSI_GREEN = '\x1b[92m'
ANSI_YELLOW = '\x1b[93m'
ANSI_BLUE = '\x1b[94m'
ANSI_MAGENTA = '\x1b[95m'
ANSI_CYAN = '\x1b[96m'
ANSI_WHITE = '\x1b[97m'


class AIAgent(ABC):
    """
    Abstract base class for AI agents that can play the dungeon game.

    This interface defines the contract between the game engine and AI implementations.
    Future biological brain-inspired AIs should implement this interface.
    """

    @abstractmethod
    def choose_action(self, perception: Dict[str, Any], bot_pos: tuple[int, int],
                     bot_dir: int, dungeon) -> str:
        """
        Choose the next action based on current perception.

        Args:
            perception: Dictionary from Dungeon.perception() containing:
                - visible_items: {(r,c): {'symbol': str, 'relative': (dr,dc)}}
                - near_monster, near_pit, near_apple: bool
                - on_apple, on_monster, on_pit: bool
                - position: (r,c), direction: str, alive: bool
            bot_pos: Current bot position (r,c)
            bot_dir: Current direction (0=N,1=E,2=S,3=W)
            dungeon: Dungeon instance for additional queries if needed

        Returns:
            One of: 'avancar', 'virar_esquerda', 'virar_direita', 'pegar', 'atacar'
        """
        pass

    @abstractmethod
    def learn_from_turn(self, p_before: Dict[str, Any], action: str,
                       result: Dict[str, Any], p_after: Dict[str, Any]):
        """
        Learn from the consequences of an action.

        Args:
            p_before: Perception before the action
            action: Action taken
            result: Result from Dungeon.step(), containing:
                - reward: int, done: bool, reason: str|None
            p_after: Perception after the action
        """
        pass

    @abstractmethod
    def begin_life(self, label: str = "vida"):
        """Start a new life/episode."""
        pass

    @abstractmethod
    def finalizar_vida(self):
        """End the current life/episode and save any persistent state."""
        pass


class DummyAI(AIAgent):
    """
    Simple dummy AI for testing game mechanics.

    This AI makes random safe actions and can be used to verify that
    the game structure works correctly without complex AI logic.
    """

    def __init__(self):
        self.actions = ['avancar', 'virar_esquerda', 'virar_direita', 'pegar', 'atacar']
        self.safe_actions = ['virar_esquerda', 'virar_direita', 'pegar']  # Avoid dangerous moves

    def choose_action(self, perception: Dict[str, Any], bot_pos: tuple[int, int],
                     bot_dir: int, dungeon) -> str:
        """Choose a random safe action."""
        if perception.get('on_apple', False):
            return 'pegar'
        elif perception.get('near_monster', False) or perception.get('near_pit', False):
            return random.choice(self.safe_actions)
        else:
            return random.choice(self.actions)

    def learn_from_turn(self, p_before: Dict[str, Any], action: str,
                       result: Dict[str, Any], p_after: Dict[str, Any]):
        """Dummy AI doesn't learn."""
        pass

    def begin_life(self, label: str = "vida"):
        """Start new life."""
        print(f"{ANSI_CYAN}DummyAI: Starting new life '{label}'{ANSI_RESET}")

    def finalizar_vida(self):
        """End life."""
        print(f"{ANSI_CYAN}DummyAI: Life ended{ANSI_RESET}")


class BiologicalBrainAI(AIAgent):
    """
    Placeholder for biological brain-inspired AI.

    This class provides the skeleton for implementing AI based on
    biological neural systems, memory consolidation, and cognitive processes.

    TODO: Implement based on neuroscience principles:
    - Hippocampal episodic memory for event sequences
    - Prefrontal cortex working memory for planning
    - Amygdala-like emotional valuation
    - Cerebellar motor learning
    - Thalamic attention filtering
    """

    def __init__(self):
        # TODO: Initialize neural networks, memory systems, etc.
        self.neural_network = None  # Placeholder for main NN
        self.episodic_memory = None  # Hippocampal-like
        self.working_memory = None  # Prefrontal-like
        self.emotional_system = None  # Amygdala-like
        self.motor_system = None  # Cerebellar-like
        self.attention_filter = None  # Thalamic-like

    def choose_action(self, perception: Dict[str, Any], bot_pos: tuple[int, int],
                     bot_dir: int, dungeon) -> str:
        """
        Choose action using biological brain simulation.

        TODO: Implement decision-making through:
        1. Sensory processing and attention filtering
        2. Memory retrieval and pattern matching
        3. Emotional valuation of options
        4. Motor planning and action selection
        """
        # Placeholder: return safe action
        return 'pegar' if perception.get('on_apple', False) else 'virar_direita'

    def learn_from_turn(self, p_before: Dict[str, Any], action: str,
                       result: Dict[str, Any], p_after: Dict[str, Any]):
        """
        Learn using biological memory consolidation.

        TODO: Implement learning through:
        1. Episodic memory storage of experience
        2. Emotional tagging of outcomes
        3. Memory replay during rest/sleep phases
        4. Synaptic plasticity and network updates
        """
        pass

    def begin_life(self, label: str = "vida"):
        """Initialize biological systems for new life."""
        print(f"{ANSI_MAGENTA}BiologicalBrainAI: Initializing neural systems for '{label}'{ANSI_RESET}")

    def finalizar_vida(self):
        """Consolidate memories and update long-term knowledge."""
        print(f"{ANSI_MAGENTA}BiologicalBrainAI: Consolidating memories{ANSI_RESET}")


# Legacy compatibility: import the old AI from archive if needed
def get_legacy_ai():
    """
    Import and return the old MegaCore AI from Version 0.1 archive.

    This is for testing or comparison purposes only.
    The old AI logic has been moved to Archive/Version 0.1/
    """
    try:
        import sys
        import os
        archive_path = os.path.join(os.path.dirname(__file__), 'Archive', 'Version 0.1 (chat try it alone do with instructions)')
        sys.path.insert(0, archive_path)
        import importlib.util
        spec = importlib.util.spec_from_file_location("legacy_megaia", os.path.join(archive_path, "MegaIA.py"))
        legacy_megaia = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(legacy_megaia)
        return legacy_megaia.MegaCore()
    except ImportError as e:
        print(f"{ANSI_RED}Error loading legacy AI: {e}{ANSI_RESET}")
        return DummyAI()


def run_tutorial(core: AIAgent):
    """
    Run the tutorial with any AI agent.

    The tutorial scenarios have been moved to Archive/Version 0.1/tutorial.py
    This is a placeholder that demonstrates the interface.
    """
    print(f"{ANSI_MAGENTA}Tutorial interface ready for AI agent{ANSI_RESET}")
    # TODO: Load tutorial scenarios and run them
    core.begin_life("tutorial")
    # Placeholder tutorial logic
    core.finalizar_vida()


def main_megaia(
    Dungeon,
    print_status,
    num_lives=80,
    max_turns=500,
    post_train_turns=10,
    interactive=True,
    reset_memory_on_start=False,
    core_instance=None,
):
    """
    Main training and simulation function using AI interface.

    This is a placeholder. The full implementation has been moved to Archive/Version 0.1/
    """
    if core_instance is None:
        core_instance = DummyAI()  # Use dummy AI by default

    print(f"{ANSI_MAGENTA}=== MegaIA Interface - Training with {type(core_instance).__name__} ==={ANSI_RESET}\n")

    # Placeholder training loop
    for vida in range(1, min(num_lives, 5) + 1):  # Limit for demo
        core_instance.begin_life(f"training_{vida}")
        dungeon = Dungeon()
        # Simplified training loop
        for turn in range(max_turns):
            p = dungeon.perception()
            action = core_instance.choose_action(p, dungeon.state['bot'].position,
                                               dungeon.state['bot'].direction, dungeon)
            result = dungeon.step(action)
            p_after = dungeon.perception()
            core_instance.learn_from_turn(p, action, result, p_after)
            if dungeon.state['done']:
                break
        core_instance.finalizar_vida()

    print(f"\n{ANSI_MAGENTA}Training completed with {type(core_instance).__name__}{ANSI_RESET}\n")

    # Simulation with visualization
    core_instance.begin_life("simulation")
    dungeon = Dungeon()
    cycle = 0
    total_turns = 0
    
    while cycle < post_train_turns:
        print(f"\n{ANSI_CYAN}=== Simulation Cycle {cycle + 1} ==={ANSI_RESET}")
        print_status(dungeon)
        
        turn = 0
        while not dungeon.state['done'] and turn < max_turns:
            p = dungeon.perception()
            action = core_instance.choose_action(p, dungeon.state['bot'].position,
                                               dungeon.state['bot'].direction, dungeon)
            result = dungeon.step(action)
            
            print(f"\nTurn {turn + 1}: Action '{ANSI_YELLOW}{action}{ANSI_RESET}', Reward: {result['reward']}")
            if result.get('reason'):
                print(f"Game ended: {result['reason']}")
            print_status(dungeon)
            
            total_turns += 1
            turn += 1
            
            # Auto-advance for non-interactive mode
            if not interactive:
                pass  # Continue automatically
            else:
                try:
                    input("Press Enter for next turn (or Ctrl+C to stop)...")
                except KeyboardInterrupt:
                    print("\nSimulation interrupted by user.")
                    break
        
        if dungeon.state['done']:
            print(f"\nCycle {cycle + 1} ended. Reason: {dungeon.state.get('reason')}, Score: {dungeon.state['bot'].score}")
        
        cycle += 1
        if cycle < post_train_turns:
            # Reset for next cycle
            dungeon = Dungeon()
    
    core_instance.finalizar_vida()
    print(f"\n{ANSI_GREEN}Simulation completed. Total turns: {total_turns}{ANSI_RESET}")
