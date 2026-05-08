# Grok: https://grok.com/share/bGVnYWN5_76d769d3-78eb-4765-826b-a08c6ca03bdf
# ChatGPT: https://chatgpt.com/share/69e03f48-a360-83e9-b235-ad5c8fa8eafe


import random
import statistics

# -------------------------
# CONFIG
# -------------------------
CYCLES = 20
SEEDS = [42, 43, 44]

# -------------------------
# STATE
# -------------------------
class SystemState:
    def __init__(self):
        self.energy = random.uniform(0.4, 0.6)
        self.horizon = 3
        self.coherence = random.uniform(0.5, 0.7)
        self.diversity = random.uniform(0.6, 0.9)
        self.ofi = random.uniform(0.4, 0.6)
        self.attention = 1.0
        self.regime = "stable"

# -------------------------
# LAW BASE
# -------------------------
class Law:
    def __init__(self, name, activation, prediction, tolerance):
        self.name = name
        self.activation = activation
        self.prediction = prediction
        self.tolerance = tolerance
        self.confidence = 0.6
        self.fail_streak = 0

    def evaluate(self, state, observed):
        if not self.activation(state):
            return

        pred = self.prediction(state)
        error = abs(pred - observed)

        if error < self.tolerance:
            self.confidence += 0.05 * (1 - self.confidence)
            self.fail_streak = 0
        else:
            self.confidence -= 0.08 * self.confidence
            self.fail_streak += 1

    def alive(self):
        return self.fail_streak < 4 and self.confidence > 0.3

# -------------------------
# LAWS (simplified real behavior)
# -------------------------
def create_laws():
    return [
        Law(
            "Escassez",
            lambda s: s.attention < 0.6,
            lambda s: s.diversity - 0.15,
            0.12
        ),
        Law(
            "Horizonte",
            lambda s: s.energy > 0.7,
            lambda s: s.horizon - 1,
            0.8
        ),
        Law(
            "Coerencia",
            lambda s: s.coherence > 0.75 or s.coherence < 0.4,
            lambda s: s.ofi - 0.1,
            0.1
        )
    ]

# -------------------------
# REGIME DETECTION
# -------------------------
def detect_regime(state):
    if state.energy > 0.7:
        return "exploratory"
    if state.coherence < 0.4:
        return "adversarial"
    return "stable"

# -------------------------
# STEP
# -------------------------
def step(state):
    prev = (state.energy, state.horizon, state.coherence)

    # stochastic evolution
    state.energy = max(0, min(1, state.energy + random.uniform(-0.1, 0.1)))
    state.coherence = max(0, min(1, state.coherence + random.uniform(-0.1, 0.1)))
    state.diversity = max(0, min(1, state.diversity + random.uniform(-0.1, 0.1)))

    # horizon adapts
    if state.energy > 0.7:
        state.horizon = max(1, state.horizon - 1)
    else:
        state.horizon = min(5, state.horizon + 0.5)

    # OFI (objective)
    state.ofi = (
        0.4 * state.diversity +
        0.3 * state.coherence +
        0.3 * (1 - abs(state.energy - 0.5))
    )

    # transition cost
    delta = sum(abs(a - b) for a, b in zip(prev, (state.energy, state.horizon, state.coherence)))
    transition_cost = delta / 3

    # prediction noise (reality gap)
    predicted_ofi = state.ofi + random.uniform(-0.1, 0.1)
    reality_gap = abs(predicted_ofi - state.ofi)

    return transition_cost, reality_gap

# -------------------------
# SIMULATION
# -------------------------
def run(seed):
    random.seed(seed)
    state = SystemState()
    laws = create_laws()

    history = []

    for cycle in range(CYCLES):
        state.regime = detect_regime(state)

        transition_cost, reality_gap = step(state)

        # evaluate laws
        for law in laws:
            observed = state.ofi
            law.evaluate(state, observed)

        # prune laws
        laws = [l for l in laws if l.alive()]

        history.append({
            "ofi": state.ofi,
            "energy": state.energy,
            "regime": state.regime,
            "laws": len(laws),
            "confidence": statistics.mean([l.confidence for l in laws]) if laws else 0,
            "transition_cost": transition_cost,
            "reality_gap": reality_gap
        })

        print(f"[Seed {seed} | Cycle {cycle}] OFI={state.ofi:.2f} Regime={state.regime} Laws={len(laws)} Gap={reality_gap:.2f}")

    return history

# -------------------------
# RUN ALL
# -------------------------
all_runs = [run(s) for s in SEEDS]