# Analisador Automatizado de Testes A/B — Méliuz

Solução reutilizável que recebe os dados de um teste A/B de cashback e
retorna uma análise estatística completa e uma recomendação de negócio
acionável: **qual variante escalar para 100% do tráfego**.

Link para acessar os relatórios e planilha com os resultados dos testes: [relatorios.md](relatorios.md) · [Planilha de acompanhamento](https://docs.google.com/spreadsheets/d/11rUTDzbcHEF8QNlcwO-CyvkuN9OfuupikytPEfyMVzk/edit?usp=sharing)

---

## 1. Como usar a solução

### 1.1 Pré-requisitos

- Python 3.10 ou superior
- Git
- Uma ferramenta de IA agêntica com execução de código (recomendado: Claude Code, Cursor, Antigravity ou Gemini CLI) — opcional, mas é o modo de uso pretendido desta solução

### 1.2 Baixe o projeto

Você pode clonar o repositório com Git:

```bash
git clone https://github.com/Julia-cel/Analise-Automatizada-de-Testes-A-B.git
cd Analise-Automatizada-de-Testes-A-B
```

Ou simplesmente clique em **Code → Download ZIP** na página do GitHub e extraia a pasta em seu computador.

---

## 1.3 Abra o projeto na ferramenta de IA

Abra a pasta do projeto em uma ferramenta de IA com execução de código, como:

- Cursor
- Claude Code
- Antigravity
- Gemini CLI

Essas ferramentas leem automaticamente o arquivo **AGENTES.md**, que contém as instruções para executar a solução.

---

### 1.4 Instale as dependências

Abra o terminal integrado da própria ferramenta de IA e execute:

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
source venv/bin/activate
```

Depois instale as bibliotecas do projeto:

```bash
pip install -r requirements.txt
```

> Essa etapa é necessária apenas na primeira utilização.

---


### 1.5 Configuração do Google Sheets 

**Importante:** por segurança, a credencial da conta de serviço do Google
**não está incluída neste repositório**. Comitar uma chave de API real em um
repositório público expõe essa credencial a qualquer pessoa — o Google
inclusive escaneia repositórios públicos e restringe automaticamente chaves
expostas dessa forma. Por isso, cada pessoa que quiser usar a integração com
o Google Sheets precisa gerar a própria credencial, seguindo estes passos:

1. Acesse o [Google Cloud Console](https://console.cloud.google.com) e crie um projeto (ou use um existente)
2. No menu **APIs e Serviços → Biblioteca**, ative a **Google Sheets API** e a **Google Drive API**
3. Vá em **APIs e Serviços → Credenciais → Criar credenciais → Conta de serviço**
4. Após criar a conta de serviço, abra ela → aba **Chaves** → **Adicionar chave → Criar nova chave → JSON**
5. Salve o arquivo baixado dentro da pasta `credentials/` deste projeto
6. Abra `scripts/resumo_sheets.py` e ajuste a constante `CAMINHO_CREDENCIAIS` para o nome exato do seu arquivo `.json`
7. Crie uma planilha no Google Sheets com as colunas: `Data | Nome do Teste | Descrição | Resultado | Decisão Tomada`
8. Compartilhe essa planilha com o e-mail da conta de serviço (encontrado dentro do `.json`, campo `client_email`), com permissão de **Editor**
9. No `scripts/main.py`, ajuste o nome da planilha na chamada `escrever_resultado_sheets(nome_planilha=...)` para o nome exato da sua planilha

**Sem esse passo, a solução continua funcionando normalmente** — a etapa de
escrita no Sheets falha de forma controlada (aviso no terminal), sem
interromper a geração do relatório. Os resultados do teste já inseridos automaticamente na planilha estão disponíveis em [RESULTADOS.md](RESULTADOS.md).

---

### 1.6 Execute uma análise

Depois que o ambiente estiver preparado, basta enviar um dataset CSV para a IA e fazer um pedido em linguagem natural, por exemplo:

```text
Analise este teste A/B.
```

ou

```text
Analise este dataset e me diga qual variante deve ser escalada.
```
O relatório só é aberto automaticamente no navegador quando explicitamente solicitado ("mostra", "abre", "quero ver").

---

### 1.7 Resultado esperado

A solução executa automaticamente todo o pipeline de análise:

- Limpeza e validação dos dados.
- Cálculo das métricas do teste.
- Testes estatísticos.
- Aplicação das regras de decisão de negócio.
- Geração da recomendação.
- Criação de um relatório HTML para gestores.
- Registro do resumo no Google Sheets (quando configurado).

Ao final da execução, a IA responde no chat com a recomendação e disponibiliza o relatório completo,caso solicitado, gerado pela solução.

---

### Execução manual (opcional)

```bash
python scripts/main.py datasets/dataset_01_parceiroA.csv
python scripts/main.py datasets/dataset_01_parceiroA.csv --abrir   # também abre o relatório no navegador
```

A solução funciona com qualquer um dos datasets fornecidos no case ou com novos datasets que sigam o mesmo formato, identificando automaticamente o parceiro, o período analisado e as variantes presentes no teste.

---

## 2. Arquitetura

### 2.1 Sobre o uso de IA neste projeto

Ferramentas de IA generativa foram utilizadas na escrita de código ao longo do desenvolvimento. A **arquitetura da solução** — analisar o problema que a automação deveria resolver, o contexto da empresa, alinhar a solução com os objetivos de negócio, conduzir diversos testes para corrigir e identificar erros e decidir como a IA iria atuar nessa solução de forma ética e funcinal — foi definida e validada por mim. 

### 2.2 Por que essa arquitetura

Os princípios centrais do projeto foram:
A implementação da solução deve ser simples o suficiente para que todos possam usar, mas ela também precisar gerar outputs exatos e confiáveis, por se tratar de métricas que vão influenciar a tomada de decisões na empresa. Para atender a esse requisito, a solução segue essa regra: **cálculo já é pré programado, a IA nunca calcula nada — só executa e interpreta — funcionando como uma ponte entre o código e o usuário final. **

```
+-----------------------------------------------------------+
|  Camada conversacional (AGENTES.md)                       |
|  Traduz linguagem natural em execução do main.py.         |
|  Nunca reproduz calculos manualmente.                     |
+---------------------------+--------------------------------+
                            |
+----------------------------v--------------------------------+
|  main.py -- orquestrador                                    |
|  Unico ponto de entrada. Recebe o caminho de um CSV.         |
+------+---------+---------+---------+----------+-------------+
       |         |         |         |          |
  cleaning_  analise_  recommend-  (HTML/     resumo_
  datasets   estatis-  ations.py    JSON/      sheets.py
  .py        tica.py                index)
```

Essa separação existe para **reduzir erros**: Seria muito arriscado deixar todos os cálculos nas responsabilidades de um modelo de linguagem natural, isso reduziria a padronização no método estatístico usado no Teste A/B e poderia resultar em valores incoerentes.   Isolando esses cálculos em funções Python puras e usando a IA apenas para tradução de linguagem natural e execução, a solução elimina o risco de alucinação numérica no resultado final — o mesmo dataset sempre produz a mesma recomendação,
independente de qual ferramenta de IA está rodando por cima.

O `AGENTES.md` funciona como o "manual de operação" do agente: ele
descreve exatamente quando e como cada script deve ser chamado, proibindo
explicitamente que a IA calcule ou interprete o CSV diretamente. Isso torna
a solução compatível com qualquer ferramenta agêntica (Claude Code, Cursor,
Antigravity, Gemini CLI, GPT personalizado) sem exigir nenhuma integração
específica de código — a forma como a solução irá funcionar está no arquivo de
instruções, não ligada a uma API de IA específica.

### 2.3 Metodologia estatística

- **Teste**: teste t de Welch (`scipy.stats.ttest_ind`, `equal_var=False`), comparando cada variante contra o grupo controle
- **Nível de significância**: 5% (p < 0.05)
- **Amostra mínima**: comparações com menos de 2 observações por grupo são sinalizadas como "dados insuficientes".
- **Métrica de decisão**: margem (comissão − cashback) é o critério primário — cashback mais alto costuma aumentar volume de compradores e venda, mas pode destruir rentabilidade, por isso volume isolado não é suficiente para recomendar escala
- **Regra de decisão**:
  1. Se a margem piora com significância estatística → variante descartada, independente das demais métricas
  2. Se a margem melhora com significância → variante é candidata forte
  3. Se a margem se mantém estável (sem diferença significativa) e algum indicador de apoio (compradores, comissão, vendas totais) melhora com significância → variante é candidata moderada
  4. Se nenhuma variante se qualifica → recomendação é manter o grupo controle

### 2.4 Robustez a dados ruins

- Valores monetários em formato brasileiro (`R$ 1.234,56`) são convertidos com tratamento de exceção — dados corrompidos viram `None` (dado ausente), nunca `0` silencioso
- Grupos são detectados dinamicamente a partir do dataset (não há suposição fixa de "Grupo 1/2/3")
- O grupo controle é inferido como o de menor rótulo numérico entre os grupos existentes
- A quantidade de variantes pode variar entre datasets sem qualquer alteração de código

### 2.5 Estrutura de pastas

```
├── scripts/
│   ├── main.py                 # ponto de entrada unico, orquestra o pipeline
│   ├── cleaning_datasets.py    # limpeza e validacao dos dados brutos
│   ├── analise_estatistica.py  # metricas e teste estatistico
│   ├── recommendations.py      # regra de decisao de negocio
│   └── resumo_sheets.py        # integracao com Google Sheets
├── datasets/                   # CSVs de entrada (parceiros A, B, C)
├── relatorios/                 # relatorios HTML/JSON gerados (indice em index.html)
├── credentials/                # nao versionado -- ver secao 1.3
├── AGENTES.md                  # instrucoes de comportamento do agente de IA
├── RESULTADOS.md               # resumo consolidado com links dos testes ja processados
└── requirements.txt
```

---

## 3. Limitações conhecidas

- A integração com Google Sheets requer que o usuário crie credencial própria (seção 1.3); sem ela, a análise e o relatório continuam sendo gerados normalmente
- O usuário ainda terá que instalar Python, git e rodar algumas linhas de código para preparar o ambiente para a IA usar a solução.
  Como próximos passos, o objetivo é que a solução evolua para funcionar de acordo com o padrão Model Context Protocol, fazendo da          solução uma Tool para a Inteligência Artificial.
- Links de relatório html publicados no GitHub (`htmlpreview.github.io`) só ficam ativos após o `git push` do arquivo correspondente — para análises novas rodadas localmente, o relatório está imediatamente disponível no computador de quem executou, mas o link público exige publicação manual
