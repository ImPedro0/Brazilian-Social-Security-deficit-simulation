import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


df_rgps = pd.read_excel('tabela_CCE002.xlsx', sheet_name='Projeções')

ano_calc_inicio = 2026
ano_calc_fim = 2060
ano_base = 2025   # ano de referência para contagem do horizonte de incerteza

df_base = df_rgps[(df_rgps['Exercício'] >= ano_base) & (df_rgps['Exercício'] <= ano_calc_fim)].copy()
df_base = df_base.set_index('Exercício')


sigma_frac_R   = 0.010   # 1,0% ao ano de incerteza na Receita
sigma_frac_D   = 0.008   # 0,8% ao ano de incerteza na Despesa (mais rígida/vegetativa)
sigma_frac_PIB = 0.0035  # 0,35% ao ano de incerteza no PIB (mais volátil)

# Matriz de correlação entre os choques (ordem: R, D, PIB)
#   R x PIB   = +0,6  -> Receita acompanha o ciclo do PIB (massa salarial)
#   D x PIB   = -0,3  -> Despesa relativamente mais pressionada quando o
#                        PIB é mais fraco (efeito anticíclico)
#   R x D     = -0,2  -> quando a Receita surpreende para cima, a Despesa
#                        tende a ficar relativamente mais controlada
corr = np.array([
    [ 1.0, -0.2,  0.6],   # R
    [-0.2,  1.0, -0.3],   # D
    [ 0.6, -0.3,  1.0],   # PIB
])
 
sigma = np.array([sigma_frac_R, sigma_frac_D, sigma_frac_PIB])
 
# Matriz de covariância para horizonte de 1 ano: Sigma = D * Corr * D
Sigma_base = np.outer(sigma, sigma) * corr
 
# Decomposição de Cholesky: Sigma_base = L @ L.T
# (permite gerar vetores normais correlacionados a partir de ruído branco:
#  se z ~ N(0, I), então L @ z ~ N(0, Sigma_base))
L_base = np.linalg.cholesky(Sigma_base)

num_simulacoes = 1000

resultados = []

rng = np.random.default_rng(42)
 
for simulacao in range(num_simulacoes):
    for ano in range(ano_calc_inicio, ano_calc_fim + 1):
 
        R_pldo   = df_base.loc[ano, 'Receita']
        D_pldo   = df_base.loc[ano, 'Despesa']
        PIB_pldo = df_base.loc[ano, 'PIB']
 
        horizonte = ano - ano_base   # anos à frente do ano-base (2025)
 
        # Ruído branco padrão (3 variáveis independentes, N(0,1))
        z = rng.standard_normal(3)
 
        # Correlaciona via Cholesky e escala pelo horizonte:
        # Sigma_t = horizonte * Sigma_base  =>  L_t = sqrt(horizonte) * L_base
        eps_R, eps_D, eps_PIB = np.sqrt(horizonte) * (L_base @ z)
 
        R_sim   = R_pldo   * (1 + eps_R)
        D_sim   = D_pldo   * (1 + eps_D)
        PIB_sim = PIB_pldo * (1 + eps_PIB)
 
        NFin_sim      = D_sim - R_sim
        NFin_pct_sim  = (NFin_sim / PIB_sim) * 100
 
        resultados.append({
            'Ano': ano,
            'Simulacao': simulacao,
            'Receita': R_sim,
            'Despesa': D_sim,
            'Deficit (NFin)': NFin_sim,
            'PIB': PIB_sim,
            'Deficit % PIB': NFin_pct_sim
        })
 
df_projecao = pd.DataFrame(resultados)
 
# Calcular média
df_media = (
    df_projecao
    .groupby('Ano')
    .mean(numeric_only=True)
    .reset_index()
)
 
# Recorte do período e cálculo do Intervalo de Confiança (5% e 95%)
df_p5  = df_projecao.groupby('Ano')[['Deficit (NFin)', 'Deficit % PIB']].quantile(0.05).reset_index()
df_p95 = df_projecao.groupby('Ano')[['Deficit (NFin)', 'Deficit % PIB']].quantile(0.95).reset_index()
 
df_media = df_media[(df_media['Ano'] >= ano_calc_inicio) & (df_media['Ano'] <= ano_calc_fim)]
df_p5    = df_p5[   (df_p5['Ano']    >= ano_calc_inicio) & (df_p5['Ano']    <= ano_calc_fim)]
df_p95   = df_p95[  (df_p95['Ano']   >= ano_calc_inicio) & (df_p95['Ano']   <= ano_calc_fim)]
 
# Cenário-base oficial (determinístico, sem ruído) para sobrepor nos gráficos
df_oficial = df_rgps[(df_rgps['Exercício'] >= ano_calc_inicio) & (df_rgps['Exercício'] <= ano_calc_fim)].copy()
df_oficial['Deficit % PIB'] = (df_oficial['Necessidade de Fin.'] / df_oficial['PIB']) * 100

# Gráficos

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Gráfico 1: Déficit Nominal
ax1 = axes[0]
deficit_p5   = df_p5['Deficit (NFin)']  / 1_000_000
deficit_p95  = df_p95['Deficit (NFin)'] / 1_000_000

ax1.fill_between(df_p5['Ano'], deficit_p5, deficit_p95,
                 alpha=0.2, color='red', label='Faixa de previsão de 90% (P5–P95)')
ax1.plot(df_oficial['Exercício'], df_oficial['Necessidade de Fin.'] / 1_000_000,
         color='black', linewidth=2, linestyle='--', label='Cenário-base (PLDO 2026)')
ax1.plot(
    df_media['Ano'],
    df_media['Deficit (NFin)'] / 1_000_000,
    linewidth=2,
    label='Média das simulações'
)
ax1.set_title(f'Necessidade de Financiamento do RGPS ({ano_calc_inicio}–{ano_calc_fim})')
ax1.set_xlabel('Ano')
ax1.set_ylabel('Déficit (R$ Trilhões)')
ax1.grid(True, linestyle='--', alpha=0.7)
ax1.legend()

# Gráfico 2: Déficit % do PIB
ax2 = axes[1]
ax2.fill_between(df_p5['Ano'], df_p5['Deficit % PIB'], df_p95['Deficit % PIB'],
                 alpha=0.2, color='darkorange', label='Faixa de previsão de 90% (P5–P95)')
ax2.plot(df_oficial['Exercício'], df_oficial['Deficit % PIB'],
         color='black', linewidth=2, linestyle='--', label='Cenário-base (PLDO 2026)')
ax2.plot(
    df_media['Ano'],
    df_media['Deficit % PIB'],
    linewidth=2,
    label='Média das simulações'
)
ax2.set_title(f'Necessidade de Financiamento do RGPS % do PIB ({ano_calc_inicio}–{ano_calc_fim})')
ax2.set_xlabel('Ano')
ax2.set_ylabel('% do PIB')
ax2.grid(True, linestyle='--', alpha=0.7)
ax2.legend()

plt.tight_layout()
plt.savefig('projecao_rgps.png', dpi=150, bbox_inches='tight')
plt.show()

# Resumo em texto
print("\nResumo da Projeção (médias)")
print(f"{'Ano':>4}  {'Receita (R$bi)':>15}  {'Despesa (R$bi)':>14}  {'Déficit (R$bi)':>14}  {'% PIB':>6}")
for _, row in df_media.iterrows():
    print(f"{int(row['Ano']):>4}  {row['Receita']/1000:>15,.1f}  "
          f"{row['Despesa']/1000:>14,.1f}  "
          f"{row['Deficit (NFin)']/1000:>14,.1f}  "
          f"{row['Deficit % PIB']:>6.2f}%")