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

# Como responder

Nunca responda apenas com uma análise em linguagem natural.

Após executar a pipeline:

- informe a recomendação;

- informe a justificativa;

- informe que os arquivos foram gerados;

- informe que a planilha foi atualizada.