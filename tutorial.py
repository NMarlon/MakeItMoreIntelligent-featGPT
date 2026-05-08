from MegaIA import AIAgent

# Cores ANSI para terminal
ANSI_RESET = '\x1b[0m'
ANSI_RED = '\x1b[91m'
ANSI_GREEN = '\x1b[92m'
ANSI_YELLOW = '\x1b[93m'
ANSI_BLUE = '\x1b[94m'
ANSI_MAGENTA = '\x1b[95m'
ANSI_CYAN = '\x1b[96m'
ANSI_WHITE = '\x1b[97m'

def run_tutorial(core: AIAgent):
    """
    Run tutorial scenarios with any AI agent.

    The detailed tutorial scenarios have been moved to Archive/Version 0.1/tutorial.py
    This is a simplified interface version for testing.
    """
    print(f"=== {ANSI_MAGENTA}Tutorial Interface for AI Agents{ANSI_RESET} ===")

    # Placeholder tutorial scenarios
    scenarios = [
        {
            'description': "Basic apple collection",
            'percepcao_inicial': {'on_apple': True, 'on_monster': False, 'on_pit': False},
            'expected_action': 'pegar',
            'reward': 50
        },
        {
            'description': "Avoiding danger",
            'percepcao_inicial': {'on_apple': False, 'on_monster': True, 'on_pit': False},
            'expected_action': 'virar_direita',  # Safe action
            'reward': -100
        }
    ]

    core.begin_life("tutorial")

    for scenario in scenarios:
        print(f"\n{ANSI_YELLOW}Scenario:{ANSI_RESET} {scenario['description']}")

        # Simulate the scenario
        p_before = scenario['percepcao_inicial']
        action = core.choose_action(p_before, (0, 0), 0, None)  # Dummy dungeon

        result = {'reward': scenario['reward'], 'done': False, 'reason': None}
        p_after = p_before.copy()  # Simplified

        core.learn_from_turn(p_before, action, result, p_after)

        print(f"  AI chose: '{ANSI_CYAN}{action}{ANSI_RESET}' (expected: {scenario['expected_action']})")
        print(f"  Reward: {scenario['reward']}")

    core.finalizar_vida()
    print(f"=== {ANSI_MAGENTA}Tutorial Completed{ANSI_RESET} ===")