import random
import json
import os
import ast


# ===================== MEGAIA CORE - MEMÓRIA SENSORIAL RELATIVA + DOMÍNIO TOTAL =====================
class MegaCore:
    MEMORIA_FILE = "megaia_memoria.json"

    def __init__(self):
        self.sensory_memory = {}
        self.rules = {
            'apple_always_exists': False,
            'apple_respawns': False,
            'monster_chases': False,
            'hunger_decreases': False,
            'near_pit_means_danger': False,
            'see_apple_in_front_means_go': False
        }
        self.world_facts = {
            'apple_respawn_count': 0,
            'apple_respawn_turns': [],
            'monster_encounters': 0,
            'last_monster_turn': None,
        }
        self.identity = "sobrevivente"
        self.personality = "1.0-caridosa"  # Personalidade inicial padronizada
        self.identity_text = (
            "MegaIA: sobrevivente que aprende em um relance, com memória relativa "
            "(dx,dy,símbolo), regras do mundo aprendidas e horizonte temporal."
        )
        self.explore_chance = 0.80
        self.apples_found = 0
        self.timeline = []
        self.turn = 0

        # Carrega memória salva se existir
        self._carregar_memoria()

    def _carregar_memoria(self):
        if os.path.exists(self.MEMORIA_FILE):
            try:
                with open(self.MEMORIA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.sensory_memory = {}
                    for k, v in data.get('sensory_memory', {}).items():
                        try:
                            key = ast.literal_eval(k)
                        except Exception:
                            key = tuple(k)
                        self.sensory_memory[key] = v
                    self.rules = data.get('rules', self.rules)
                    self.world_facts = data.get('world_facts', self.world_facts)
                    self.identity = data.get('identity', self.identity)
                    self.personality = data.get('personality', self.personality)
                    self.apples_found = data.get('apples_found', self.apples_found)
                    self.timeline = data.get('timeline', [])
                print("Memória da MegaIA recuperada do arquivo!")
            except Exception as e:
                print(f"Erro ao carregar memória: {e}. Começando do zero.")

    def _salvar_memoria(self):
        data = {
            'sensory_memory': {str(k): v for k, v in self.sensory_memory.items()},
            'rules': self.rules,
            'world_facts': self.world_facts,
            'identity': self.identity,
            'personality': self.personality,
            'apples_found': self.apples_found,
            'timeline': self.timeline[-200:]
        }
        try:
            with open(self.MEMORIA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Memória da MegaIA salva no arquivo.")
        except Exception as e:
            print(f"Erro ao salvar memória: {e}")

    def finalizar_vida(self):
        self._salvar_memoria()

    def get_sensory_truth(self, relative, symbol):
        key = (relative[0], relative[1], symbol)
        return self.sensory_memory.get(key, 0)

    def update_sensory_truth(self, relative, symbol, reward, reason, is_mental=False):
        key = (relative[0], relative[1], symbol)
        change = -35 if reason in ('poço', 'monstro', 'morreu_fome') else (reward if reward > 0 else 0)
        if symbol == 'A' and reward > 0:
            change += 140  # desejo + satisfação por maçã

        current = self.sensory_memory.get(key, 0)
        self.sensory_memory[key] = max(-200, min(200, current + change))

        # Aprende regras do mundo a partir dos senses
        if symbol == 'A':
            self.rules['apple_always_exists'] = True
            self.rules['apple_respawns'] = True
            self.rules['see_apple_in_front_means_go'] = True
            self.apples_found += 1
        if symbol == 'X' or reason == 'poço':
            self.rules['near_pit_means_danger'] = True
        if symbol == 'M' or reason == 'monstro':
            self.rules['monster_chases'] = True
        if reason == 'morreu_fome':
            self.rules['hunger_decreases'] = True

        if is_mental and change > 0:
            print(f"  (Pensamento: {symbol} em {relative} → atrai!)")

    def _update_personality(self):
        # Transições simples de personalidade com base em experiência
        if self.apples_found >= 2:
            self.personality = '2.2-livre'
        elif self.world_facts.get('monster_encounters', 0) >= 2:
            self.personality = '2.1-vilao'

    def _personality_action_bias(self, act, p):
        bias = 0
        if self.personality.startswith('1.0'):
            if act == 'pegar' and p.get('on_apple', False):
                bias += 260
            if act == 'atacar':
                bias -= 120
            if p.get('near_pit', False) and act == 'avancar':
                bias -= 110
        elif self.personality.startswith('2.1'):
            if act == 'atacar' and p.get('near_monster', False):
                bias += 200
            if act == 'pegar' and p.get('on_apple', False):
                bias += 80
            if p.get('near_pit', False) and act == 'avancar':
                bias -= 40
        else:  # 2.2 livre
            if act == 'pegar' and p.get('on_apple', False):
                bias += 200
            if act == 'atacar' and p.get('near_monster', False):
                bias += 80
            if p.get('near_pit', False) and act == 'avancar':
                bias -= 60
        return bias

    def record_event(self, turn, action, p, reward, reason):
        self.timeline.append({
            'turn': turn,
            'action': action,
            'position': p['position'],
            'direction': p['direction'],
            'reward': reward,
            'reason': reason,
            'near_apple': p.get('near_apple', False),
            'near_monster': p.get('near_monster', False),
            'near_pit': p.get('near_pit', False),
        })

        if reason == 'monstro':
            self.world_facts['monster_encounters'] += 1
            self.world_facts['last_monster_turn'] = turn
        if p.get('near_apple', False) and action == 'pegar':
            self.world_facts['apple_respawn_count'] += 1
            self.world_facts['apple_respawn_turns'].append(turn)
            if len(self.world_facts['apple_respawn_turns']) >= 2:
                diffs = [self.world_facts['apple_respawn_turns'][i] - self.world_facts['apple_respawn_turns'][i-1] for i in range(1, len(self.world_facts['apple_respawn_turns']))]
                self.world_facts['apple_respawn_est'] = sum(diffs) / len(diffs)

    def _temporal_insight(self):
        insight = 0
        if self.world_facts.get('apple_respawn_est'):
            insight += 20
        if self.world_facts.get('last_monster_turn') is not None and self.turn - self.world_facts['last_monster_turn'] < 3:
            insight -= 30
        return insight

    def choose_action(self, p, bot_pos, bot_dir, dungeon):
        visible = p.get('visible_items', {})

        # ATRAÇÃO DIRETA POR MAÇÃ (visão relativa)
        for pos, item in visible.items():
            rel = item['relative']
            if item['symbol'] == 'A' and abs(rel[0]) + abs(rel[1]) <= 1:
                return 'avancar' if not p['on_apple'] else 'pegar'

        if p['on_apple']:
            return 'pegar'

        self._update_personality()
        if self.apples_found >= 1:
            self.identity = "colecionador"

        if random.random() < self.explore_chance:
            opts = ['avancar', 'virar_esquerda', 'virar_direita']
            if p['near_monster']:
                opts.append('atacar')
            if p['on_apple']:
                opts.append('pegar')
            return random.choice(opts)

        best_score = -999
        best_act = 'avancar'
        for act in ['avancar', 'virar_esquerda', 'virar_direita', 'pegar', 'atacar']:
            score = self._mental_simulate(act, p, visible)
            score += self._personality_action_bias(act, p)
            if score > best_score:
                best_score = score
                best_act = act
        return best_act

    def _mental_simulate(self, act, p, visible):
        score = 0

        # Avalia sentidos atuais (memória relativa)
        for item in visible.values():
            rel = item['relative']
            sym = item['symbol']
            truth = self.get_sensory_truth(rel, sym)
            score += truth * 3 if sym == 'A' else truth * 1.5

        # Bônus por regras aprendidas
        if self.rules['apple_always_exists']:
            score += 50
        if self.rules['near_pit_means_danger'] and p['near_pit']:
            score -= 80
        if self.rules['see_apple_in_front_means_go'] and any(v['symbol'] == 'A' for v in visible.values()):
            score += 180

        # Simulação de ação
        if act == 'avancar':
            score += 40   # tendência a explorar
        if act == 'pegar' and p['on_apple']:
            score += 300
        if act == 'atacar' and p['near_monster']:
            score += 100

        # memória temporal: preferir ações que evitam perigo recente
        score += self._temporal_insight()
        return score


def main_megaia(Dungeon, print_status, num_lives=30, max_turns=200):
    core = MegaCore()
    print('=== MegaIA - Treino (30 vidas rápidas) + depois simulação detalhada ===\n')

    # === FASE 1: TREINO RÁPIDO (aprende regras e memória sensorial) ===
    for vida in range(1, num_lives + 1):
        core.explore_chance = max(0.15, core.explore_chance - 0.03)
        dungeon = Dungeon()

        while not dungeon.state['done']:
            p = dungeon.perception()
            action = core.choose_action(p, dungeon.state['bot'].position, dungeon.state['bot'].direction, dungeon)
            result = dungeon.step(action)

            # Atualiza memória sensorial relativa
            if 'visible_items' in p:
                for pos, item in p['visible_items'].items():
                    rel = item['relative']
                    core.update_sensory_truth(rel, item['symbol'], result['reward'], result.get('reason'))

        # Resumo rápido do treino (sem print excessivo)
        if vida % 5 == 0:
            print(f"Vida {vida} concluída | Maçãs: {dungeon.state['apples_collected']} | Score: {dungeon.state['bot'].score}")
        core.finalizar_vida()

    print("\nTreino concluído! Agora rodando simulação detalhada turno a turno...\n")

    dungeon = Dungeon()
    turn = 0
    while not dungeon.state['done'] and turn < max_turns:
        turn += 1
        p = dungeon.perception()
        action = core.choose_action(p, dungeon.state['bot'].position, dungeon.state['bot'].direction, dungeon)

        print(f"\nTurno {turn:3d} | MegaIA escolheu: {action} | Identidade: {core.identity} | Personalidade: {core.personality}")
        print(dungeon.render())
        print_status(dungeon)

        result = dungeon.step(action)

        if 'visible_items' in p:
            for pos, item in p['visible_items'].items():
                rel = item['relative']
                core.update_sensory_truth(rel, item['symbol'], result['reward'], result.get('reason'))

        if dungeon.state['done']:
            print(f"\nFim da simulação! Razão: {dungeon.state.get('reason', 'desconhecida')}")
            print(f"Maçãs finais: {dungeon.state['apples_collected']} | Score final: {dungeon.state['bot'].score}")

    if turn >= max_turns:
        print("\nLimite de turnos atingido. MegaIA sobreviveu muito tempo!")

    core.finalizar_vida()
    print("Simulação terminada. Memória salva para a próxima execução.")
