import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

df_rgps = pd.read_excel('tabela_CCE002.xlsx', sheet_name='Projeções')

ano_calc_inicio = 2026
ano_calc_fim = 2060
ano_base = 2025
ano_alvo = 2060   # ano em que a decomposição será reportada

df_base = df_rgps[(df_rgps['Exercício'] >= ano_base) & (df_rgps['Exercício'] <= ano_calc_fim)].copy()
df_base = df_base.set_index('Exercício')

sigma_frac_R   = 0.010
sigma_frac_D   = 0.008
sigma_frac_PIB = 0.0035

corr = np.array([
    [ 1.0, -0.2,  0.6],
    [-0.2,  1.0, -0.3],
    [ 0.6, -0.3,  1.0],
])
sigma = np.array([sigma_frac_R, sigma_frac_D, sigma_frac_PIB])
Sigma_base = np.outer(sigma, sigma) * corr
L_base = np.linalg.cholesky(Sigma_base)

num_simulacoes = 1000

def rodar_simulacao(ativa_R, ativa_D, ativa_PIB, correlacionado, seed):
    """Roda o Monte Carlo com subconjuntos de choques ativos/desativados."""
    rng = np.random.default_rng(seed)
    resultados = []
    for simulacao in range(num_simulacoes):
        for ano in range(ano_calc_inicio, ano_calc_fim + 1):
            R_pldo   = df_base.loc[ano, 'Receita']
            D_pldo   = df_base.loc[ano, 'Despesa']
            PIB_pldo = df_base.loc[ano, 'PIB']
            horizonte = ano - ano_base

            if correlacionado:
                z = rng.standard_normal(3)
                eps_R, eps_D, eps_PIB = np.sqrt(horizonte) * (L_base @ z)
            else:
                eps_R   = rng.normal(0, sigma_frac_R   * np.sqrt(horizonte))
                eps_D   = rng.normal(0, sigma_frac_D   * np.sqrt(horizonte))
                eps_PIB = rng.normal(0, sigma_frac_PIB * np.sqrt(horizonte))

            if not ativa_R:   eps_R   = 0.0
            if not ativa_D:   eps_D   = 0.0
            if not ativa_PIB: eps_PIB = 0.0

            R_sim   = R_pldo   * (1 + eps_R)
            D_sim   = D_pldo   * (1 + eps_D)
            PIB_sim = PIB_pldo * (1 + eps_PIB)

            NFin_pct_sim = ((D_sim - R_sim) / PIB_sim) * 100

            if ano == ano_alvo:
                resultados.append(NFin_pct_sim)

    return np.array(resultados)

resultado_R   = rodar_simulacao(True,  False, False, correlacionado=False, seed=1)
resultado_D   = rodar_simulacao(False, True,  False, correlacionado=False, seed=2)
resultado_PIB = rodar_simulacao(False, False, True,  correlacionado=False, seed=3)
resultado_TOT = rodar_simulacao(True,  True,  True,  correlacionado=True,  seed=42)

def largura_ic90(vetor):
    p5, p95 = np.quantile(vetor, [0.05, 0.95])
    return p95 - p5, p5, p95

larg_R,   p5_R,   p95_R   = largura_ic90(resultado_R)
larg_D,   p5_D,   p95_D   = largura_ic90(resultado_D)
larg_PIB, p5_PIB, p95_PIB = largura_ic90(resultado_PIB)
larg_TOT, p5_TOT, p95_TOT = largura_ic90(resultado_TOT)

print(f"\nAno de referência: {ano_alvo}\n")
print(f"Necessidade de Financiamento do RGPS (% do PIB) \n")
print(f"{'Cenário':<25}{'P5':>10}{'P95':>10}{'Largura':>12}")
print("-" * 60)

for nome, larg, p5, p95 in [
    ('Somente Receita (R)',  larg_R,   p5_R,   p95_R),
    ('Somente Despesa (D)', larg_D,   p5_D,   p95_D),
    ('Somente PIB',         larg_PIB, p5_PIB, p95_PIB),
    ('Cenário completo',    larg_TOT, p5_TOT, p95_TOT),
]:
    print(f"{nome:<25}{p5:>9.2f}%{p95:>9.2f}%{larg:>11.2f} p.p.")

# Gráfico
fig, ax = plt.subplots(figsize=(8,5))
fontes   = ['PIB', 'Despesa (D)', 'Receita (R)']
p5_vals  = [p5_PIB,  p5_D,  p5_R]
p95_vals = [p95_PIB, p95_D, p95_R]
medias   = [np.mean(resultado_PIB), np.mean(resultado_D), np.mean(resultado_R)]
cores    = ['darkorange', 'firebrick', 'steelblue']

y_pos = np.arange(len(fontes))
larguras_barra = [p95 - p5 for p5, p95 in zip(p5_vals, p95_vals)]

ax.barh(y_pos, larguras_barra, left=p5_vals, color=cores, alpha=0.6, height=0.5)
ax.scatter(medias, y_pos, color='black', zorder=3, s=40, label='Média')

for i, (p5, p95, m) in enumerate(zip(p5_vals, p95_vals, medias)):
    ax.text(p5 - 0.05, i, f'P5: {p5:.2f}', va='center', ha='right', fontsize=9)
    ax.text(p95 + 0.05, i, f'P95: {p95:.2f}', va='center', ha='left', fontsize=9)

ax.set_yticks(y_pos)
ax.set_yticklabels(fontes)
ax.set_xlabel('Necessidade de Financiamento % PIB em 2060')
ax.set_title('Decomposição da incerteza (Faixa P5–P95) isolado por variável')
ax.grid(True, axis='x', linestyle='--', alpha=0.6)
ax.legend(loc='lower right')

xmin = min(p5_vals) - 0.6
xmax = max(p95_vals) + 0.6
ax.set_xlim(xmin, xmax)

plt.tight_layout()
plt.savefig('decomposicao_incerteza.png', dpi=150, bbox_inches='tight')