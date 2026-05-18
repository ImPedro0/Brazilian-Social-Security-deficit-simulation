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
        df_inss[col] = df_inss[col].astype(str).str.replace('%', '').astype(float) / 100

# Dados RGPS

def limpar_numeros_br(valor):
    if isinstance(valor, str):
        valor = valor.replace('.', '').replace(',', '.')
        if '%' in valor: return float(valor.replace('%', '')) / 100
        return float(valor)
    return valor

for col in df_rgps.columns[1:]:
    df_rgps[col] = df_rgps[col].apply(limpar_numeros_br)

# Dados IBGE

def eh_idade_idosa(texto):
    texto = str(texto).lower()
    if 'anos' in texto or '+' in texto:
        numeros = [int(s) for s in texto.split() if s.isdigit()]
        if numeros and numeros[0] >= 65:
            return True
        if '90+' in texto or '80+' in texto:
            return True
    return False

df_idosos = df_ibge[df_ibge.iloc[:, 1].apply(eh_idade_idosa)]

colunas_anos = [col for col in df_idosos.columns if str(col).isdigit()]

pop_idosa_serie = df_idosos[colunas_anos].sum()
pop_idosa_serie.index = pop_idosa_serie.index.astype(int)

rgps_2025 = df_rgps[df_rgps.iloc[:, 0] == 2025].iloc[0]

R_t_menos_1 = rgps_2025['Receita']
D_t_menos_1 = rgps_2025['Despesa']
PIB_t_menos_1 = rgps_2025['PIB']

resultados = []

a_t = 0.65
limite_max = 0.75

# Simulação

num_simulacoes = 1000

for simulacao in range(num_simulacoes):

    R_inicial = rgps_2025['Receita']
    D_inicial = rgps_2025['Despesa']
    PIB_inicial = rgps_2025['PIB']

    a_inicial = 0.65

    # Reseta variáveis

    R_t_menos_1 = R_inicial
    D_t_menos_1 = D_inicial
    PIB_t_menos_1 = PIB_inicial
    a_t = a_inicial

    # Cálculo

    for ano in range(ano_calc_inicio, ano_calc_fim + 1):

        taxas_t_df = df_inss[df_inss.iloc[:, 0] == ano]

        # Variáveis

        if taxas_t_df.empty:
            continue

        taxas_t = taxas_t_df.iloc[0]    
        
        Cms_base  = taxas_t['Taxa de Crescimento da Massa Salarial dos Contribuintes']
        I_base    = taxas_t['Taxa de Inflacao Anual (INPC Acumulado)']
        Cpib_base = taxas_t['Taxa de Crescimento Real do PIB']
        rmin_base = taxas_t['Taxa de Reajuste do Salario-Minimo']
        rb_base   = taxas_t['Taxa de Reajuste dos Demais Beneficios']
        
        Cd_base = taxas_t['Taxa de Crescimento Real (Vegetativa) da Despesa']

        rmin_t = rmin_base
        rb_t = rb_base

        # Monte Carlo

        Cms_t = np.random.normal(Cms_base, 0.01)

        I_t = np.random.normal(I_base, 0.01)

        Cpib_t = np.random.normal(Cpib_base, 0.015)

        Cd_t = np.random.normal(Cd_base, 0.01)
        
        # Equações

        fator_envelhecimento = Cd_t * 0.05 
        a_t = a_t * (1 + fator_envelhecimento)
        
        a_t = min(a_t, limite_max)

        R_t = R_t_menos_1 * (1 + Cms_t + I_t)
        
        D_t = D_t_menos_1 * (1 + Cd_t + (a_t * rmin_t) + ((1 - a_t) * rb_t) + I_t)
        
        NFin_t = D_t - R_t
        PIB_t = PIB_t_menos_1 * (1 + Cpib_t + I_t)
        NFin_pct_pib = NFin_t / PIB_t
        
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

df_projecao_completa = pd.DataFrame(resultados)

# Calcular média
df_media = (
    df_projecao_completa
    .groupby('Ano')
    .mean(numeric_only=True)
    .reset_index()
)

# Recorte do período
df_media = df_media[
    (df_media['Ano'] >= ano_inicio) &
    (df_media['Ano'] <= ano_fim)
]

# Gráficos

plt.figure(figsize=(14, 6))

# Evolução do Déficit Nominal

plt.subplot(1, 2, 1)
plt.plot(df_media['Ano'], df_media['Deficit (NFin)'] / 1e12, marker='o', color='red', linewidth=2)
plt.title(f'Projeção do Déficit do INSS ({ano_inicio} - {ano_fim})')
plt.xlabel('Ano')
plt.ylabel('Déficit (em R$ Trilhões)')
plt.grid(True, linestyle='--', alpha=0.7)
plt.ticklabel_format(style='plain', axis='y')

# Déficit como % do PIB

plt.subplot(1, 2, 2)
plt.plot(df_media['Ano'], df_media['Deficit % PIB'], marker='s', color='darkorange', linewidth=2)
plt.title(f'Déficit do INSS em % do PIB ({ano_inicio} - {ano_fim})')
plt.xlabel('Ano')
plt.ylabel('% do PIB')
plt.grid(True, linestyle='--', alpha=0.7)

plt.tight_layout()
plt.show()