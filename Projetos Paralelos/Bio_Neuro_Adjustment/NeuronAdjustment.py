import numpy as np
import matplotlib.pyplot as plt

# ====================== PARÂMETROS DA STDP ======================
A_plus  = 0.005    # Força máxima de LTP (fortalecimento)
A_minus = 0.0055   # Força máxima de LTD (enfraquecimento) — ligeiramente maior para estabilidade
tau_plus  = 20.0   # ms — quanto tempo o efeito positivo dura
tau_minus = 20.0   # ms

def stdp_delta_w(delta_t):
    """Calcula Δw segundo a regra STDP"""
    if delta_t > 0:
        return A_plus * np.exp(-delta_t / tau_plus)      # pré antes de pós → fortalece
    else:
        return -A_minus * np.exp(delta_t / tau_minus)    # pós antes de pré → enfraquece

# ====================== 1. PLOT DA CURVA STDP ======================
dt_values = np.linspace(-100, 100, 1000)
delta_w_values = np.array([stdp_delta_w(t) for t in dt_values])

plt.figure(figsize=(10, 6))
plt.plot(dt_values, delta_w_values, 'b-', linewidth=2.5, label='Regra STDP')
plt.axvline(0, color='black', linestyle='--', alpha=0.7)
plt.axhline(0, color='black', linestyle='--', alpha=0.7)
plt.xlabel('Δt = t_pós - t_pré (milissegundos)')
plt.ylabel('Mudança no peso sináptico (Δw)')
plt.title('Curva de Aprendizado STDP\n(A+ = {:.4f}, A- = {:.4f}, τ = {} ms)'.format(
    A_plus, A_minus, int(tau_plus)))
plt.grid(True, alpha=0.3)

# Anotações explicativas
plt.text(25, 0.0032, 'LTP\n(fortalece)\npré → pós', color='green', fontsize=12, ha='center')
plt.text(-55, -0.0038, 'LTD\n(enfraquece)\npré depois de pós', color='red', fontsize=12, ha='center')

plt.legend()
plt.tight_layout()
plt.show()

# ====================== 2. SIMULAÇÃO DE APRENDIZADO REAL ======================
np.random.seed(42)          # para resultados reproduzíveis
num_pairs = 200             # número de pares pré/pós (pense em 200 repetições de um estímulo)

# Geramos tempos de spikes (em ms)
pre_times  = np.random.uniform(0, 100, num_pairs)
post_times = pre_times + np.random.normal(5, 18, num_pairs)  # em média o pós vem 5 ms depois (causalidade)

weights = np.full(num_pairs, 0.5)   # peso inicial de cada sinapse = 0.5

for i in range(num_pairs):
    delta_t = post_times[i] - pre_times[i]
    dw = stdp_delta_w(delta_t)
    weights[i] += dw                    # atualiza o peso

# Resultados
print("\n=== RESULTADOS DA SIMULAÇÃO ===")
print(f"Peso médio inicial:          {0.5:.4f}")
print(f"Peso médio após {num_pairs} repetições: {np.mean(weights):.4f}")
print(f"Mudança média no peso:       {np.mean(weights) - 0.5:.4f}")
print(f"Média de Δt (timing):        {np.mean(post_times - pre_times):.2f} ms")

# Histograma dos timings para você ver visualmente
plt.figure(figsize=(8, 5))
plt.hist(post_times - pre_times, bins=30, color='skyblue', edgecolor='black')
plt.axvline(0, color='red', linestyle='--', label='Δt = 0')
plt.xlabel('Δt = t_pós - t_pré (ms)')
plt.ylabel('Número de ocorrências')
plt.title('Distribuição dos timings na simulação')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()