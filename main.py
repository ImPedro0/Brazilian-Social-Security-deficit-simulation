import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from leitura_dados import df_inss, df_rgps, df_ibge

# Valores fixos
ano_calc_inicio = 2026
ano_calc_fim = 2060

# Intervalo a ser analisado
ano_inicio = 2026
ano_fim = 2060

# Dados INSS

for col in df_inss.columns[1:]:
    if df_inss[col].dtype == 'object':
        df_inss[col] = (df_inss[col].astype(str)
                                    .str.replace('%', '', regex=False)
                                    .astype(float) / 100)

# Dados RGPS

def limpar_numeros_br(valor):
    if isinstance(valor, str):
        valor = valor.replace('.', '').replace(',', '.')
        if '%' in valor: 
            return float(valor.replace('%', '')) / 100
        return float(valor)
    return valor

for col in df_rgps.columns[1:]:
    df_rgps[col] = df_rgps[col].apply(limpar_numeros_br)

# Dados IBGE

linha_pop = df_ibge[df_ibge['Indicador'] == 'População projetada']
colunas_anos = [col for col in df_ibge.columns if isinstance(col, int)]
 
if not linha_pop.empty:
    pop_total_serie = linha_pop.iloc[0][colunas_anos]
    pop_total_serie.index = pop_total_serie.index.astype(int)
else:
    pop_total_serie = pd.Series(dtype=float)

rgps_2025 = df_rgps[df_rgps.iloc[:, 0] == 2025].iloc[0]

# Em milhões

R_inicial   = rgps_2025['Receita']             
D_inicial   = rgps_2025['Despesa']            
PIB_inicial = rgps_2025['PIB']

resultados = []

a_inicial = 0.65
limite_max = 0.75

# Simulação

num_simulacoes = 1000

for simulacao in range(num_simulacoes):

    R_t_menos_1   = R_inicial
    D_t_menos_1   = D_inicial
    PIB_t_menos_1 = PIB_inicial
    a_t           = a_inicial

    # Cálculo

    for ano in range(ano_calc_inicio, ano_calc_fim + 1):

        taxas_t_df = df_inss[df_inss['Exercicio'] == ano]

        if taxas_t_df.empty:
            continue

        taxas_t = taxas_t_df.iloc[0]

        # Variáveis  
        
        Cms_base  = taxas_t['Taxa de Crescimento da Massa Salarial dos Contribuintes']
        I_base    = taxas_t['Taxa de Inflacao Anual (INPC Acumulado)']
        Cpib_base = taxas_t['Taxa de Crescimento Real do PIB']
        rmin_base = taxas_t['Taxa de Reajuste do Salario-Minimo']
        rb_base   = taxas_t['Taxa de Reajuste dos Demais Beneficios']
        Cd_base = taxas_t['Taxa de Crescimento Real (Vegetativa) da Despesa']

        # Monte Carlo

        Cms_t = np.random.normal(Cms_base, 0.01)
        I_t = np.random.normal(I_base, 0.01)
        Cpib_t = np.random.normal(Cpib_base, 0.015)
        Cd_t = np.random.normal(Cd_base, 0.01)
        
        # Equações

        fator_envelhecimento = Cd_t * 0.05
        a_t = min(a_t * (1 + fator_envelhecimento), limite_max)

        R_t   = R_t_menos_1   * (1 + Cms_t + I_t)
        D_t   = D_t_menos_1   * (1 + Cd_t + (a_t * rmin_base) + ((1 - a_t) * rb_base) + I_t)
        PIB_t = PIB_t_menos_1 * (1 + Cpib_t + I_t)
 
        NFin_t        = D_t - R_t
        NFin_pct_pib  = NFin_t / PIB_t
        
        resultados.append({
            'Ano': ano,
            'Simulacao': simulacao,
            'Receita': R_t,
            'Despesa': D_t,
            'Deficit (NFin)': NFin_t,
            'PIB': PIB_t,
            'Deficit % PIB': NFin_pct_pib * 100,
            'Proporção Sal. Mínimo (a)': a_t * 100
        })
        
        R_t_menos_1 = R_t
        D_t_menos_1 = D_t
        PIB_t_menos_1 = PIB_t

df_projecao = pd.DataFrame(resultados)

# Calcular média
df_media = (
    df_projecao
    .groupby('Ano')
    .mean(numeric_only=True)
    .reset_index()
)

# Recorte do período
df_p5  = df_projecao.groupby('Ano')[['Deficit (NFin)', 'Deficit % PIB']].quantile(0.05).reset_index()
df_p95 = df_projecao.groupby('Ano')[['Deficit (NFin)', 'Deficit % PIB']].quantile(0.95).reset_index()
 
df_media = df_media[(df_media['Ano'] >= ano_inicio) & (df_media['Ano'] <= ano_fim)]
df_p5    = df_p5[   (df_p5['Ano']   >= ano_inicio) & (df_p5['Ano']   <= ano_fim)]
df_p95   = df_p95[  (df_p95['Ano']  >= ano_inicio) & (df_p95['Ano']  <= ano_fim)]

# Gráfico 1

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

ax1 = axes[0]
deficit_bi   = df_media['Deficit (NFin)'] / 1_000_000
deficit_p5   = df_p5['Deficit (NFin)']    / 1_000_000
deficit_p95  = df_p95['Deficit (NFin)']   / 1_000_000

ax1.fill_between(df_p5['Ano'], deficit_p5, deficit_p95,
                 alpha=0.2, color='red', label='IC 90%')
ax1.plot(df_media['Ano'], deficit_bi, marker='o', color='red',
         linewidth=2, markersize=4, label='Média')
ax1.set_title(f'Projeção do Déficit do INSS ({ano_inicio}–{ano_fim})')
ax1.set_xlabel('Ano')
ax1.set_ylabel('Déficit (R$ Trilhões)')
ax1.grid(True, linestyle='--', alpha=0.7)
ax1.legend()

# Gráfico 2

ax2 = axes[1]
ax2.fill_between(df_p5['Ano'], df_p5['Deficit % PIB'], df_p95['Deficit % PIB'],
                 alpha=0.2, color='darkorange', label='IC 90%')
ax2.plot(df_media['Ano'], df_media['Deficit % PIB'], marker='s',
         color='darkorange', linewidth=2, markersize=4, label='Média')
ax2.set_title(f'Déficit do INSS em % do PIB ({ano_inicio}–{ano_fim})')
ax2.set_xlabel('Ano')
ax2.set_ylabel('% do PIB')
ax2.grid(True, linestyle='--', alpha=0.7)
ax2.legend()
 
plt.tight_layout()
plt.savefig('projecao_inss.png', dpi=150, bbox_inches='tight')
plt.show()

print("\nResumo da Projeção (médias)")
print(f"{'Ano':>4}  {'Receita (R$bi)':>15}  {'Despesa (R$bi)':>14}  "
      f"{'Déficit (R$bi)':>14}  {'% PIB':>6}")
for _, row in df_media.iterrows():
    print(f"{int(row['Ano']):>4}  {row['Receita']/1000:>15,.1f}  "
          f"{row['Despesa']/1000:>14,.1f}  "
          f"{row['Deficit (NFin)']/1000:>14,.1f}  "
          f"{row['Deficit % PIB']:>6.2f}%")