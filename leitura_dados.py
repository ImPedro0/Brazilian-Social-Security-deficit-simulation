import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df_inss = pd.read_excel('tabela1_CCE002.xlsx')

colunas_pct_inss = df_inss.columns[1:]

for col in colunas_pct_inss:
    if df_inss[col].dtype == 'object':
        df_inss[col] = df_inss[col].astype(str).str.replace('%', '').astype(float) / 100

df_rgps = pd.read_excel('tabela2_CCE002.xlsx')

def limpar_numeros_br(valor):
    if isinstance(valor, str):
        valor = valor.replace('.', '')
        valor = valor.replace(',', '.')
        if '%' in valor:
            return float(valor.replace('%', '')) / 100
        return float(valor)
    return valor

for col in df_rgps.columns[1:]:
    df_rgps[col] = df_rgps[col].apply(limpar_numeros_br)

df_ibge = pd.read_excel('Projecao populacional IBGE.xlsx')

df_ibge.dropna(how='all', inplace=True)
