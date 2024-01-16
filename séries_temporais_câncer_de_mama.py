# -*- coding: utf-8 -*-
"""Séries Temporais - Câncer de mama.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1rZl_ZoFkTN9W8yxXk4TqK2MJxPeXpTVw

# Aplicação de Séries Temporais

Discentes:
- Adriele Correia Ribeiro
- Gisele Cerqueira Conceição
- Victor Miranda Bulhosa

Docente:
- Renato Novais

Disciplina:
- PPGESP-ESPA04-6: Análise Visual de Dados

Título do Artigo:
- Uma Análise Visual do Cenário de Realização de Mamografias na Bahia

Índice:  
1.  Introdução  
2.  Análise Exploratória de dados - EDA  
  2.1 Pré-Processamento de Dados  
  2.2 Transformações de Atributos  
  2.3 Dados faltantes  
  2.4 Análise Univariada  
  2.5 Decomposição da Série Temporal  
  2.6 Teste Estacionário  
  2.7 Técnica para tornar a série temporal estacionária  
    2.7.1 Diferenciação da série  
    2.7.2 Transformação Boxcox  
  2.8 Autocorrelação  
3. Modelagem  
  3.1 Divisão em conjunto de treino e teste  
  3.2 Comparando modelos  
  3.3 Gerando previsões  
4. Resultados

## 1. Introdução

Este trabalho tem por objetivo realizar uma análise visual da detecção precoce do câncer de mama nos municípios Bahia, avaliando o histórico dos últimos anos (2017 a 2023) e apresentando uma estimativa do cenário futuro (2024 e 2025) por meio das referências do manual de parâmetros técnicos do INCA e pela aplicação aplicação da análise de séries
temporais

As bases de dados utilizadas foram adquiridas através do site do DataSUS e do IBGE, e contêm:
- Quantidade de exames realizados na Bahia por mês (janeiro/2017 a setembro/2023) por tipo de resultado;
- Quantidade de exames realizados por município baiano e por mês (janeiro/2017 a setembro/2023);
- Quantidade de exames diagnosticados como lesão de câncer por município baiano e por mês (março/2017 a setembro/2023);
- Cidades e Mesorregiões da Bahia.
"""

# !pip install pmdarima
!pip install odfpy

# Análise de dados e construção de gráficos
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from plotly.offline import plot

import datetime

# Decomposição de série temporal
import statsmodels.api as sm
from statsmodels.tsa.seasonal import seasonal_decompose

# Teste estacionário
from statsmodels.tsa.stattools import adfuller, kpss

# Plotar gráficos de autocorrelação
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

# Transformação BoxCox
from scipy import stats
from scipy.special import inv_boxcox

# Método de comparação entre os modelos - RMSE
from sklearn.metrics import mean_squared_error

# Bloquear warnings
import warnings
warnings.filterwarnings('ignore')

# Modelo PROPHET
from prophet import Prophet

# Dataset de Resultados de Exames de Mamografia:
df_resultados_exames = pd.read_csv('mamografia_residba16984970756.csv', sep = ';', decimal = ',', encoding = 'latin')
df_resultados_exames

# Dataset de Total de Exames por Cidade e Mês/Ano:
df_exames_cidades = pd.read_csv('mamografia_residba16987182839.csv', sep = ';', decimal = ',', encoding = 'latin')
df_exames_cidades

# Dataset de Quantidade de Lesões de Câncer por Cidade e Mês/Ano:
df_lesoes_cancer = pd.read_csv('mamografia_residba16988818099.csv', sep = ';', decimal = ',', encoding = 'latin')
df_lesoes_cancer

# Dataset Macrorregiões:
df_macrorregioes = pd.read_excel('regioes_geograficas_composicao_por_municipios_2017_20180911.ods', engine='odf')
df_macrorregioes

"""## 2. Análise Exploratória dos Dados - EDA

---

### 2.1 Pré-processamento de Dados
"""

mapa_mes_data = {
    'JANEIRO': 1,
    'FEVEREIRO': 2,
    'MARÇO': 3,
    'ABRIL': 4,
    'MAIO': 5,
    'JUNHO': 6,
    'JULHO': 7,
    'AGOSTO': 8,
    'SETEMBRO': 9,
    'OUTUBRO': 10,
    'NOVEMBRO': 11,
    'DEZEMBRO': 12
}

# Converter formato de data: JANEIRO/2023 -> 2023-01-01
def conversao_data(data):
  mes_antigo = data.split('/')[0]
  mes_atual = mapa_mes_data[mes_antigo]
  data = data.replace(mes_antigo, str(mes_atual))
  data = pd.to_datetime(data, dayfirst=True)
  return data

# Tratar dataset de Resultados de Exames de Mamografia:
df_resultados_exames = df_resultados_exames.iloc[0:-2,:]
df_resultados_exames.columns = ['mes_ano', 'normais', 'alterados', 'nao_visualizados', 'ignorados', 'total']
df_resultados_exames.mes_ano = df_resultados_exames.mes_ano.apply(conversao_data)
df_resultados_exames

# Tratar dataset de Total de Exames por Cidade e Mês/Ano:
df_exames_cidades = df_exames_cidades.iloc[0:-1, 0:-1]
df_exames_cidades = df_exames_cidades.melt(id_vars=["Munic.de residencia"], var_name = 'data', value_name="qtd_exames")
df_exames_cidades.columns = ['municipio', 'data', 'qtd_exames']
df_exames_cidades.data = df_exames_cidades.data.apply(conversao_data)
df_exames_cidades['cod_municipio'] = df_exames_cidades.municipio.apply(lambda x: int(x.split(" ")[0]))
df_exames_cidades['municipio'] = df_exames_cidades.municipio.apply(lambda x: x.split(" ", maxsplit=1)[1])
df_exames_cidades

# Tratar dataset de Quantidade de Lesões de Câncer por Cidade e Mês/Ano:
df_lesoes_cancer = df_lesoes_cancer.iloc[0:-1, 0:-2]
df_lesoes_cancer = df_lesoes_cancer.melt(id_vars=["Munic.de residencia"], var_name = 'data', value_name="qtd_lesoes")
df_lesoes_cancer.columns = ['municipio', 'data', 'qtd_lesoes']
df_lesoes_cancer.data = df_lesoes_cancer.data.apply(conversao_data)
df_lesoes_cancer['cod_municipio'] = df_lesoes_cancer.municipio.apply(lambda x: int(x.split(" ")[0]))
df_lesoes_cancer['municipio'] = df_lesoes_cancer.municipio.apply(lambda x: x.split(" ", maxsplit=1)[1])
df_lesoes_cancer

# Acrescentar valores de lesões de câncer no dataset de exames:
df_aux = pd.pivot_table(df_lesoes_cancer, index='data', values='qtd_lesoes', aggfunc='sum').reset_index()

df_resultados_exames = df_resultados_exames.merge(df_aux, left_on='mes_ano', right_on='data', how='left')
df_resultados_exames

# Acrescentar microrregioes e código da cidade no dataset de exames por cidade:
df_macrorregioes['cod_reduzido'] = df_macrorregioes.CD_GEOCODI//10
df_exames_cidades = df_exames_cidades.merge(df_macrorregioes[['cod_reduzido','CD_GEOCODI','cod_rgi','nome_rgint']],
                                            left_on='cod_municipio',
                                            right_on='cod_reduzido',
                                            how='left')
# df_exames_cidades.CD_GEOCODI = df_exames_cidades.nome_rgint
# df_exames_cidades = df_exames_cidades.iloc[:,0:-2]
df_exames_cidades = df_exames_cidades[['municipio','data','qtd_exames','CD_GEOCODI','cod_rgi','nome_rgint']]
df_exames_cidades['ano'] = df_exames_cidades.data.dt.year
df_exames_cidades

# Acrescentar microrregioes e código da cidade no dataset de lesoes por cidade:
df_macrorregioes['cod_reduzido'] = df_macrorregioes.CD_GEOCODI//10
df_lesoes_cancer = df_lesoes_cancer.merge(df_macrorregioes[['cod_reduzido','CD_GEOCODI','cod_rgi','nome_rgint']],
                                            left_on='cod_municipio',
                                            right_on='cod_reduzido',
                                            how='left')
# df_exames_cidades.CD_GEOCODI = df_exames_cidades.nome_rgint
# df_exames_cidades = df_exames_cidades.iloc[:,0:-2]
df_lesoes_cancer = df_lesoes_cancer[['municipio','data','qtd_lesoes','CD_GEOCODI','cod_rgi','nome_rgint']]
df_lesoes_cancer['ano'] = df_lesoes_cancer.data.dt.year
df_lesoes_cancer

# Exportar dados no formato aceito pelo VYR:
df_vyr = df_exames_cidades.copy()
df_vyr = df_vyr.merge(df_lesoes_cancer[['municipio','data','qtd_lesoes']], on=['municipio','data'], how='left')
df_vyr = df_vyr[['municipio','CD_GEOCODI','ano','qtd_exames','qtd_lesoes']]
df_vyr = df_vyr.groupby(['municipio','CD_GEOCODI','ano']).sum()
df_vyr = df_vyr.reset_index()
for ano in df_vyr.ano.unique():
  df_vyr[df_vyr.ano==ano].to_excel('df_vyy'+str(ano)+'.xlsx', index=False)

df_vyr

"""### 2.4 Análise Univariada"""

# Estatística descritiva:
df_resultados_exames.describe().T

# Preencher valores nulos com 0:
df_resultados_exames.qtd_lesoes.fillna(0, inplace=True)

# Criando backup dos dados para EDA:
df_EDA = df_resultados_exames.copy()

# Plotando dados importados:
fig = px.line(df_EDA,
              x='mes_ano',
              y=['normais', 'alterados', 'nao_visualizados', 'ignorados','total','qtd_lesoes'],
              title='Resultados de Exames')
fig.show()

# Estatística descritiva:
df_EDA.describe().T

# Descrição dos atributos numéricos:
atr_numericos = ['normais', 'alterados', 'nao_visualizados', 'ignorados', 'total', 'qtd_lesoes']

# Histograma e Boxplot:
fig = px.histogram(df_EDA, x=atr_numericos, title = 'Histograma e Boxplot por Atributo: ', height=400, marginal="box")
fig.show()

# Teste de normalidade - Shapiro:
# Hipótese nula (H0) = conjunto de dados seguem distribuição normal
print('')
print("Atributos que seguem distribuição normal: \n")
for x in atr_numericos:
    pvalor = stats.shapiro(df_EDA[x])[1]
    if (pvalor > 0.05):
        print(f'O atributo "{x}" segue distribuição normal, pois o p-valor é igual a {pvalor:.2e}')

print("\n===================================================================================================== \n")
print("Atributos que não seguem distribuição normal: \n")

for x in atr_numericos:
    pvalor = stats.shapiro(df_EDA[x])[1]
    if (pvalor <= 0.05):
        print(f'O atributo "{x}" pode não seguir distribuição normal, pois o p-valor é igual a {pvalor:.2e}')

"""### 2.5 Decomposição da Série Temporal"""

# Criando dataset para decomposição:
df_EDA_decomposicao = df_EDA.copy()
df_EDA_decomposicao = df_EDA_decomposicao[['mes_ano','normais', 'alterados', 'nao_visualizados', 'ignorados', 'total', 'qtd_lesoes']]
df_EDA_decomposicao.set_index('mes_ano', inplace = True)
df_EDA_decomposicao.head(2)

# Decomposição aditiva: melhor quando a amplitude da sazonalidade NÃO DEPENDE do valor da trend.
# A decomposição multiplicativa é melhor quando a amplitude da sazonalidade DEPENDE do valor da trend.
for coluna in df_EDA_decomposicao.columns:

  decomposicao_aditiva = seasonal_decompose(df_EDA_decomposicao[coluna], model = 'aditive')

  figures = [px.line(decomposicao_aditiva.observed,  y=coluna, title=coluna),
            px.line(decomposicao_aditiva.trend,  y='trend', title='Componente de Tendência'),
            px.line(decomposicao_aditiva.seasonal,  y='seasonal', title='Componente de Sazonalidade'),
            px.line(decomposicao_aditiva.resid,  y='resid', title='Componente de Ruído Aleatório')]

  fig = make_subplots(rows=len(figures), cols=1, subplot_titles=(coluna,
                                                                'Componente de Tendência',
                                                                'Componente de Sazonalidade',
                                                                'Componente de Ruído Aleatório'))

  for i, figure in enumerate(figures):
      for trace in range(len(figure["data"])):
          fig.append_trace(figure["data"][trace], row=i+1, col=1)

  fig.update_layout(height = 900, title_text="Decomposição Aditiva")
  fig.show()

# Estatística dos resíduos:
for coluna in df_EDA_decomposicao.columns:
  figures = [px.histogram(decomposicao_aditiva.resid, x="resid"),
            px.box(decomposicao_aditiva.resid, y="resid")]

  fig = make_subplots(cols=len(figures), rows=1, subplot_titles=('Histograma Componente Ruído Aleatório',
                                                                'Boxplot Componente Ruído Aleatório'))

  for i, figure in enumerate(figures):
      for trace in range(len(figure["data"])):
          fig.append_trace(figure["data"][trace], col=i+1, row=1)

  fig.update_layout(width = 1000, title_text="Distribuição Componente de Ruído Aleatório - " + coluna)
  fig.show()

# Teste de normalidade - Shapiro:
  pvalor = stats.shapiro(decomposicao_aditiva.resid)[1]
  if (pvalor > 0.05):
    print(f'O atributo "{coluna}" segue distribuição normal, pois o p-valor é igual a {pvalor:.2e}')
  else:
    print(f'O atributo "{coluna}" não segue distribuição normal, pois o p-valor é igual a {pvalor:.2e}')
  print("\n===================================================================================================== \n")

"""Para todos os grupos, percebe-se que a mediana dos resíduos é próxima de zero, e um histograma com comportamento próximo ao da distribuição normal, o que evidencia uma decomposição adequada da série temporal.

### 2.6 Teste Estacionário

Combinação dos testes ADF (Augmented Dickey & Fuller) e KPSS (Kwiatkowski Philips Schmidt & Shin):

ADF: teste estatístico onde a hipótese nula (H0) é que a série é não estacionária.  
KPSS: teste estatístico onde a hipótese nula (H0) é que a série é estacionária.  

O KPSS pode ser utilizado junto com o ADF para reduzir a sua incerteza:
- H0 ADF aceita | H0 KPSS aceita = decisão inconclusiva.
- H0 ADF aceita | H0 KPSS rejeitada = série não estacionária.
- H0 ADF rejeitada | H0 KPSS aceita = série estacionária.
- H0 ADF rejeitada | H0 KPSS rejeitada = decisão inconclusiva.
"""

# Função para combinar ADF e KPSS:
def teste_estacionario(dados):
    # Calculando ADF
    teste_adf = adfuller(dados, autolag='AIC')
    print(f'ADF Statistics: {teste_adf[0]}')
    if teste_adf[1] < 0.05:
        # Hipótese nula rejeitada -> Série Estacionária
        print(f'P-Value = {teste_adf[1]}.\nHipótese nula rejeitada -> Série pode ser Estacionária.\n')
    else:
        # Hipótese nula não pode ser rejeitada -> Série Não Estacionária.
        print(f'P-Value = {teste_adf[1]}.\nHipótese nula não pode ser rejeitada -> Série Não Estacionária.\n')

    # Calculando KPSS
    teste_kpss = kpss(dados, regression='c')
    print(f'KPSS Statistics: {teste_kpss[0]}')
    if teste_kpss[1] < 0.05:
        # Hipótese nula rejeitada -> Série Não Estacionária.
        print(f'P-Value = {teste_kpss[1]}.\nHipótese nula rejeitada -> Série pode ser Não Estacionária.\n')
    else:
        # Hipótese nula não pode ser rejeitada -> Série pode ser Estacionária.
        print(f'P-Value = {teste_kpss[1]}.\nHipótese nula não pode ser rejeitada ->  Série Estacionária.\n')

    # Combinando resultados dos testes:
    if (teste_adf[1] < 0.05 and teste_kpss[1] < 0.05) or (teste_adf[1] >= 0.05 and teste_kpss[1] >= 0.05):
        return("Decisão Inconclusiva")
    if teste_adf[1] < 0.05 and teste_kpss[1] > 0.05:
        return("Série Estacionária")
    if teste_adf[1] > 0.05 and teste_kpss[1] < 0.05:
        return("Série Não Estacionária")

# Aplicando função:
for coluna in df_EDA_decomposicao.columns:
  print(f'Atributo: {coluna}')
  print(teste_estacionario(df_EDA_decomposicao[coluna]))
  print("=======================================================")

"""### 2.7 Técnicas para tornar a série temporal estacionária

Serão aplicadas as seguintes técnicas para tornar a série estacionária:
- Diferenciação da série
- Transformação Boxcox

#### 2.7.1 Diferenciação da série
"""

# Diferenciando lag = 1 (consumo = consumo_(t) - consumo_(t-1))
df_EDA_decomposicao['diff_normais'] = df_EDA_decomposicao.normais.diff()
df_EDA_decomposicao['diff_alterados'] = df_EDA_decomposicao.alterados.diff()
df_EDA_decomposicao['diff_nao_visualizados'] = df_EDA_decomposicao.nao_visualizados.diff()
df_EDA_decomposicao['diff_ignorados'] = df_EDA_decomposicao.ignorados.diff()
df_EDA_decomposicao['diff_total'] = df_EDA_decomposicao.total.diff()
df_EDA_decomposicao['diff_qtd_lesoes'] = df_EDA_decomposicao.qtd_lesoes.diff()
df_EDA_decomposicao.head(4)

# Aplicando função:
for coluna in df_EDA_decomposicao.columns[-6:]:
  print(f'Atributo: {coluna}')
  print(teste_estacionario(df_EDA_decomposicao[coluna].iloc[1:]))
  print("=======================================================")

"""Com a primeira diferenciação, as séries se tornam estacionárias, conforme resultado dos testes acima.
Abaixo segue como ficaram as distribuições dos grupos com a diferenciação:
"""

df_EDA_decomposicao.columns[-6:]

# Gráfico da diferenciação com lag = 1 dos consumos:
fig = px.line(df_EDA_decomposicao.iloc[1:],
              y=['diff_normais', 'diff_alterados', 'diff_nao_visualizados','diff_ignorados', 'diff_total', 'diff_qtd_lesoes'],
              title='Diferenciação')
fig.show()

"""#### 2.7.2 Transformação Boxcox"""

vetor_lambda = []
# Transformação Boxcox:
for coluna in df_EDA_decomposicao.columns[0:6]:
  # Calculando lambda:
  df_box_cox, best_lambda = stats.boxcox(df_EDA_decomposicao[coluna]+1)
  vetor_lambda.append(best_lambda)
  print(f'Atributo: {coluna}\n')
  print(f'Valor de lambda: {best_lambda}')
  # Inserindo valores transformados no dataset:
  df_EDA_decomposicao['boxcox_'+coluna] = df_box_cox
  # Aplicando função:
  print(teste_estacionario(df_box_cox))
  print("=======================================================\n")

df_EDA_decomposicao.head(6)

"""Nesse caso, não houve uma melhoria associada ao uso da transformação boxcox, pois as séries permaneceram não estacionárias. Um refinamento do parâmetro lambda pode contornar essa situação.

Abaixo segue como ficou a distribuição dos dados:
"""

fig = px.line(df_EDA_decomposicao,
              y=['boxcox_normais','boxcox_alterados','boxcox_nao_visualizados','boxcox_ignorados','boxcox_total','boxcox_qtd_lesoes'],
              title='BoxCox')
fig.show()

"""### 2.8 Autocorrelação

Medida de correlação entre a variável e o valores passados da mesma variável (lag).  
A autocorrelação total leva em consideração a influência de todos os lags anteriores.  
A autocorrelação parcial desconsidera a influência dos lags anteriores.
"""

# Gráfico de autocorrelação total:
for coluna in df_EDA_decomposicao.columns[0:6]:
  fig, axes = plt.subplots(1,3, figsize=(20,5))
  plot_acf(df_EDA_decomposicao[coluna], ax=axes[0]);
  plot_acf(df_EDA_decomposicao['diff_'+coluna].iloc[1:], ax=axes[1]);
  plot_acf(df_EDA_decomposicao['boxcox_'+coluna], ax=axes[2]);
  axes[0].set_xlabel(coluna);
  axes[1].set_xlabel(coluna + " - Diferenciação");
  axes[2].set_xlabel(coluna + " - BoxCox");

# Gráfico de autocorrelação parcial:
for coluna in df_EDA_decomposicao.columns[0:6]:
  fig, axes = plt.subplots(1,3, figsize=(20,5))
  plot_pacf(df_EDA_decomposicao[coluna], ax=axes[0]);
  plot_pacf(df_EDA_decomposicao['diff_'+coluna].iloc[1:], ax=axes[1]);
  plot_pacf(df_EDA_decomposicao['boxcox_'+coluna], ax=axes[2]);
  axes[0].set_xlabel(coluna);
  axes[1].set_xlabel(coluna + " - Diferenciação");
  axes[2].set_xlabel(coluna + " - BoxCox");

"""## 3. Modelagem

O método de avaliação entre os modelos será a Raiz do Erro Médio Quadrático (RMSE em inglês), pois trabalha bem com grandes quantidades de dados, e penaliza mais os erros elevados.

### 3.1 Divisão em conjuntos de treino e teste
"""

# Separando em 80%|20%:
indice = int(len(df_EDA)*0.8)

df_EDA_treino = df_EDA.iloc[:indice, :]
df_EDA_treino = df_EDA_treino[['mes_ano','normais', 'alterados', 'nao_visualizados', 'ignorados', 'total', 'qtd_lesoes']]
df_EDA_teste = df_EDA.iloc[indice:, :]
df_EDA_teste = df_EDA_teste[['mes_ano','normais', 'alterados', 'nao_visualizados', 'ignorados', 'total', 'qtd_lesoes']]

print('Dataset treino:')
display(df_EDA_treino.head())
print('\n\n Dataset teste:')
display(df_EDA_teste.head())

# Vetor de pré-processamento:
preprocessamento = ['nenhum','diff','boxcox']

"""### 3.2 Comparando modelos"""

# Dataframe de resultados:
resultados = pd.DataFrame(columns = ['grupo', 'preprocessamento','rmse'])

for coluna in df_EDA_treino.columns[1:]:
  for prep in preprocessamento:
    # Treino:
    treino = df_EDA_treino[['mes_ano',coluna]].copy()
    treino.columns = ['ds','y']

    # Transformação:
    if prep == 'nenhum':
        pass
    elif prep == 'diff':
        primeiro_valor = treino.y[0]
        treino.y = treino.y.diff()
        treino = treino.iloc[1:,:]    # Removendo NaN
    elif prep == 'boxcox':
        treino_box, best_lambda = stats.boxcox(treino.y+1)
        treino.y = treino_box

    # Rodando modelo:
    m = Prophet()
    m.fit(treino)

    # Calculando índices de início e término da previsão:
    vetor_indice = []
    for indice in range(1,len(df_EDA_teste)+1):
      vetor_indice.append(treino.iloc[-1,0] + pd.DateOffset(months=indice))
    vetor_indice = pd.DataFrame(vetor_indice, columns = ["ds"])

    # Gerar previsão:
    predicao = m.predict(vetor_indice);

    # Transformação inversa:
    if prep == 'nenhum':
        pass
    elif prep == 'diff':
        inv_diff = predicao.yhat.cumsum()
        inv_diff = inv_diff.fillna(0) + primeiro_valor
        predicao.yhat = inv_diff
    elif prep == 'boxcox':
        predicao.yhat = inv_boxcox(predicao.yhat, best_lambda)-1

    # Calculando RMSE:
    rmse_prophet = mean_squared_error(df_EDA_teste[coluna], predicao.yhat, squared = True)


    # # Gráficos com as séries:
    # fig = px.scatter(y = [df_EDA_teste[coluna], predicao.yhat],
    #                   title = 'Predição (vermelho) x Teste (azul) - ' + coluna + '(' + prep + ') - RMSE: ' + str(round(rmse_prophet,2)),
    #                  height = 300)
    # fig.show()
    # fig1 = m.plot(predicao, figsize=(9, 4))
    # fig1.show()

    # Inserindo valores na tabela resultados:
    linha = [coluna, prep, rmse_prophet]
    resultados = pd.DataFrame(np.insert(resultados.values, 0, values=linha, axis=0))

resultados.columns = ['grupo', 'preprocessamento','rmse']
resultados.sort_values(by = ['grupo','rmse'], ascending=True, inplace = True)
print()
display(resultados)

"""### 3.3 Gerando previsões"""

# Dataset com previsões:
previsoes = pd.DataFrame()

# Calculando índices de início e término da previsão:
vetor_indice = []
for indice in range(1,12*2+4):
  vetor_indice.append(df_EDA.iloc[-1,0] + pd.DateOffset(months=indice))
vetor_indice = pd.DataFrame(vetor_indice, columns = ["ds"])

# normais:
coluna = 'normais'
treino = df_EDA[['mes_ano',coluna]].copy()
treino.columns = ['ds','y']

# Rodando modelo:
m = Prophet()
m.fit(treino)

# Gerar previsão:
predicao = m.predict(vetor_indice)

# Tabela com resultados:
display(predicao.tail())

# Gráficos com as séries:
fig = m.plot(predicao, figsize=(9, 4), ylabel=coluna)
fig.show()

fig1 = m.plot_components(predicao)
fig1.show()

# Montando dataset para visão total
previsoes['mes_ano'] = predicao.ds
previsoes[coluna] = predicao.yhat

# alterados:
coluna = 'alterados'
treino = df_EDA[['mes_ano',coluna]].copy()
treino.columns = ['ds','y']

# # Transformação Box-Cox:
# treino_box, best_lambda = stats.boxcox(treino.y+1)
# treino.y = treino_box
# primeiro_valor = treino.y[0]
# treino.y = treino.y.diff()
# treino = treino.iloc[1:,:]    # Removendo NaN


# Rodando modelo:
m = Prophet()
m.fit(treino)

# Gerar previsão:
predicao = m.predict(vetor_indice)

# # Transformação Inversa:
# predicao.yhat = inv_boxcox(predicao.yhat, best_lambda)-1
# inv_diff = predicao.yhat.cumsum()
# inv_diff = inv_diff.fillna(0) + primeiro_valor
# predicao.yhat = inv_diff

# Tabela com resultados:
display(predicao.tail())

# Gráficos com as séries:
fig = m.plot(predicao, figsize=(9, 4), ylabel=coluna)
fig.show()

fig1 = m.plot_components(predicao)
fig1.show()

# Montando dataset para visão total
previsoes['mes_ano'] = predicao.ds
previsoes[coluna] = predicao.yhat

# nao_visualizados:
coluna = 'nao_visualizados'
treino = df_EDA[['mes_ano',coluna]].copy()
treino.columns = ['ds','y']

# # Transformação Box-Cox:
# treino_box, best_lambda = stats.boxcox(treino.y+1)
# treino.y = treino_box
# primeiro_valor = treino.y[0]
# treino.y = treino.y.diff()
# treino = treino.iloc[1:,:]    # Removendo NaN


# Rodando modelo:
m = Prophet()
m.fit(treino)

# Gerar previsão:
predicao = m.predict(vetor_indice)

# # Transformação Inversa:
# predicao.yhat = inv_boxcox(predicao.yhat, best_lambda)-1
# inv_diff = predicao.yhat.cumsum()
# inv_diff = inv_diff.fillna(0) + primeiro_valor
# predicao.yhat = inv_diff

# Tabela com resultados:
display(predicao.tail())

# Gráficos com as séries:
fig = m.plot(predicao, figsize=(9, 4), ylabel=coluna)
fig.show()

fig1 = m.plot_components(predicao)
fig1.show()

# Montando dataset para visão total
previsoes['mes_ano'] = predicao.ds
previsoes[coluna] = predicao.yhat

# ignorados:
coluna = 'ignorados'
treino = df_EDA[['mes_ano',coluna]].copy()
treino.columns = ['ds','y']

# # Transformação Box-Cox:
# treino_box, best_lambda = stats.boxcox(treino.y+1)
# treino.y = treino_box
# primeiro_valor = treino.y[0]
# treino.y = treino.y.diff()
# treino = treino.iloc[1:,:]    # Removendo NaN


# Rodando modelo:
m = Prophet()
m.fit(treino)

# Gerar previsão:
predicao = m.predict(vetor_indice)

# # Transformação Inversa:
# predicao.yhat = inv_boxcox(predicao.yhat, best_lambda)-1
# inv_diff = predicao.yhat.cumsum()
# inv_diff = inv_diff.fillna(0) + primeiro_valor
# predicao.yhat = inv_diff

# Tabela com resultados:
display(predicao.tail())

# Gráficos com as séries:
fig = m.plot(predicao, figsize=(9, 4), ylabel=coluna)
fig.show()

fig1 = m.plot_components(predicao)
fig1.show()

# Montando dataset para visão total
previsoes['mes_ano'] = predicao.ds
previsoes[coluna] = predicao.yhat

# total:
coluna = 'total'
treino = df_EDA[['mes_ano',coluna]].copy()
treino.columns = ['ds','y']

# # Transformação Box-Cox:
# treino_box, best_lambda = stats.boxcox(treino.y+1)
# treino.y = treino_box
# primeiro_valor = treino.y[0]
# treino.y = treino.y.diff()
# treino = treino.iloc[1:,:]    # Removendo NaN


# Rodando modelo:
m = Prophet()
m.fit(treino)

# Gerar previsão:
predicao = m.predict(vetor_indice)

# # Transformação Inversa:
# predicao.yhat = inv_boxcox(predicao.yhat, best_lambda)-1
# inv_diff = predicao.yhat.cumsum()
# inv_diff = inv_diff.fillna(0) + primeiro_valor
# predicao.yhat = inv_diff

# Tabela com resultados:
display(predicao.tail())

# Gráficos com as séries:
fig = m.plot(predicao, figsize=(9, 4), ylabel=coluna)
fig.show()

fig1 = m.plot_components(predicao)
fig1.show()

# Montando dataset para visão total
previsoes['mes_ano'] = predicao.ds
previsoes[coluna] = predicao.yhat

# qtd_lesoes:
coluna = 'qtd_lesoes'
treino = df_EDA[['mes_ano',coluna]].copy()
treino.columns = ['ds','y']

# # Transformação Box-Cox:
# treino_box, best_lambda = stats.boxcox(treino.y+1)
# treino.y = treino_box
# primeiro_valor = treino.y[0]
# treino.y = treino.y.diff()
# treino = treino.iloc[1:,:]    # Removendo NaN


# Rodando modelo:
m = Prophet()
m.fit(treino)

# Gerar previsão:
predicao = m.predict(vetor_indice)

# # Transformação Inversa:
# predicao.yhat = inv_boxcox(predicao.yhat, best_lambda)-1
# inv_diff = predicao.yhat.cumsum()
# inv_diff = inv_diff.fillna(0) + primeiro_valor
# predicao.yhat = inv_diff

# Tabela com resultados:
display(predicao.tail())

# Gráficos com as séries:
fig = m.plot(predicao, figsize=(9, 4), ylabel=coluna)
fig.show()

fig1 = m.plot_components(predicao)
fig1.show()

# Montando dataset para visão total
previsoes['mes_ano'] = predicao.ds
previsoes[coluna] = predicao.yhat

# Comparando previsão do consumo total com soma das previsões dos consumos:
previsoes['soma_previsoes'] = previsoes.normais + \
                                          previsoes.alterados + \
                                          previsoes.nao_visualizados + \
                                          previsoes.ignorados

# Gerando gráfico:
px.line(previsoes,
        y=['total','soma_previsoes'],
        x='mes_ano',
        title = 'Comparação entre Previsão do Total de Exames e Soma das Previsões dos Exames por resultados')

# Gerando totais de consumo por ano:
previsoes['ano'] = previsoes.mes_ano.dt.year
df_resumo = pd.pivot_table(previsoes, index = 'ano', aggfunc='sum')
df_resumo

"""## 4. Proporcionalização

### 4.1 Região
"""

# Quantidade de exames:
df_exames_cidades.head(2)

# Quantidade de exames por data e macrorregião:
df_aux = pd.pivot_table(df_exames_cidades,index='data',columns='nome_rgint',values='qtd_exames', aggfunc='sum').reset_index()
df_aux

# Medianas das quantidades de exames:
medianas = []
for col in df_aux.columns[1:]:
  print(f'{col} - {df_aux[col].median()}')
  medianas.append(df_aux[col].median())

# Medianas e porcentagens das quantidades de exames:
df_aux2 = pd.DataFrame()
df_aux2['regioes'] = df_aux.columns[1:]
df_aux2['medianas'] = medianas
df_aux2['porcentagem'] = df_aux2['medianas'] / df_aux2['medianas'].sum()
df_aux2

# Quantidade prevista de exames por região:
df_resumo_exames = df_resumo[['total']].copy()
for regiao in df_aux2.regioes:
  df_resumo_exames[regiao] = (df_resumo_exames.total * df_aux2.loc[df_aux2.regioes == regiao, 'porcentagem'].iloc[0]).astype('int')
df_resumo_exames

# Quantidade de lesões previstas por região:
df_resumo_lesoes = df_resumo[['qtd_lesoes']].copy()
for regiao in df_aux2.regioes:
  df_resumo_lesoes[regiao] = (df_resumo_lesoes.qtd_lesoes * df_aux2.loc[df_aux2.regioes == regiao, 'porcentagem'].iloc[0]).astype('int')
df_resumo_lesoes

"""### Cidade"""

df_aux = pd.pivot_table(df_exames_cidades,index='data',columns='CD_GEOCODI',values='qtd_exames', aggfunc='sum').reset_index()
df_aux

medianas = []
for col in df_aux.columns[1:]:
  print(f'{col} - {df_aux[col].median()}')
  medianas.append(df_aux[col].median())

df_aux2 = pd.DataFrame()
df_aux2['cidades'] = df_aux.columns[1:]
df_aux2['medianas'] = medianas
df_aux2['porcentagem'] = df_aux2['medianas'] / df_aux2['medianas'].sum()
df_aux2

# Quantidade de exames previstos por cidade:
df_resumo_exames = df_resumo[['total']].copy()
for cidade in df_aux2.cidades:
  df_resumo_exames[cidade] = (df_resumo_exames.total * df_aux2.loc[df_aux2.cidades == cidade, 'porcentagem'].iloc[0]).astype('int')
df_resumo_exames

# Quantidade de lesões previstas por cidade:
df_resumo_lesoes = df_resumo[['qtd_lesoes']].copy()
for cidade in df_aux2.cidades:
  df_resumo_lesoes[cidade] = (df_resumo_lesoes.qtd_lesoes * df_aux2.loc[df_aux2.cidades == cidade, 'porcentagem'].iloc[0]).astype('int')
df_resumo_lesoes

df_previsoes_vyr = df_resumo_lesoes.iloc[:,1:].T
df_previsoes_vyr = df_previsoes_vyr.reset_index()
df_previsoes_vyr.columns = ['COD IBGE', 'Lesoes 2023', 'Lesoes 2024', 'Lesoes 2025']
df_previsoes_vyr.to_excel('VYR_Lesoes.xlsx', index = False)
df_previsoes_vyr

df_previsoes_vyr = df_resumo_exames.iloc[:,1:].T
df_previsoes_vyr = df_previsoes_vyr.reset_index()
df_previsoes_vyr.columns = ['COD IBGE', 'Exames 2023', 'Exames 2024', 'Exames 2025']
df_previsoes_vyr.to_excel('VYR_Exames.xlsx', index = False)
df_previsoes_vyr