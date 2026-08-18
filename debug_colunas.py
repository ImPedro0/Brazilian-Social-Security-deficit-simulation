import pandas as pd

print("=== Colunas do df_inss ===")
df_inss = pd.read_excel('tabela1_CCE002.xlsx')
print(df_inss.columns.tolist())
print("\nPrimeiras linhas:")
print(df_inss.head())

print("\n=== Colunas do df_rgps ===")
df_rgps = pd.read_excel('tabela2_CCE002.xlsx')
print(df_rgps.columns.tolist())
print("\nPrimeiras linhas:")
print(df_rgps.head())

print("\n=== Colunas do df_ibge ===")
df_ibge = pd.read_excel('Projecao populacional IBGE.xlsx')
print(df_ibge.columns.tolist())
print("\nPrimeiras linhas:")
print(df_ibge.head())
