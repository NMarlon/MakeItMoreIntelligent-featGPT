from MegaIA import MegaCore

# Cores ANSI para terminal
ANSI_RESET = '\x1b[0m'
ANSI_RED = '\x1b[91m'
ANSI_GREEN = '\x1b[92m'
ANSI_YELLOW = '\x1b[93m'
ANSI_BLUE = '\x1b[94m'
ANSI_MAGENTA = '\x1b[95m'
ANSI_CYAN = '\x1b[96m'
ANSI_WHITE = '\x1b[97m'

def run_tutorial(core: MegaCore):
    """
    Executa uma série de cenários de aprendizado pré-definidos para ensinar ao bot
    as regras básicas do mundo.
    """
    print(f"=== {ANSI_MAGENTA}Iniciando Pré-Tutorial da MegaIA{ANSI_RESET} ===")

    # Cenário 1: Aprender a avançar com sucesso
    ensinar_cenario(core, {
        'descricao': "Avançar em um espaço vazio",
        'percepcao_inicial': {'on_apple': False, 'on_monster': False, 'on_pit': False, 'direction': 'E', 'visible_items': {}},
        'acao': 'avancar',
        'resultado': {'reward': -1, 'reason': None},
        'percepcao_final': {'on_apple': False, 'on_monster': False, 'on_pit': False}
    })

    # Cenário 2: Aprender sobre o perigo do monstro
    ensinar_cenario(core, {
        'descricao': "Avançar em direção a um monstro resulta em morte",
        'percepcao_inicial': {'on_apple': False, 'on_monster': True, 'on_pit': False, 'direction': 'E', 'visible_items': {}},
        'acao': 'avancar',
        'resultado': {'reward': -100, 'reason': 'monstro'},
        'percepcao_final': {'on_apple': False, 'on_monster': True, 'on_pit': False}
    })
    
    # Cenário 3: Aprender a virar à direita
    ensinar_cenario(core, {
        'descricao': "Aprender a virar à direita",
        'percepcao_inicial': {'on_apple': False, 'on_monster': False, 'on_pit': False, 'direction': 'N', 'visible_items': {}},
        'acao': 'virar_direita',
        'resultado': {'reward': 0, 'reason': None},
        'percepcao_final': {'on_apple': False, 'on_monster': False, 'on_pit': False, 'direction': 'E'}
    })

    # Cenário 4: Aprender a pegar uma maçã
    ensinar_cenario(core, {
        'descricao': "Pegar uma maçã resulta em recompensa",
        'percepcao_inicial': {'on_apple': True, 'on_monster': False, 'on_pit': False, 'direction': 'N', 'inventory': {'apple': False}},
        'acao': 'pegar',
        'resultado': {'reward': 50, 'reason': None},
        'percepcao_final': {'on_apple': False, 'on_monster': False, 'on_pit': False, 'inventory': {'apple': True}}
    })
    
    # Cenário 5: Aprender sobre o perigo do poço
    ensinar_cenario(core, {
        'descricao': "Avançar em direção a um poço resulta em morte",
        'percepcao_inicial': {'on_apple': False, 'on_monster': False, 'on_pit': True, 'direction': 'S', 'visible_items': {}},
        'acao': 'avancar',
        'resultado': {'reward': -100, 'reason': 'poço'},
        'percepcao_final': {'on_apple': False, 'on_monster': False, 'on_pit': True}
    })

    print(f"=== {ANSI_MAGENTA}Pré-Tutorial Concluído{ANSI_RESET} ===")
    core.finalizar_vida() # Salva o aprendizado do tutorial

def ensinar_cenario(core: MegaCore, cenario: dict):
    """
    Simula um único cenário de aprendizado para o MegaCore.
    """
    print(f"\n{ANSI_YELLOW}Ensinando:{ANSI_RESET} {cenario['descricao']}")
    
    p_inicial = cenario['percepcao_inicial']
    acao = cenario['acao']
    resultado = cenario['resultado']
    p_final = cenario['percepcao_final']

    # A MegaIA "pensa" e "aprende" com o resultado fornecido
    core.learn_from_turn(p_inicial, acao, resultado, p_final)
    
    reward = resultado['reward']
    reward_color = ANSI_GREEN if reward > 0 else (ANSI_RED if reward < 0 else ANSI_WHITE)
    reason_str = f", Razão: {resultado['reason']}" if resultado['reason'] else ""

    print(f"  Ação: '{ANSI_CYAN}{acao}{ANSI_RESET}' -> Resultado: Reward {reward_color}{reward}{ANSI_RESET}{reason_str}")
    
    # Forçar o aprendizado dos instintos básicos
    if resultado['reward'] > 0:
        core._record_event("recompensa", {"reward": resultado['reward'], "turn": core.turn})
        print(f"  {ANSI_GREEN}MegaIA sentiu uma recompensa (instinto 'encontrar maçã' reforçado).{ANSI_RESET}")
    elif resultado['reward'] < -50:
        reason = core._normalize_reason(resultado.get('reason'))
        if reason:
            core._record_event(f"morreu_{reason}", {"position": p_inicial.get("position"), "turn": core.turn})
            print(f"  {ANSI_RED}MegaIA sentiu uma punição (instinto 'não morrer' de '{reason}' reforçado).{ANSI_RESET}")

    core.turn += 1
