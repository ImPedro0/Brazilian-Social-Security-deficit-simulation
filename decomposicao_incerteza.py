import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# DECOMPOSIÇÃO DA INCERTEZA (One-At-a-Time / OAT)
#
# Objetivo: identificar quanto da largura do IC 90% da "Necessidade de
# Financiamento % PIB" em 2060 vem de cada fonte de choque (R, D, PIB),
# isoladamente.
#
# Método: roda o MESMO Monte Carlo do modelo principal, mas em 4 variantes:
#   1) Só eps_R  ativo (eps_D = eps_PIB = 0)
#   2) Só eps_D  ativo (eps_R = eps_PIB = 0)
#   3) Só eps_PIB ativo (eps_R = eps_D = 0)
#   4) TODOS ativos e correlacionados (Cholesky) -> cenário completo (baseline)
#
# Comparando a largura do IC 90% de cada variante isolada com a do cenário
# completo, mede-se a contribuição relativa de cada fonte para a incerteza
# total. É uma análise de sensibilidade "um fator de cada vez", mais simples
# que uma decomposição de variância de Sobol, mas suficiente para apontar
# qual variável domina o risco no TCC.
# ---------------------------------------------------------------------------

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

# 4 cenários: cada fonte isolada + o cenário completo (correlacionado) como referência
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

print(f"Ano de referência: {ano_alvo}\n")
print(f"{'Fonte':<20}{'Largura da faixa P5–P95 (pontos percentuais do PIB) em 2060':<22}{'Largura':<12}{'% da largura total (soma OAT)'}")
soma_larguras = larg_R + larg_D + larg_PIB
for nome, larg, p5, p95 in [
    ('Receita (R)',  larg_R,   p5_R,   p95_R),
    ('Despesa (D)',  larg_D,   p5_D,   p95_D),
    ('PIB',          larg_PIB, p5_PIB, p95_PIB),
]:
    pct = larg / soma_larguras * 100
    print(f"{nome:<20}[{p5:.2f}, {p95:.2f}]{'':<8}{larg:<12.3f}{pct:.1f}%")
print(f"\n{'Cenário completo':<20}[{p5_TOT:.2f}, {p95_TOT:.2f}]{'':<8}{larg_TOT:<12.3f}(correlacionado, não é soma direta)")

# Gráfico de barras (tipo "tornado" simplificado)
fig, ax = plt.subplots(figsize=(8,5))
fontes = ['PIB', 'Despesa (D)', 'Receita (R)']
larguras = [larg_PIB, larg_D, larg_R]
cores = ['darkorange', 'firebrick', 'steelblue']
ax.barh(fontes, larguras, color=cores)
for i, v in enumerate(larguras):
    ax.text(v + 0.02, i, f'{v:.2f} p.p.', va='center')
ax.set_xlabel('Largura da faixa P5–P95 (pontos percentuais do PIB) em 2060')
ax.set_title('Decomposição da incerteza por fonte de choque (one-at-a-time)')
ax.grid(True, axis='x', linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig('decomposicao_incerteza.png', dpi=150, bbox_inches='tight')