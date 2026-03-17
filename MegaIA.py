import random
import json
import os


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
            'morreu_poço': {'count': 0, 'turns': []},
            'morreu_monstro': {'count': 0, 'turns': []},
            'morreu_fome': {'count': 0, 'turns': []},
            'recompensas': {'count': 0, 'turns': []},
        }
        self.timeline = []
        self.turn = 0
        self.identity = "sobrevivente"
        self.explore_chance = 0.80
        self.apples_found = 0

        # Carrega memória salva se existir
        self._carregar_memoria()

    def _carregar_memoria(self):
        if os.path.exists(self.MEMORIA_FILE):
            try:
                with open(self.MEMORIA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.sensory_memory = {}
                    for k, v in data.get('sensory_memory', {}).items():
                        key = tuple(k) if isinstance(k, list) else tuple(eval(k)) if isinstance(k, str) and k.startswith('(') else tuple(k)
                        self.sensory_memory[key] = v
                    self.rules = data.get('rules', self.rules)
                    self.world_facts = data.get('world_facts', self.world_facts)
                    self.timeline = data.get('timeline', self.timeline)
                    self.identity = data.get('identity', self.identity)
                    self.apples_found = data.get('apples_found', self.apples_found)
                print("Memória da MegaIA recuperada do arquivo!")
            except Exception as e:
                print(f"Erro ao carregar memória: {e}. Começando do zero.")

    def _salvar_memoria(self):
        data = {
            'sensory_memory': {str(k): v for k, v in self.sensory_memory.items()},
            'rules': self.rules,
            'world_facts': self.world_facts,
            'timeline': self.timeline,
            'identity': self.identity,
            'apples_found': self.apples_found
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

    def _record_event(self, event_type, data):
        self.timeline.append({'turn': self.turn, 'type': event_type, 'data': data})
        if event_type not in self.world_facts:
            self.world_facts[event_type] = {'count': 0, 'turns': []}
        self.world_facts[event_type]['count'] += 1
        self.world_facts[event_type]['turns'].append(self.turn)

    def _temporal_risk(self, event_type, window=10):
        info = self.world_facts.get(event_type, {'turns': []})
        turns = info.get('turns', [])
        recent = [t for t in turns if self.turn - window <= t <= self.turn]
        if not recent:
            return 0
        freq = len(recent)/max(1, window)
        recency = max(0, 1 - ((self.turn - recent[-1]) / window))
        return min(1.0, freq + recency*0.5)

    def _dir_vector(self, direction):
        return {'N': (-1,0), 'S': (1,0), 'E': (0,1), 'W': (0,-1)}.get(direction, (0,1))

    def _rotate(self, direction, turn):
        order = ['N','E','S','W']
        idx = order.index(direction)
        if turn == 'left':
            return order[(idx - 1) % 4]
        return order[(idx + 1) % 4]

    def _next_relative(self, act, p):
        direction = p['direction']
        if direction not in ['N','S','E','W']:
            direction = 'N'
        if act == 'avancar':
            return self._dir_vector(direction)
        if act == 'virar_esquerda':
            new_dir = self._rotate(direction, 'left')
            return self._dir_vector(new_dir)
        if act == 'virar_direita':
            new_dir = self._rotate(direction, 'right')
            return self._dir_vector(new_dir)
        return (0, 0)

    def _safe_route_score(self, act, p, visible):
        rel = self._next_relative(act, p)
        score = 0

        # risco de poço/monstro baseado no futuro celula e memória relativa
        score -= self.get_sensory_truth(rel, 'X') * 2
        score -= self.get_sensory_truth(rel, 'M') * 2

        # se já sabemos que frente é seguro (vazio), dá bônus
        if self.get_sensory_truth(rel, '.',) > 0:
            score += 20

        # risco temporal local, se morrer em poço/monstro nos últimos turns
        score -= self._temporal_risk('morreu_poço') * 50
        score -= self._temporal_risk('morreu_monstro') * 40

        # preventiva: se a ação é 'avancar' para um lado desconhecido com muitos registros de morte, penaliza.
        if act == 'avancar' and abs(rel[0]) + abs(rel[1]) == 1:
            score -= self.world_facts.get('morreu_poço', {}).get('count', 0) * 0.4
            score -= self.world_facts.get('morreu_monstro', {}).get('count', 0) * 0.3

        return score

    def _twostep_score(self, act, p):
        direction = p['direction']
        if direction not in ['N','S','E','W']:
            direction = 'N'
        score = 0
        if act == 'avancar':
            dr, dc = self._dir_vector(direction)
            for step in [1,2]:
                rel = (dr*step, dc*step)
                score += self.get_sensory_truth(rel, 'A') * 2
                score -= self.get_sensory_truth(rel, 'X') * 3
                score -= self.get_sensory_truth(rel, 'M') * 2
        elif act == 'virar_esquerda':
            new_dir = self._rotate(direction, 'left')
            dr, dc = self._dir_vector(new_dir)
            rel = (dr, dc)
            score += self.get_sensory_truth(rel, 'A') * 2
            score -= self.get_sensory_truth(rel, 'X') * 4
        elif act == 'virar_direita':
            new_dir = self._rotate(direction, 'right')
            dr, dc = self._dir_vector(new_dir)
            rel = (dr, dc)
            score += self.get_sensory_truth(rel, 'A') * 2
            score -= self.get_sensory_truth(rel, 'X') * 4
        return score

    def choose_action(self, p, bot_pos, bot_dir, dungeon):
        visible = p.get('visible_items', {})

        # ATRAÇÃO DIRETA POR MAÇÃ (visão relativa)
        for pos, item in visible.items():
            rel = item['relative']
            if item['symbol'] == 'A':
                if rel == (0, 1) or rel == (0, -1) or rel == (1, 0) or rel == (-1, 0):
                    return 'avancar' if not p['on_apple'] else 'pegar'

        if p['on_apple']:
            return 'pegar'

        if self.apples_found >= 1:
            self.identity = "colecionador"

        if random.random() < self.explore_chance:
            opts = ['avancar', 'virar_esquerda', 'virar_direita']
            if p['near_monster']:
                opts.append('atacar')
            return random.choice(opts)

        best_score = -999
        best_act = 'avancar'
        for act in ['avancar', 'virar_esquerda', 'virar_direita', 'pegar', 'atacar']:
            score = self._mental_simulate(act, p, visible)
            score += self._twostep_score(act, p)
            score += self._safe_route_score(act, p, visible)
            if self.rules['near_pit_means_danger'] and p['near_pit'] and act == 'avancar':
                score -= 40
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

        # Preferência por maior horizonte mental
        score += self._twostep_score(act, p) * 0.2

        return score


def main_megaia(Dungeon, print_status, num_lives=30, max_turns=200):
    core = MegaCore()
    print('=== MegaIA - Treino (30 vidas rápidas) + depois simulação detalhada ===\n')

    # === FASE 1: TREINO RÁPIDO (aprende regras e memória sensorial) ===
    for vida in range(1, num_lives + 1):
        core.explore_chance = max(0.15, core.explore_chance - 0.03)
        dungeon = Dungeon()

        while not dungeon.state['done']:
            core.turn += 1
            p = dungeon.perception()
            action = core.choose_action(p, dungeon.state['bot'].position, dungeon.state['bot'].direction, dungeon)
            result = dungeon.step(action)

            if result.get('reason'):
                core._record_event(f"morreu_{result['reason']}", {'position': p['position'], 'turn': core.turn})
            if result['reward'] > 0:
                core._record_event('recompensa', {'reward': result['reward'], 'turn': core.turn})

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
        core.turn += 1
        p = dungeon.perception()
        action = core.choose_action(p, dungeon.state['bot'].position, dungeon.state['bot'].direction, dungeon)

        print(f"\nTurno {turn:3d} | MegaIA escolheu: {action} | Identidade: {core.identity}")
        print(dungeon.render())
        print_status(dungeon)

        result = dungeon.step(action)

        if result.get('reason'):
            core._record_event(f"morreu_{result['reason']}", {'position': p['position'], 'turn': core.turn})
        if result['reward'] > 0:
            core._record_event('recompensa', {'reward': result['reward'], 'turn': core.turn})

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
