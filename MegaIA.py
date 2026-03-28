"""Núcleo cognitivo da MegaIA.

Este módulo reúne memória, aprendizagem incremental e política de ação.
"""


"""
# Algumas tarefas à fazer:

## Veja:
- turn nao e persistido, mas timeline e world_facts sao. Isso quebra a memoria temporal entre execucoes, porque o contador volta para 0 em cada boot e depois mistura eventos de sessoes diferentes como se fossem da mesma linha do tempo. Isso aparece no codigo em MegaIA.py#L34, MegaIA.py#L237, MegaIA.py#L251 e fica evidente no JSON com turnos repetidos em megaia_memoria.json#L109. Isso pra mim e uma inconsistência real ❌.
- A sensory_memory esta saturando. Hoje 11 de 16 registros ja bateram -200 ou 200, entao ela para de distinguir intensidade e vira quase binaria na pratica. A limitacao nasce em MegaIA.py#L63, os incrementos estao em MegaIA.py#L286 e MegaIA.py#L308, e os sinais de saturacao aparecem logo no topo de megaia_memoria.json#L3.
- A representacao da memoria ainda e pobre demais para o que o AGENTS pede. A chave e so (dx, dy, symbol), entao o agente nao lembra contexto, causa, orientacao anterior, acao escolhida, confianca nem contradicoes. Isso esta em MegaIA.py#L110.
- O aprendizado esta concentrado quase todo em heuristica manual dentro de learn_from_turn, entao a memoria aprende pouco “por estrutura” e muito “por regra codificada”. Isso esta em MegaIA.py#L308.
- update_sensory_truth parece ser uma via de aprendizado pensada mas praticamente nao participa do fluxo principal. Ela existe em MegaIA.py#L294, mas o aprendizado real passa por _apply_sensory_delta via learn_from_turn.
- rules guarda conhecimento estrutural util, mas tudo e booleano. Uma unica experiencia pode cristalizar uma “verdade” sem grau de confianca, sem evidencia contraria e sem revisao. Isso esta em MegaIA.py#L41 e MegaIA.py#L212.
- timeline e world_facts acumulam bastante, mas quase nao sao consolidados em conhecimento melhor. Crescem como historico bruto, nao como memoria organizada. Isso esta em MegaIA.py#L364 e MegaIA.py#L373.
- identity ainda esta simplificada demais. Na pratica ela vira "colecionador" quando acha maca, entao ainda nao e uma memoria de si mesmo, e so um rótulo de estado. Isso esta em MegaIA.py#L35, MegaIA.py#L342 e MegaIA.py#L361.


## Tarefas:
- Separar a memoria em camadas: memoria de trabalho, episodica, semantica e identitaria.
- Trocar valor unico clampado por evidencia positiva, evidencia negativa e confianca, em vez de um numero so.
- Persistir turn, life_id e session_id para o historico temporal fazer sentido de verdade.
- Enriquecer a chave da memoria com contexto: orientacao, acao tomada, resultado observado e talvez tipo de sensor.
- Criar memoria causal explicita no formato percepcao -> acao -> resultado -> erro, alinhando com teu delta realidade-mente.
- Fazer consolidacao e compressao: episodios antigos viram regra semantica, e historico redundante deixa de crescer bruto.
- Substituir rules booleanas por regras graduais com confianca, contador de evidencias e possibilidade de contradicao.
- Construir uma memoria-grafo de verdades e relacoes, porque isso conversa muito melhor com teu AGENTS do que um dicionario isolado por simbolo.



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
    MEMORY_FORMAT = 3
    MAX_EPISODES = 240
    MAX_TIMELINE = 400
    MAX_WORKING_ITEMS = 12
    MAX_CAUSAL_LINKS = 180

    def __init__(self, memory_file=None):
        """Inicializa estado e carrega memória persistida (se existir)."""
        self.memory_file = memory_file or self.MEMORIA_FILE
        self._reset_runtime_state()
        self._carregar_memoria()
        self.session_id = max(1, self.session_id + 1)
        self._record_meta_event("nova_sessao", {"session_id": self.session_id})
        self._refresh_legacy_sensory_cache()

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
    def _default_working_memory():
        """Memoria de trabalho: o que esta ativo na atencao do turno atual."""
        return {
            "attention": [],
            "current_perception": {},
            "last_action": None,
            "last_result": {},
            "prediction_error": 0.0,
        }

    @staticmethod
    def _default_identity_state():
        """Estado identitario gradual para a IA nao ser apenas um rotulo fixo."""
        return {
            "traits": {
                "caution": 0.0,
                "collector": 0.0,
                "aggression": 0.0,
                "curiosity": 0.0,
            },
            "dominant": "sobrevivente",
            "last_shift_reason": None,
            "last_turn": 0,
        }

    @staticmethod
    def _blank_belief(kind, label):
        """Estrutura base para crencas semanticas e estruturais."""
        return {
            "kind": str(kind),
            "label": str(label),
            "positive": 0.0,
            "negative": 0.0,
            "confidence": 0.0,
            "strength": 0.0,
            "score": 0.0,
            "last_turn": 0,
            "uses": 0,
            "reward_sum": 0.0,
        }

    def _default_rule_memory(self):
        """Toda regra do agente vira uma crenca com evidencia positiva/negativa."""
        records = {}
        for rule_name in self._default_rules():
            record = self._blank_belief("rule", rule_name)
            record["rule"] = rule_name
            records[rule_name] = record
        return records

    def _serialize_semantic_memory(self):
        """Serializa memoria semantica perceptiva com evidencia e confianca."""
        records = []
        for key in sorted(self.semantic_memory):
            record = self.semantic_memory[key]
            records.append(
                {
                    "key": key,
                    "dx": int(record["dx"]),
                    "dy": int(record["dy"]),
                    "symbol": str(record["symbol"])[:1],
                    "positive": round(self._safe_float(record.get("positive"), 0.0), 4),
                    "negative": round(self._safe_float(record.get("negative"), 0.0), 4),
                    "confidence": round(self._safe_float(record.get("confidence"), 0.0), 4),
                    "strength": round(self._safe_float(record.get("strength"), 0.0), 4),
                    "score": round(self._safe_float(record.get("score"), 0.0), 2),
                    "last_turn": max(0, self._safe_int(record.get("last_turn"), 0)),
                    "uses": max(0, self._safe_int(record.get("uses"), 0)),
                    "reward_sum": round(self._safe_float(record.get("reward_sum"), 0.0), 2),
                    "last_context": record.get("last_context", {}),
                }
            )
        return records

    def _serialize_rule_memory(self):
        """Serializa memoria estrutural das regras com sua evidencia acumulada."""
        records = []
        for rule_name in sorted(self.rule_memory):
            record = self.rule_memory[rule_name]
            records.append(
                {
                    "rule": rule_name,
                    "positive": round(self._safe_float(record.get("positive"), 0.0), 4),
                    "negative": round(self._safe_float(record.get("negative"), 0.0), 4),
                    "confidence": round(self._safe_float(record.get("confidence"), 0.0), 4),
                    "strength": round(self._safe_float(record.get("strength"), 0.0), 4),
                    "score": round(self._safe_float(record.get("score"), 0.0), 2),
                    "last_turn": max(0, self._safe_int(record.get("last_turn"), 0)),
                    "uses": max(0, self._safe_int(record.get("uses"), 0)),
                    "reward_sum": round(self._safe_float(record.get("reward_sum"), 0.0), 2),
                    "last_context": record.get("last_context", {}),
                }
            )
        return records

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
    def _safe_float(value, default=0.0):
        """Converte para float de forma defensiva para manter a memoria estavel."""
        try:
            return float(value)
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

    @staticmethod
    def _parse_percept_memory_key(raw_key):
        """Interpreta chave textual de memoria no formato dx:dy:simbolo."""
        if not isinstance(raw_key, str):
            return None
        parts = raw_key.split(":")
        if len(parts) != 3:
            return None
        try:
            dx = int(parts[0])
            dy = int(parts[1])
        except (TypeError, ValueError):
            return None
        symbol = str(parts[2])[:1]
        if not symbol:
            return None
        return (dx, dy, symbol)

    def _percept_memory_key(self, relative, symbol):
        """Transforma percepcao relativa em chave estavel de memoria semantica."""
        return f"{int(relative[0])}:{int(relative[1])}:{str(symbol)[:1]}"

    def _refresh_belief(self, record):
        """Recalcula forca, confianca e score de uma crenca apos nova evidencia."""
        positive = max(0.0, self._safe_float(record.get("positive"), 0.0))
        negative = max(0.0, self._safe_float(record.get("negative"), 0.0))
        total = positive + negative
        if total <= 0:
            record["confidence"] = 0.0
            record["strength"] = 0.0
            record["score"] = 0.0
            return

        strength = (positive - negative) / total
        confidence = min(1.0, total / 8.0)
        record["confidence"] = round(confidence, 4)
        record["strength"] = round(strength, 4)
        record["score"] = round(strength * confidence * 100.0, 2)

    def _refresh_legacy_sensory_cache(self):
        """Mantem uma projecao simples da memoria nova para compatibilidade."""
        legacy = {}
        for record in self.semantic_memory.values():
            key = (record["dx"], record["dy"], record["symbol"])
            legacy[key] = self._clamp_truth(record.get("score", 0.0))
        self.sensory_memory = legacy

    def _sync_rules_from_memory(self):
        """Traduz regras graduais em flags booleanas para o restante do agente."""
        active_rules = self._default_rules()
        for rule_name in active_rules:
            record = self.rule_memory.get(rule_name)
            score = self._safe_float(record.get("score"), 0.0) if record else 0.0
            active_rules[rule_name] = score >= 18.0
        self.rules = active_rules

    def _record_meta_event(self, event_type, data):
        """Registra eventos de sessao/vida sem contaminar world_facts."""
        event = {
            "turn": self.turn,
            "session_id": self.session_id,
            "life_id": self.life_id,
            "type": str(event_type),
            "data": data if isinstance(data, dict) else {},
        }
        self.timeline.append(event)
        self.timeline = self.timeline[-self.MAX_TIMELINE:]

    def _ensure_percept_record(self, relative, symbol):
        """Cria ou recupera a crenca perceptiva referente a uma posicao relativa."""
        dx = int(relative[0])
        dy = int(relative[1])
        symbol = str(symbol)[:1]
        key = self._percept_memory_key((dx, dy), symbol)
        if key not in self.semantic_memory:
            record = self._blank_belief("percept", symbol)
            record["dx"] = dx
            record["dy"] = dy
            record["symbol"] = symbol
            self.semantic_memory[key] = record
        return self.semantic_memory[key]

    def _ensure_rule_record(self, rule_name):
        """Cria ou recupera a crenca estrutural de uma regra do mundo."""
        if rule_name not in self.rule_memory:
            record = self._blank_belief("rule", rule_name)
            record["rule"] = rule_name
            self.rule_memory[rule_name] = record
        return self.rule_memory[rule_name]

    def _apply_signal_to_record(self, record, signal, weight=1.0, reward=0, context=None):
        """Aplica nova evidencia a uma crenca sem perder nuance por saturacao."""
        magnitude = max(
            0.25,
            min(
                6.0,
                abs(self._safe_float(signal, 0.0))
                * max(0.1, self._safe_float(weight, 1.0)),
            ),
        )
        if signal >= 0:
            record["positive"] = round(self._safe_float(record.get("positive"), 0.0) + magnitude, 4)
        else:
            record["negative"] = round(self._safe_float(record.get("negative"), 0.0) + magnitude, 4)
        record["last_turn"] = self.turn
        record["uses"] = max(0, self._safe_int(record.get("uses"), 0)) + 1
        record["reward_sum"] = round(
            self._safe_float(record.get("reward_sum"), 0.0) + self._safe_float(reward, 0.0),
            2,
        )
        if isinstance(context, dict):
            record["last_context"] = context
        self._refresh_belief(record)

    def _remember_percept(self, relative, symbol, signal, weight=1.0, reward=0, context=None):
        """Atualiza memoria semantica perceptiva a partir de uma experiencia."""
        record = self._ensure_percept_record(relative, symbol)
        self._apply_signal_to_record(record, signal, weight=weight, reward=reward, context=context)
        self._refresh_legacy_sensory_cache()

    def _remember_rule(self, rule_name, signal, weight=1.0, reward=0, context=None):
        """Atualiza memoria estrutural das regras com evidencia gradual."""
        record = self._ensure_rule_record(rule_name)
        self._apply_signal_to_record(record, signal, weight=weight, reward=reward, context=context)
        self._sync_rules_from_memory()

    def _symbol_prior(self, symbol):
        """Generaliza por simbolo quando a posicao exata ainda nao foi aprendida."""
        scores = []
        for record in self.semantic_memory.values():
            if record.get("symbol") == symbol:
                scores.append(self._safe_float(record.get("score"), 0.0))
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

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
                    return self._parse_percept_memory_key(cur)
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
        self.semantic_memory = {}
        self.rule_memory = self._default_rule_memory()
        self.rules = self._default_rules()
        self.world_facts = self._default_world_facts()
        self.working_memory = self._default_working_memory()
        self.episodic_memory = []
        self.causal_graph = {}
        self.timeline = []
        self.turn = 0
        self.session_id = 0
        self.life_id = 0
        self.identity_state = self._default_identity_state()
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

            # Persistimos turno, sessao e vida para o historico nao misturar execucoes.
            self.turn = max(0, self._safe_int(data.get("turn"), self.turn))
            self.session_id = max(0, self._safe_int(data.get("session_id"), self.session_id))
            self.life_id = max(0, self._safe_int(data.get("life_id"), self.life_id))

            # A memória sensorial pode vir em formatos diferentes entre versões.
            self.sensory_memory = self._parse_sensory_memory(data.get("sensory_memory", {}))

            self.semantic_memory = {}
            semantic_payload = data.get("semantic_memory", [])
            if isinstance(semantic_payload, list):
                for entry in semantic_payload:
                    if not isinstance(entry, dict):
                        continue
                    rel = self._normalize_memory_key(
                        (entry.get("dx"), entry.get("dy"), entry.get("symbol"))
                    )
                    if rel is None:
                        rel = self._parse_percept_memory_key(entry.get("key"))
                    if rel is None:
                        continue
                    record = self._blank_belief("percept", rel[2])
                    record["dx"] = rel[0]
                    record["dy"] = rel[1]
                    record["symbol"] = rel[2]
                    record["positive"] = max(0.0, self._safe_float(entry.get("positive"), 0.0))
                    record["negative"] = max(0.0, self._safe_float(entry.get("negative"), 0.0))
                    record["last_turn"] = max(0, self._safe_int(entry.get("last_turn"), 0))
                    record["uses"] = max(0, self._safe_int(entry.get("uses"), 0))
                    record["reward_sum"] = round(self._safe_float(entry.get("reward_sum"), 0.0), 2)
                    if isinstance(entry.get("last_context"), dict):
                        record["last_context"] = entry["last_context"]
                    self._refresh_belief(record)
                    self.semantic_memory[self._percept_memory_key((rel[0], rel[1]), rel[2])] = record

            loaded_rules = data.get("rules", {})
            merged_rules = self._default_rules()
            if isinstance(loaded_rules, dict):
                for k in merged_rules:
                    if k in loaded_rules:
                        merged_rules[k] = bool(loaded_rules[k])
            self.rules = merged_rules
            self.rule_memory = self._default_rule_memory()
            rule_payload = data.get("rule_memory", [])
            if isinstance(rule_payload, list):
                for entry in rule_payload:
                    if not isinstance(entry, dict):
                        continue
                    rule_name = str(entry.get("rule", ""))
                    if not rule_name:
                        continue
                    record = self._ensure_rule_record(rule_name)
                    record["positive"] = max(0.0, self._safe_float(entry.get("positive"), 0.0))
                    record["negative"] = max(0.0, self._safe_float(entry.get("negative"), 0.0))
                    record["last_turn"] = max(0, self._safe_int(entry.get("last_turn"), 0))
                    record["uses"] = max(0, self._safe_int(entry.get("uses"), 0))
                    record["reward_sum"] = round(self._safe_float(entry.get("reward_sum"), 0.0), 2)
                    if isinstance(entry.get("last_context"), dict):
                        record["last_context"] = entry["last_context"]
                    self._refresh_belief(record)

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
            self.timeline = self.timeline[-self.MAX_TIMELINE:]
            self.working_memory = (
                data.get("working_memory", {})
                if isinstance(data.get("working_memory"), dict)
                else self._default_working_memory()
            )
            for key, value in self._default_working_memory().items():
                self.working_memory.setdefault(key, value)
            if not isinstance(self.working_memory.get("attention"), list):
                self.working_memory["attention"] = []
            self.working_memory["attention"] = self.working_memory["attention"][:self.MAX_WORKING_ITEMS]
            self.episodic_memory = (
                data.get("episodic_memory", [])
                if isinstance(data.get("episodic_memory"), list)
                else []
            )[-self.MAX_EPISODES:]
            self.causal_graph = data.get("causal_graph", {}) if isinstance(data.get("causal_graph"), dict) else {}
            loaded_identity_state = data.get("identity_state", {})
            if isinstance(loaded_identity_state, dict):
                self.identity_state = self._default_identity_state()
                traits = loaded_identity_state.get("traits", {})
                if isinstance(traits, dict):
                    for trait in self.identity_state["traits"]:
                        self.identity_state["traits"][trait] = round(
                            self._safe_float(traits.get(trait), 0.0),
                            4,
                        )
                self.identity_state["dominant"] = str(
                    loaded_identity_state.get("dominant", self.identity_state["dominant"])
                )
                self.identity_state["last_shift_reason"] = loaded_identity_state.get("last_shift_reason")
                self.identity_state["last_turn"] = max(
                    0,
                    self._safe_int(loaded_identity_state.get("last_turn"), 0),
                )
            self.identity = str(data.get("identity", self.identity))
            self.apples_found = max(0, self._safe_int(data.get("apples_found", self.apples_found), 0))
            if not self.semantic_memory:
                for (dx, dy, symbol), value in self.sensory_memory.items():
                    signal = 1.0 if value > 0 else -1.0
                    weight = max(0.5, min(5.0, abs(value) / 40.0))
                    self._remember_percept(
                        (dx, dy),
                        symbol,
                        signal,
                        weight=weight,
                        reward=value,
                        context={"source": "legacy"},
                    )
            self._sync_rules_from_memory()
            self._refresh_legacy_sensory_cache()
            print(f"{ANSI_GREEN}Memoria da MegaIA recuperada do arquivo.{ANSI_RESET}")
        except Exception as e:
            print(f"{ANSI_RED}Erro ao carregar memoria: {e}. Iniciando do zero.{ANSI_RESET}")

    def _salvar_memoria(self):
        """Persiste estado cognitivo completo para continuidade entre execuções."""
        data = {
            "memory_format": self.MEMORY_FORMAT,
            "turn": self.turn,
            "session_id": self.session_id,
            "life_id": self.life_id,
            "sensory_memory": self._serialize_sensory_memory(),
            "semantic_memory": self._serialize_semantic_memory(),
            "rule_memory": self._serialize_rule_memory(),
            "working_memory": self.working_memory,
            "episodic_memory": self.episodic_memory,
            "causal_graph": self.causal_graph,
            "rules": self.rules,
            "world_facts": self.world_facts,
            "timeline": self.timeline[-self.MAX_TIMELINE:],
            "identity": self.identity,
            "identity_state": self.identity_state,
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

    def begin_life(self, label="vida"):
        """Marca nova vida/ciclo para dar contexto temporal ao aprendizado."""
        self.life_id += 1
        self.working_memory = self._default_working_memory()
        self._record_meta_event("nova_vida", {"label": label, "life_id": self.life_id})

    def finalizar_vida(self):
        """Hook de finalização: salva memória ao fim de cada vida/ciclo."""
        self._salvar_memoria()

    def get_sensory_truth(self, relative, symbol):
        """Consulta o valor de verdade atual para uma percepção relativa."""
        key = self._percept_memory_key(relative, symbol)
        record = self.semantic_memory.get(key)
        if record:
            return self._clamp_truth(record.get("score", 0.0))
        return self._clamp_truth(self._symbol_prior(str(symbol)[:1]) * 0.35)

    def _apply_sensory_delta(self, relative, symbol, delta):
        """Aplica ajuste incremental e clampado em um item da memória sensorial."""
        if delta == 0:
            return
        signal = 1.0 if delta > 0 else -1.0
        weight = max(0.5, min(5.0, abs(self._safe_float(delta, 0.0)) / 40.0))
        self._remember_percept(
            relative,
            symbol,
            signal,
            weight=weight,
            reward=delta,
            context={"source": "legacy_delta"},
        )

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

    def _ingest_perception(self, p):
        """Atualiza memoria de trabalho com os itens mais relevantes do turno."""
        if not isinstance(p, dict):
            self.working_memory = self._default_working_memory()
            return

        attention = []
        visible = p.get("visible_items", {})
        if isinstance(visible, dict):
            for item in visible.values():
                if not isinstance(item, dict):
                    continue
                rel = item.get("relative")
                symbol = str(item.get("symbol", "?"))[:1]
                if not (isinstance(rel, tuple) and len(rel) == 2):
                    continue
                distance = abs(rel[0]) + abs(rel[1])
                weight = max(0.5, 3.0 - distance)
                if symbol in ("X", "M"):
                    weight += 2.5
                elif symbol == "A":
                    weight += 2.0
                attention.append(
                    {
                        "symbol": symbol,
                        "relative": [int(rel[0]), int(rel[1])],
                        "weight": round(weight, 3),
                    }
                )
        attention.sort(key=lambda item: item["weight"], reverse=True)
        self.working_memory["attention"] = attention[:self.MAX_WORKING_ITEMS]
        self.working_memory["current_perception"] = {
            "direction": p.get("direction"),
            "position": list(p.get("position")) if isinstance(p.get("position"), tuple) else p.get("position"),
            "near_monster": bool(p.get("near_monster")),
            "near_pit": bool(p.get("near_pit")),
            "near_apple": bool(p.get("near_apple")),
            "on_apple": bool(p.get("on_apple")),
            "on_monster": bool(p.get("on_monster")),
            "on_pit": bool(p.get("on_pit")),
        }

    def _record_episode(self, p_before, action, result, p_after):
        """Guarda resumo do turno na memoria episodica."""
        reward = self._safe_int(result.get("reward", 0), 0)
        reason = self._normalize_reason(result.get("reason"))
        episode = {
            "turn": self.turn,
            "session_id": self.session_id,
            "life_id": self.life_id,
            "action": action,
            "reward": reward,
            "reason": reason,
            "direction_before": p_before.get("direction"),
            "position_before": list(p_before.get("position")) if isinstance(p_before.get("position"), tuple) else p_before.get("position"),
            "near_monster": bool(p_before.get("near_monster")),
            "near_pit": bool(p_before.get("near_pit")),
            "near_apple": bool(p_before.get("near_apple")),
            "on_apple_before": bool(p_before.get("on_apple")),
            "on_apple_after": bool(p_after.get("on_apple")),
            "attention": self.working_memory.get("attention", [])[:4],
        }
        self.episodic_memory.append(episode)
        self.episodic_memory = self.episodic_memory[-self.MAX_EPISODES:]
        self.working_memory["last_action"] = action
        self.working_memory["last_result"] = {"reward": reward, "reason": reason}

    def _record_causal_link(self, p_before, action, result):
        """Consolida elo simples de causalidade entre percepcao, acao e resultado."""
        reward = self._safe_int(result.get("reward", 0), 0)
        reason = self._normalize_reason(result.get("reason")) or "continua"
        focus_tokens = []
        for item in self.working_memory.get("attention", [])[:3]:
            focus_tokens.append(f"{item['symbol']}@{item['relative'][0]},{item['relative'][1]}")
        if p_before.get("near_pit"):
            focus_tokens.append("near_pit")
        if p_before.get("near_monster"):
            focus_tokens.append("near_monster")
        if p_before.get("near_apple"):
            focus_tokens.append("near_apple")
        focus = ",".join(focus_tokens[:4]) or "sem_foco"
        key = f"{focus}|{action}|{reason}"
        if key not in self.causal_graph:
            self.causal_graph[key] = {"count": 0, "reward_sum": 0.0, "last_turn": 0}
        self.causal_graph[key]["count"] += 1
        self.causal_graph[key]["reward_sum"] = round(
            self._safe_float(self.causal_graph[key].get("reward_sum"), 0.0) + reward,
            2,
        )
        self.causal_graph[key]["last_turn"] = self.turn

    def _update_identity_state(self, p_before, action, reward, reason):
        """Molda a identidade com base no que o agente faz e no que colhe."""
        traits = self.identity_state["traits"]
        for trait in traits:
            traits[trait] = round(self._safe_float(traits[trait], 0.0) * 0.985, 4)

        if action == "pegar" and reward > 0:
            traits["collector"] = round(traits["collector"] + 1.4, 4)
        if action == "atacar" and reward > 0:
            traits["aggression"] = round(traits["aggression"] + 1.0, 4)
        if action in ("avancar", "virar_esquerda", "virar_direita") and reason is None:
            traits["curiosity"] = round(traits["curiosity"] + 0.18, 4)
        if reason in ("poco", "monstro", "fome"):
            traits["caution"] = round(traits["caution"] + 1.0, 4)
        if p_before.get("near_pit") and action != "avancar" and reason is None:
            traits["caution"] = round(traits["caution"] + 0.2, 4)

        dominant_trait = max(traits, key=lambda name: traits[name])
        mapping = {
            "collector": "colecionador",
            "aggression": "combatente",
            "curiosity": "explorador",
            "caution": "sobrevivente",
        }
        new_identity = mapping.get(dominant_trait, "sobrevivente")
        if new_identity != self.identity_state.get("dominant"):
            self.identity_state["last_shift_reason"] = {
                "turn": self.turn,
                "action": action,
                "reason": reason,
                "reward": reward,
            }
        self.identity_state["dominant"] = new_identity
        self.identity_state["last_turn"] = self.turn
        self.identity = new_identity

    def learn_from_turn(self, p_before, action, result, p_after):
        """Atualiza crenças e identidade com base na transição de um turno."""
        if not isinstance(p_before, dict):
            return
        if not isinstance(result, dict):
            return
        if not isinstance(p_after, dict):
            p_after = {}

        self._ingest_perception(p_before)
        self._record_episode(p_before, action, result, p_after)
        self._record_causal_link(p_before, action, result)

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
                self._remember_rule(
                    "near_pit_means_danger",
                    1.0,
                    weight=2.5,
                    reward=reward,
                    context={"near_pit": bool(p_before.get("near_pit"))},
                )
            elif reason == "monstro" or p_after.get("on_monster"):
                self._apply_sensory_delta(front_rel, "M", -150)
                self._remember_rule(
                    "monster_chases",
                    1.0,
                    weight=2.0,
                    reward=reward,
                    context={"near_monster": bool(p_before.get("near_monster"))},
                )
            elif p_after.get("on_apple"):
                self._apply_sensory_delta(front_rel, "A", 90)
                self._remember_rule(
                    "see_apple_in_front_means_go",
                    1.0,
                    weight=2.0,
                    reward=reward,
                    context={"front_rel": [front_rel[0], front_rel[1]]},
                )
            else:
                self._apply_sensory_delta(front_rel, ".", 10)

        elif action == "pegar":
            if reward > 0 and p_before.get("on_apple"):
                self._apply_sensory_delta((0, 0), "A", 140)
                self.apples_found += 1
                self._remember_rule(
                    "apple_always_exists",
                    0.7,
                    weight=1.5,
                    reward=reward,
                    context={"apples_found": self.apples_found},
                )
                self._remember_rule(
                    "apple_respawns",
                    0.9,
                    weight=1.6,
                    reward=reward,
                    context={"apples_found": self.apples_found},
                )
            else:
                self._apply_sensory_delta((0, 0), "A", -30)

        elif action == "atacar":
            if reward > 0:
                self._apply_sensory_delta(front_rel, "M", 30)
                self._remember_rule(
                    "monster_chases",
                    0.5,
                    weight=1.2,
                    reward=reward,
                    context={"attack_success": True},
                )
            else:
                self._apply_sensory_delta(front_rel, "M", -35)

        if reason == "fome":
            self._remember_rule(
                "hunger_decreases",
                1.0,
                weight=2.4,
                reward=reward,
                context={"reason": reason},
            )
            self._apply_sensory_delta((0, 0), ".", -60)

        # Após encontrar maçã, identidade migra para perfil mais coletor.
        if self.apples_found >= 1:
            self.identity = "colecionador"

        self._update_identity_state(p_before, action, reward, reason)
        self._sync_rules_from_memory()

    def _record_event(self, event_type, data):
        """Registra evento no timeline e atualiza frequência em world_facts."""
        normalized = self._normalize_event_key(event_type) or event_type
        self.timeline.append(
            {
                "turn": self.turn,
                "session_id": self.session_id,
                "life_id": self.life_id,
                "type": normalized,
                "data": data,
            }
        )
        self.timeline = self.timeline[-self.MAX_TIMELINE:]
        if normalized not in self.world_facts:
            self.world_facts[normalized] = {"count": 0, "turns": []}
        self.world_facts[normalized]["count"] += 1
        self.world_facts[normalized]["turns"].append(self.turn)
        self.world_facts[normalized]["turns"] = self.world_facts[normalized]["turns"][-self.MAX_TIMELINE:]

    def _temporal_risk(self, event_type, window=10):
        """Estima risco temporal recente de um evento com base em frequência/recência."""
        recent = []
        lower_bound = self.turn - window
        for event in reversed(self.timeline):
            if not isinstance(event, dict):
                continue
            if event.get("type") != event_type:
                continue
            event_turn = self._safe_int(event.get("turn"), -1)
            if event_turn < lower_bound:
                break
            if event_turn <= self.turn:
                recent.append(event_turn)
        if not recent:
            return 0.0
        freq = len(recent) / max(1, window)
        recency = max(0.0, 1 - ((self.turn - recent[0]) / window))
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
    num_lives=80,
    max_turns=500,
    post_train_turns=10,
    interactive=True,
    reset_memory_on_start=False,
    core_instance=None,
):
    """Executa treino e simulação da MegaIA, salvando memória ao final."""
    """ISSO serve para que ele não fique morrendo à toa no "Real", somente nesse treino, será como um tutorial"""
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
        core.begin_life(label=f"treino_{vida}")
        core.explore_chance = max(0.15, core.explore_chance - 0.03)
        dungeon = Dungeon()
        life_turns = 0

        while not dungeon.state["done"] and life_turns < max_turns:
            life_turns += 1
            core.turn += 1
            p_before = dungeon.perception()
            action = core.choose_action(
                p_before,
                dungeon.state["bot"].position,
                dungeon.state["bot"].direction,
                dungeon,
            )
            result = dungeon.step(action)
            if action not in ("avancar", "atacar"):
                core.turn -= 1
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
    core.begin_life(label="simulacao_pos_treino")
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
            if action not in ("avancar", "atacar"):
                core.turn -= 1
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
                core.begin_life(label="reinicio_mapa")
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
            core.begin_life(label="reinicio_mapa")
            dungeon = Dungeon()
            print(f"{ANSI_YELLOW}Reiniciando em novo mapa automatico...{ANSI_RESET}")
            continue
        print(f"{ANSI_YELLOW}Continuando o mesmo mapa por mais um ciclo...{ANSI_RESET}")

    core.finalizar_vida()
    print(f"{ANSI_GREEN}Simulacao terminada. Memoria salva para a proxima execucao.{ANSI_RESET}")
