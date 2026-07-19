# AGENTS.md

# Sistema de Automação para Análise de Testes A/B

## Objetivo

Este projeto implementa uma pipeline completa para análise de testes A/B de cashback.

O usuário deve fornecer apenas o dataset CSV.

Toda a lógica estatística, de negócio e geração de artefatos está implementada no projeto.

O agente NÃO deve reproduzir essa lógica manualmente.

---

# REGRA OBRIGATÓRIA

Sempre que o usuário solicitar:

- analisar um teste A/B
- analisar um dataset
- gerar uma recomendação
- decidir qual grupo escalar
- avaliar um experimento

você DEVE executar a pipeline completa utilizando exclusivamente o arquivo `main.py`.

É proibido responder realizando cálculos manuais ou interpretando diretamente o CSV.
A lógica de decisão está implementada em recommendations.py.
Nunca reproduza essa lógica manualmente.
Sempre utilize o resultado retornado pela pipeline.

Uma execução somente é considerada concluída quando TODOS os passos abaixo forem executados.

# Pipeline obrigatória

1. Executar:

python scripts/main.py datasets/arquivo.csv

2. Aguardar a conclusão.

3. Verificar se o processo terminou sem erro.

4. Confirmar que:

✓ análise estatística foi executada

✓ recomendação foi gerada

✓ JSON foi criado

✓ CSV foi criado

✓ Google Sheets foi atualizado

5. Somente então responder ao usuário.

---

# REGRA OBRIGATÓRIA: Abertura do relatório HTML

Por padrão, o passo 1 da Pipeline obrigatória NUNCA abre o relatório no navegador.
O relatório é apenas gerado e salvo em disco.

## Quando adicionar a flag --abrir

Adicione a flag `--abrir` ao comando do passo 1 SOMENTE quando o usuário
solicitar explicitamente VER, ABRIR ou MOSTRAR o relatório. Exemplos de
solicitação explícita:

- "mostra o relatório"
- "abre o relatório do parceiro A"
- "quero ver o relatório completo"
- "exibe o resultado em tela"

Nesses casos, o comando do passo 1 passa a ser:

python scripts/main.py datasets/arquivo.csv --abrir

## Quando NÃO adicionar a flag --abrir

Se o usuário solicitar apenas a análise (ex: "analisa o parceiro A", "roda
esse teste", "avalia esse experimento"), SEM mencionar ver, abrir ou
mostrar o relatório, o comando DEVE ser executado sem a flag `--abrir`.

É proibido abrir o navegador automaticamente sem essa solicitação explícita.
A ausência da flag não interrompe nem invalida a execução da pipeline --
todos os passos de 1 a 5 da Pipeline obrigatória continuam sendo cumpridos
normalmente, apenas sem a abertura do navegador.

---

# Como responder

Nunca responda apenas com uma análise em linguagem natural.

Após executar a pipeline:

- informe a recomendação;

- informe a justificativa;

- informe que os arquivos foram gerados;

- informe que a planilha foi atualizada.
