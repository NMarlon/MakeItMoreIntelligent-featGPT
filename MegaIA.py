"""Núcleo cognitivo da MegaIA.

Este módulo reúne memória, aprendizagem incremental e política de ação.
"""

import ast
import json
import os
import random
import shutil
from datetime import datetime

# Cores ANSI para terminal
ANSI_RESET = '\x1b[0m'
ANSI_RED = '\x1b[91m'
ANSI_GREEN = '\x1b[92m'
ANSI_YELLOW = '\x1b[93m'
ANSI_BLUE = '\x1b[94m'
ANSI_MAGENTA = '\x1b[95m'
ANSI_CYAN = '\x1b[96m'
ANSI_WHITE = '\x1b[97m'

class MegaCore:
    """Cérebro da MegaIA: aprende, armazena e decide ações."""
    MEMORIA_FILE = "megaia_memoria.json"

    def __init__(self, memory_file=None):
        """Inicializa estado e carrega memória persistida (se existir)."""
        self.memory_file = memory_file or self.MEMORIA_FILE
        self.sensory_memory = {}
        self.rules = self._default_rules()
        self.world_facts = self._default_world_facts()
        self.timeline = []
        self.turn = 0
        self.identity = "sobrevivente"
        self.explore_chance = 0.80
        self.apples_found = 0
        self._carregar_memoria()

    @staticmethod
    def _default_rules():
        """Retorna as regras inferidas do mundo com estado inicial neutro."""
        return {
            "apple_always_exists": False,
            "apple_respawns": False,
            "monster_chases": False,
            "hunger_decreases": False,
            "near_pit_means_danger": False,
            "see_apple_in_front_means_go": False,
        }

    @staticmethod
    def _default_world_facts():
        """Retorna estrutura base de eventos observáveis do ambiente."""
        return {
            "morreu_poco": {"count": 0, "turns": []},
            "morreu_monstro": {"count": 0, "turns": []},
            "morreu_fome": {"count": 0, "turns": []},
            "recompensa": {"count": 0, "turns": []},
        }

    @staticmethod
    def _clamp_truth(value):
        """Limita valores para evitar memórias com magnitude descontrolada."""
        return max(-200, min(200, int(value)))

    @staticmethod
    def _safe_int(value, default=0):
        """Converte para int sem quebrar execução em dados inválidos."""
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _normalize_reason(reason):
        """Padroniza motivo de evento para facilitar aprendizado e histórico."""
        if not reason:
            return None
        txt = str(reason).strip().lower()
        txt = txt.replace("poÃ§o", "poco").replace("poço", "poco")
        if "poco" in txt:
            return "poco"
        if "monstro" in txt:
            return "monstro"
        if "fome" in txt:
            return "fome"
        return txt

    def _normalize_event_key(self, event_name):
        """Padroniza nome de evento para as chaves conhecidas de world_facts."""
        if not event_name:
            return None
        txt = str(event_name).strip().lower()
        txt = txt.replace("poÃ§o", "poco").replace("poço", "poco")
        if txt in ("recompensa", "recompensas"):
            return "recompensa"
        if txt.startswith("morreu_"):
            reason = self._normalize_reason(txt.replace("morreu_", "", 1))
            if reason in ("poco", "monstro", "fome"):
                return f"morreu_{reason}"
        if txt == "morreu_poco":
            return "morreu_poco"
        if txt == "morreu_monstro":
            return "morreu_monstro"
        if txt == "morreu_fome":
            return "morreu_fome"
        return None

    def _normalize_memory_key(self, raw_key):
        """Converte chave de memória para o formato canônico (dx, dy, símbolo)."""
        cur = raw_key
        # Alguns arquivos antigos serializaram tuplas como string; tentamos resolver.
        for _ in range(10):
            if isinstance(cur, str):
                try:
                    cur = ast.literal_eval(cur)
                    continue
                except Exception:
                    return None
            if isinstance(cur, tuple) and cur and all(isinstance(ch, str) and len(ch) == 1 for ch in cur):
                cur = "".join(cur)
                continue
            break

        if isinstance(cur, list):
            cur = tuple(cur)

        if isinstance(cur, tuple) and len(cur) == 3:
            try:
                dx = int(cur[0])
                dy = int(cur[1])
            except (TypeError, ValueError):
                return None
            symbol = str(cur[2])[:1]
            if not symbol:
                return None
            return (dx, dy, symbol)

        return None

    def _parse_sensory_memory(self, payload):
        """Interpreta memória salva em diferentes formatos e consolida em dict."""
        totals = {}
        counts = {}

        def add_entry(key, value):
            """Acumula entradas repetidas para fazer média robusta no final."""
            if key is None:
                return
            v = self._safe_int(value, None)
            if v is None:
                return
            totals[key] = totals.get(key, 0) + v
            counts[key] = counts.get(key, 0) + 1

        if isinstance(payload, list):
            for entry in payload:
                if not isinstance(entry, dict):
                    continue
                key = self._normalize_memory_key(
                    (entry.get("dx"), entry.get("dy"), entry.get("symbol"))
                )
                add_entry(key, entry.get("value", 0))
        elif isinstance(payload, dict):
            for raw_key, value in payload.items():
                key = self._normalize_memory_key(raw_key)
                add_entry(key, value)

        merged = {}
        for key, total in totals.items():
            avg = round(total / counts[key])
            merged[key] = self._clamp_truth(avg)
        return merged

    def _serialize_sensory_memory(self):
        """Converte memória para lista estável de registros serializáveis em JSON."""
        records = []
        for (dx, dy, symbol), value in sorted(self.sensory_memory.items()):
            records.append(
                {
                    "dx": int(dx),
                    "dy": int(dy),
                    "symbol": str(symbol)[:1],
                    "value": self._clamp_truth(value),
                }
            )
        return records

    def _reset_runtime_state(self):
        """Reseta apenas estado em execução (sem apagar arquivo diretamente)."""
        self.sensory_memory = {}
        self.rules = self._default_rules()
        self.world_facts = self._default_world_facts()
        self.timeline = []
        self.turn = 0
        self.identity = "sobrevivente"
        self.explore_chance = 0.80
        self.apples_found = 0

    def _carregar_memoria(self):
        """Carrega memória do disco com validação e normalização defensiva."""
        if not os.path.exists(self.memory_file):
            return
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # A memória sensorial pode vir em formatos diferentes entre versões.
            self.sensory_memory = self._parse_sensory_memory(data.get("sensory_memory", {}))

            loaded_rules = data.get("rules", {})
            merged_rules = self._default_rules()
            if isinstance(loaded_rules, dict):
                for k in merged_rules:
                    if k in loaded_rules:
                        merged_rules[k] = bool(loaded_rules[k])
            self.rules = merged_rules

            loaded_facts = data.get("world_facts", {})
            merged_facts = self._default_world_facts()
            if isinstance(loaded_facts, dict):
                for raw_name, info in loaded_facts.items():
                    event_name = self._normalize_event_key(raw_name)
                    if not event_name:
                        continue
                    if isinstance(info, dict):
                        turns = []
                        for t in info.get("turns", []):
                            turns.append(self._safe_int(t, 0))
                        merged_facts[event_name] = {
                            "count": max(0, self._safe_int(info.get("count", len(turns)), len(turns))),
                            "turns": turns,
                        }
            self.world_facts = merged_facts

            self.timeline = data.get("timeline", []) if isinstance(data.get("timeline"), list) else []
            self.identity = str(data.get("identity", self.identity))
            self.apples_found = max(0, self._safe_int(data.get("apples_found", self.apples_found), 0))
            print(f"{ANSI_GREEN}Memoria da MegaIA recuperada do arquivo.{ANSI_RESET}")
        except Exception as e:
            print(f"{ANSI_RED}Erro ao carregar memoria: {e}. Iniciando do zero.{ANSI_RESET}")

    def _salvar_memoria(self):
        """Persiste estado cognitivo completo para continuidade entre execuções."""
        data = {
            "memory_format": 2,
            "sensory_memory": self._serialize_sensory_memory(),
            "rules": self.rules,
            "world_facts": self.world_facts,
            "timeline": self.timeline,
            "identity": self.identity,
            "apples_found": self.apples_found,
        }
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"{ANSI_GREEN}Memoria da MegaIA salva no arquivo.{ANSI_RESET}")
        except Exception as e:
            print(f"{ANSI_RED}Erro ao salvar memoria: {e}{ANSI_RESET}")

    def reset_memory(self, create_backup=True):
        """Reseta memória com backup opcional para não perder histórico anterior."""
        backup_path = None
        if create_backup and os.path.exists(self.memory_file):
            base, ext = os.path.splitext(self.memory_file)
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_path = f"{base}.backup-{timestamp}{ext or '.json'}"
            shutil.copy2(self.memory_file, backup_path)
            print(f"{ANSI_YELLOW}Backup de memoria criado: {backup_path}{ANSI_RESET}")

        self._reset_runtime_state()
        self._salvar_memoria()
        print(f"{ANSI_YELLOW}Memoria da MegaIA reiniciada.{ANSI_RESET}")
        return backup_path

    def finalizar_vida(self):
        """Hook de finalização: salva memória ao fim de cada vida/ciclo."""
        self._salvar_memoria()

    def get_sensory_truth(self, relative, symbol):
        """Consulta o valor de verdade atual para uma percepção relativa."""
        key = (int(relative[0]), int(relative[1]), str(symbol)[:1])
        return self.sensory_memory.get(key, 0)

    def _apply_sensory_delta(self, relative, symbol, delta):
        """Aplica ajuste incremental e clampado em um item da memória sensorial."""
        if delta == 0:
            return
        key = (int(relative[0]), int(relative[1]), str(symbol)[:1])
        current = self.sensory_memory.get(key, 0)
        self.sensory_memory[key] = self._clamp_truth(current + int(delta))

    def update_sensory_truth(self, relative, symbol, reward, reason, is_mental=False):
        """Transforma recompensa/motivo em delta de memória para um símbolo percebido."""
        reason_norm = self._normalize_reason(reason)
        delta = 0
        if reward > 0:
            delta += min(120, int(reward))
        if reason_norm in ("poco", "monstro", "fome"):
            delta -= 35
        if symbol == "A" and reward > 0:
            delta += 80
        self._apply_sensory_delta(relative, symbol, delta)
        if is_mental and delta > 0:
            print(f"  {ANSI_BLUE}(Pensamento: {symbol} em {relative} -> atrai){ANSI_RESET}")

    def learn_from_turn(self, p_before, action, result, p_after):
        """Atualiza crenças e identidade com base na transição de um turno."""
        if not isinstance(p_before, dict):
            return
        if not isinstance(result, dict):
            return
        if not isinstance(p_after, dict):
            p_after = {}

        reward = self._safe_int(result.get("reward", 0), 0)
        reason = self._normalize_reason(result.get("reason"))

        direction = p_before.get("direction", "N")
        if direction not in ("N", "E", "S", "W"):
            direction = "N"
        front_rel = self._dir_vector(direction)

        # Regras de aprendizado por tipo de ação: o agente ajusta memória local.
        if action == "avancar":
            if reason == "poco" or p_after.get("on_pit"):
                self._apply_sensory_delta(front_rel, "X", -160)
                self.rules["near_pit_means_danger"] = True
            elif reason == "monstro" or p_after.get("on_monster"):
                self._apply_sensory_delta(front_rel, "M", -150)
                self.rules["monster_chases"] = True
            elif p_after.get("on_apple"):
                self._apply_sensory_delta(front_rel, "A", 90)
                self.rules["see_apple_in_front_means_go"] = True
            else:
                self._apply_sensory_delta(front_rel, ".", 10)

        elif action == "pegar":
            if reward > 0 and p_before.get("on_apple"):
                self._apply_sensory_delta((0, 0), "A", 140)
                self.apples_found += 1
                self.identity = "colecionador"
                self.rules["apple_always_exists"] = True
                self.rules["apple_respawns"] = True
            else:
                self._apply_sensory_delta((0, 0), "A", -30)

        elif action == "atacar":
            if reward > 0:
                self._apply_sensory_delta(front_rel, "M", 30)
                self.rules["monster_chases"] = True
            else:
                self._apply_sensory_delta(front_rel, "M", -35)

        if reason == "fome":
            self.rules["hunger_decreases"] = True
            self._apply_sensory_delta((0, 0), ".", -60)

        # Após encontrar maçã, identidade migra para perfil mais coletor.
        if self.apples_found >= 1:
            self.identity = "colecionador"

    def _record_event(self, event_type, data):
        """Registra evento no timeline e atualiza frequência em world_facts."""
        normalized = self._normalize_event_key(event_type) or event_type
        self.timeline.append({"turn": self.turn, "type": normalized, "data": data})
        if normalized not in self.world_facts:
            self.world_facts[normalized] = {"count": 0, "turns": []}
        self.world_facts[normalized]["count"] += 1
        self.world_facts[normalized]["turns"].append(self.turn)

    def _temporal_risk(self, event_type, window=10):
        """Estima risco temporal recente de um evento com base em frequência/recência."""
        info = self.world_facts.get(event_type, {"turns": []})
        turns = info.get("turns", [])
        recent = [t for t in turns if self.turn - window <= t <= self.turn]
        if not recent:
            return 0.0
        freq = len(recent) / max(1, window)
        recency = max(0.0, 1 - ((self.turn - recent[-1]) / window))
        return min(1.0, freq + recency * 0.5)

    def _dir_vector(self, direction):
        """Converte direção cardinal em deslocamento relativo (dr, dc)."""
        return {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1)}.get(direction, (0, 1))

    def _rotate(self, direction, turn):
        """Rotaciona direção 90 graus para esquerda ou direita."""
        order = ["N", "E", "S", "W"]
        idx = order.index(direction)
        if turn == "left":
            return order[(idx - 1) % 4]
        return order[(idx + 1) % 4]

    def _next_relative(self, act, p):
        """Prevê a posição relativa principal associada a uma ação candidata."""
        direction = p.get("direction", "N")
        if direction not in ["N", "S", "E", "W"]:
            direction = "N"
        if act == "avancar":
            return self._dir_vector(direction)
        if act == "virar_esquerda":
            return self._dir_vector(self._rotate(direction, "left"))
        if act == "virar_direita":
            return self._dir_vector(self._rotate(direction, "right"))
        return (0, 0)

    def _safe_route_score(self, act, p, visible):
        """Pontua segurança de rota usando memória sensorial e histórico de morte."""
        rel = self._next_relative(act, p)
        score = 0.0
        # Verdades negativas (X/M) reduzem score; positivas (A/.) compensam.
        score += self.get_sensory_truth(rel, "X") * 2.0
        score += self.get_sensory_truth(rel, "M") * 2.0
        score += self.get_sensory_truth(rel, ".") * 0.6
        score += self.get_sensory_truth(rel, "A") * 0.8

        # Risco temporal pune caminhos similares a padrões recentes de morte.
        score -= self._temporal_risk("morreu_poco") * 50
        score -= self._temporal_risk("morreu_monstro") * 40

        if act == "avancar" and abs(rel[0]) + abs(rel[1]) == 1:
            score -= self.world_facts.get("morreu_poco", {}).get("count", 0) * 0.4
            score -= self.world_facts.get("morreu_monstro", {}).get("count", 0) * 0.3

        return score

    def _twostep_score(self, act, p):
        """Pontuação de previsão curta (até 2 passos) para a ação candidata."""
        direction = p.get("direction", "N")
        if direction not in ["N", "S", "E", "W"]:
            direction = "N"
        score = 0.0
        if act == "avancar":
            dr, dc = self._dir_vector(direction)
            for step in [1, 2]:
                rel = (dr * step, dc * step)
                score += self.get_sensory_truth(rel, "A") * 2.0
                score += self.get_sensory_truth(rel, "X") * 3.0
                score += self.get_sensory_truth(rel, "M") * 2.0
        elif act == "virar_esquerda":
            rel = self._dir_vector(self._rotate(direction, "left"))
            score += self.get_sensory_truth(rel, "A") * 2.0
            score += self.get_sensory_truth(rel, "X") * 3.0
            score += self.get_sensory_truth(rel, "M") * 2.0
        elif act == "virar_direita":
            rel = self._dir_vector(self._rotate(direction, "right"))
            score += self.get_sensory_truth(rel, "A") * 2.0
            score += self.get_sensory_truth(rel, "X") * 3.0
            score += self.get_sensory_truth(rel, "M") * 2.0
        return score

    def _action_towards_adjacent_apple(self, p, visible):
        """Atalho reativo: prioriza maçã adjacente sem custo de busca completa."""
        direction = p.get("direction", "N")
        if direction not in ("N", "E", "S", "W"):
            direction = "N"

        front = self._dir_vector(direction)
        left = self._dir_vector(self._rotate(direction, "left"))
        right = self._dir_vector(self._rotate(direction, "right"))
        back = (-front[0], -front[1])

        adjacent_apples = []
        for item in visible.values():
            rel = item.get("relative")
            if item.get("symbol") != "A":
                continue
            if isinstance(rel, tuple) and len(rel) == 2 and abs(rel[0]) + abs(rel[1]) == 1:
                adjacent_apples.append(rel)

        if not adjacent_apples:
            return None
        if front in adjacent_apples:
            return "avancar"
        if left in adjacent_apples:
            return "virar_esquerda"
        if right in adjacent_apples:
            return "virar_direita"
        if back in adjacent_apples:
            return "virar_esquerda"
        return None

    def choose_action(self, p, bot_pos, bot_dir, dungeon):
        """Escolhe ação combinando reflexos, exploração e simulação mental."""
        visible = p.get("visible_items", {})

        # Reflexo imediato: se está em cima da maçã, pegar é prioridade absoluta.
        if p.get("on_apple"):
            return "pegar"

        # Reflexo de curto alcance: alinhar para maçã adjacente.
        apple_action = self._action_towards_adjacent_apple(p, visible)
        if apple_action:
            return apple_action

        if self.apples_found >= 1:
            self.identity = "colecionador"

        # Modo exploração: testa ações diversas com filtros de segurança.
        if random.random() < self.explore_chance:
            options = ["avancar", "virar_esquerda", "virar_direita"]
            if p.get("near_monster"):
                options.append("atacar")
            if self._safe_route_score("avancar", p, visible) < -120:
                options = [act for act in options if act != "avancar"] or ["virar_esquerda", "virar_direita"]
            return random.choice(options)

        # Modo avaliação: escolhe ação com melhor score agregado.
        best_score = -10_000.0
        best_act = "avancar"
        for act in ["avancar", "virar_esquerda", "virar_direita", "pegar", "atacar"]:
            score = self._mental_simulate(act, p, visible)
            score += self._twostep_score(act, p)
            score += self._safe_route_score(act, p, visible)
            if self.rules["near_pit_means_danger"] and p.get("near_pit") and act == "avancar":
                score -= 40
            if score > best_score:
                best_score = score
                best_act = act
        return best_act

    def _mental_simulate(self, act, p, visible):
        """Simula rapidamente utilidade de uma ação com base nas crenças atuais."""
        score = 0.0
        rel = self._next_relative(act, p)
        # Combina atração por recompensa e aversão a perigo.
        score += self.get_sensory_truth(rel, "A") * 2.5
        score += self.get_sensory_truth(rel, ".") * 0.8
        score += self.get_sensory_truth(rel, "X") * 3.0
        score += self.get_sensory_truth(rel, "M") * 2.5

        # Regras descobertas ajustam o peso de certas decisões.
        if self.rules["apple_always_exists"]:
            score += 30
        if self.rules["near_pit_means_danger"] and p.get("near_pit") and act == "avancar":
            score -= 80
        if self.rules["see_apple_in_front_means_go"] and act == "avancar":
            front = self._dir_vector(p.get("direction", "N"))
            for item in visible.values():
                if item.get("symbol") == "A" and item.get("relative") == front:
                    score += 140
                    break

        # Priorização fixa por tipo de ação para guiar comportamento base.
        if act == "avancar":
            score += 20
        if act == "pegar":
            score += 260 if p.get("on_apple") else -30
        if act == "atacar":
            score += 90 if p.get("near_monster") else -25

        score += self._twostep_score(act, p) * 0.2
        return score


def main_megaia(
    Dungeon,
    print_status,
    num_lives=30,
    max_turns=200,
    post_train_turns=10,
    interactive=True,
    reset_memory_on_start=False,
    core_instance=None,
):
    """Executa treino e simulação da MegaIA, salvando memória ao final."""
    if core_instance:
        core = core_instance
        print(f"\n{ANSI_GREEN}Usando instância da MegaIA pré-treinada pelo tutorial.{ANSI_RESET}")
    else:
        core = MegaCore()
        if reset_memory_on_start:
            core.reset_memory(create_backup=True)
    
    print(f"{ANSI_MAGENTA}=== MegaIA - Treino ({num_lives} vidas rapidas) + simulacao detalhada ==={ANSI_RESET}\n")

    # Fase 1: treino rápido para consolidar regras e memória sensorial.
    for vida in range(1, num_lives + 1):
        core.explore_chance = max(0.15, core.explore_chance - 0.03)
        dungeon = Dungeon()

        while not dungeon.state["done"]:
            core.turn += 1
            p_before = dungeon.perception()
            action = core.choose_action(
                p_before,
                dungeon.state["bot"].position,
                dungeon.state["bot"].direction,
                dungeon,
            )
            result = dungeon.step(action)
            p_after = result.get("perception") if isinstance(result, dict) else None

            reason = core._normalize_reason(result.get("reason")) if isinstance(result, dict) else None
            if reason:
                core._record_event(
                    f"morreu_{reason}",
                    {"position": p_before.get("position"), "turn": core.turn},
                )
            if isinstance(result, dict) and result.get("reward", 0) > 0:
                core._record_event(
                    "recompensa",
                    {"reward": result["reward"], "turn": core.turn},
                )

            core.learn_from_turn(p_before, action, result, p_after)

        if vida % 5 == 0:
            score_color = ANSI_GREEN if dungeon.state['bot'].score >= 0 else ANSI_RED
            print(
                f"Vida {vida} concluida | Maçãs: {ANSI_GREEN}{dungeon.state['apples_collected']}{ANSI_RESET} | "
                f"Score: {score_color}{dungeon.state['bot'].score}{ANSI_RESET}"
            )
        core.finalizar_vida()

    print(f"\n{ANSI_MAGENTA}Treino concluido! Rodando simulacao detalhada turno a turno...{ANSI_RESET}\n")

    # Fase 2: simulação observável para inspeção do comportamento aprendido.
    cycle = 0
    total_turns = 0
    dungeon = Dungeon()
    while True:
        cycle += 1
        print(f"\n{ANSI_CYAN}=== Simulacao pos-treino: ciclo {cycle}, ate {post_train_turns} turnos ==={ANSI_RESET}")
        for _ in range(1, post_train_turns + 1):
            if dungeon.state["done"]:
                break
            total_turns += 1
            core.turn += 1
            p_before = dungeon.perception()
            action = core.choose_action(
                p_before,
                dungeon.state["bot"].position,
                dungeon.state["bot"].direction,
                dungeon,
            )

            print(f"\nTurno {total_turns:3d} | MegaIA escolheu: {ANSI_YELLOW}{action}{ANSI_RESET} | Identidade: {ANSI_CYAN}{core.identity}{ANSI_RESET}")
            print(dungeon.render())
            print_status(dungeon)

            result = dungeon.step(action)
            p_after = result.get("perception") if isinstance(result, dict) else None
            reason = core._normalize_reason(result.get("reason")) if isinstance(result, dict) else None
            if reason:
                core._record_event(
                    f"morreu_{reason}",
                    {"position": p_before.get("position"), "turn": core.turn},
                )
            if isinstance(result, dict) and result.get("reward", 0) > 0:
                core._record_event(
                    "recompensa",
                    {"reward": result["reward"], "turn": core.turn},
                )

            core.learn_from_turn(p_before, action, result, p_after)

            if dungeon.state["done"]:
                reason_color = ANSI_RED if dungeon.state.get('reason') else ANSI_WHITE
                score_color = ANSI_GREEN if dungeon.state['bot'].score >= 0 else ANSI_RED
                print(f"\n{ANSI_RED}Fim da simulacao! Razao: {reason_color}{dungeon.state.get('reason', 'desconhecida')}{ANSI_RESET}")
                print(
                    f"Maçãs finais: {ANSI_GREEN}{dungeon.state['apples_collected']}{ANSI_RESET} | "
                    f"Score final: {score_color}{dungeon.state['bot'].score}{ANSI_RESET}"
                )
                break

        if dungeon.state["done"]:
            if not interactive:
                print("\nModo nao interativo: encerrando apos morte/fim de mapa.")
                break
            escolha_fim = input(f"{ANSI_YELLOW}Mapa finalizado. [R]einiciar, [C]ontinuar mesmo mapa, [S]air: {ANSI_RESET}").strip().lower()
            if escolha_fim in ["s", "sair", "q", "quit"]:
                print(f"{ANSI_YELLOW}Encerrando simulacao por escolha do usuario.{ANSI_RESET}")
                break
            if escolha_fim in ["r", "reiniciar", "novo", "mapa", "n"]:
                dungeon = Dungeon()
                print(f"{ANSI_YELLOW}Reiniciando em novo mapa automatico...{ANSI_RESET}")
                continue
            print(f"{ANSI_YELLOW}Continuando o mesmo mapa por mais um ciclo...{ANSI_RESET}")

        print(f"\nCiclo concluido ({post_train_turns} turnos). Total de turnos: {total_turns}.")

        if not interactive:
            print("Modo nao interativo: encerrando apos o ciclo de simulacao.")
            break

        # Em modo interativo, o usuário decide fluxo do próximo ciclo.
        escolha = input(f"{ANSI_YELLOW}Escolha: [C]ontinuar mesmo mapa, [R]einiciar mapa automatico, [S]air: {ANSI_RESET}").strip().lower()
        if escolha in ["s", "sair", "q", "quit"]:
            print(f"{ANSI_YELLOW}Encerrando simulacao por escolha do usuario.{ANSI_RESET}")
            break
        if escolha in ["r", "reiniciar", "mapa", "novo", "n"]:
            dungeon = Dungeon()
            print(f"{ANSI_YELLOW}Reiniciando em novo mapa automatico...{ANSI_RESET}")
            continue
        print(f"{ANSI_YELLOW}Continuando o mesmo mapa por mais um ciclo...{ANSI_RESET}")

    core.finalizar_vida()
    print(f"{ANSI_GREEN}Simulacao terminada. Memoria salva para a proxima execucao.{ANSI_RESET}")
