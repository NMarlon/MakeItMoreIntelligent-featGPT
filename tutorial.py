
from MegaIA import MegaCore

def run_tutorial(core: MegaCore):
    """
    Executa uma série de cenários de aprendizado pré-definidos para ensinar ao bot
    as regras básicas do mundo.
    """
    print("=== Iniciando Pré-Tutorial da MegaIA ===")

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

    print("=== Pré-Tutorial Concluído ===")
    core.finalizar_vida() # Salva o aprendizado do tutorial

def ensinar_cenario(core: MegaCore, cenario: dict):
    """
    Simula um único cenário de aprendizado para o MegaCore.
    """
    print(f"\nEnsinando: {cenario['descricao']}")
    
    p_inicial = cenario['percepcao_inicial']
    acao = cenario['acao']
    resultado = cenario['resultado']
    p_final = cenario['percepcao_final']

    # A MegaIA "pensa" e "aprende" com o resultado fornecido
    core.learn_from_turn(p_inicial, acao, resultado, p_final)
    
    print(f"  Ação: '{acao}' -> Resultado: Reward {resultado['reward']}, Razão: {resultado['reason']}")
    
    # Forçar o aprendizado dos instintos básicos
    if resultado['reward'] > 0:
        core._record_event("recompensa", {"reward": resultado['reward'], "turn": core.turn})
        print("  MegaIA sentiu uma recompensa (instinto 'encontrar maçã' reforçado).")
    elif resultado['reward'] < -50:
        reason = core._normalize_reason(resultado.get('reason'))
        if reason:
            core._record_event(f"morreu_{reason}", {"position": p_inicial.get("position"), "turn": core.turn})
            print(f"  MegaIA sentiu uma punição (instinto 'não morrer' de '{reason}' reforçado).")

    core.turn += 1
