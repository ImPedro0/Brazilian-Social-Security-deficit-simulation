# Simulação Estocástica da Necessidade de Financiamento do RGPS

Este repositório contém a implementação computacional utilizada para a projeção da **Necessidade de Financiamento do Regime Geral de Previdência Social (RGPS)** entre 2026 e 2060, utilizando simulações de Monte Carlo em Python.

## Requisitos

* Python 3.10 ou superior
* pip
* Git

As principais bibliotecas utilizadas são:

* `pandas`
* `numpy`
* `matplotlib`
* `openpyxl`

## Instalação

Clone o repositório:

```bash
git clone URL_DO_REPOSITORIO
```

Entre na pasta do projeto:

```bash
cd NOME_DO_REPOSITORIO
```

Recomenda-se criar um ambiente virtual:

```bash
python -m venv .venv
```

### Windows

Ative o ambiente virtual:

```bash
.venv\Scripts\activate
```

### Linux/macOS

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install pandas numpy matplotlib openpyxl
```

## Estrutura do projeto

A estrutura esperada do repositório é:

```text
.
├── tabela_CCE002.xlsx
├── leitura_dados.py
├── simulacao.py
├── decomposicao_incerteza.py
└── README.md
```

Os nomes dos arquivos `.py` devem ser substituídos pelos nomes presentes no repositório.

## Execução

Após instalar as dependências e ativar o ambiente virtual, execute os programas a partir da pasta principal do projeto.

Para executar a simulação principal:

```bash
python simulacao.py
```

Para executar a decomposição da incerteza:

```bash
python decomposicao_incerteza.py
```

> Substitua os nomes acima pelos nomes reais dos arquivos presentes no repositório.

## Arquivo de dados

O arquivo:

```text
tabela_CCE002.xlsx
```

deve estar na mesma pasta dos códigos que fazem sua leitura.

A planilha utilizada pelo código deve conter a aba:

```text
Projeções
```

com os dados necessários para a execução da simulação.

## Resultados

Após a execução dos códigos, os arquivos de saída são gerados automaticamente na pasta do projeto.

A simulação principal gera:

```text
projecao_rgps.png
```

A análise de decomposição da incerteza gera:

```text
decomposicao_incerteza.png
```

Além dos gráficos, a execução dos programas apresenta no terminal os principais resultados das simulações.

## Reprodutibilidade

As simulações utilizam sementes (`seed`) para a geração dos números aleatórios. Dessa forma, mantendo os mesmos dados, parâmetros e código, os resultados podem ser reproduzidos.

## Observação

Para executar os códigos corretamente, mantenha a estrutura de arquivos e os nomes das planilhas conforme apresentados neste README.
