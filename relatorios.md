# Resultados — Análise de Testes A/B (Méliuz)

Este arquivo consolida os resultados dos 3 testes A/B analisados, com acesso
direto à planilha de acompanhamento e aos relatórios completos de cada teste.

## Planilha de acompanhamento

[Ver planilha completa](https://docs.google.com/spreadsheets/d/11rUTDzbcHEF8QNlcwO-CyvkuN9OfuupikytPEfyMVzk/edit?usp=sharing)

## Relatórios individuais

| Parceiro | Período analisado | Recomendação | Relatório completo |
|---|---|---|---|
| Parceiro A | 2011-01-01 a 2011-04-02 | Manter Grupo 1 | [Ver relatório](https://htmlpreview.github.io/?https://raw.githubusercontent.com/Julia-cel/Analise-Automatizada-de-Testes-A-B/main/relatorios/relatorio_parceiro_a.html) |
| Parceiro B | 2011-05-01 a 2011-06-30 | Manter Grupo 1 | [Ver relatório](https://htmlpreview.github.io/?https://raw.githubusercontent.com/Julia-cel/Analise-Automatizada-de-Testes-A-B/main/relatorios/relatorio_parceiro_b.html) |
| Parceiro C | 2011-07-01 a 2011-08-04 | Manter Grupo 1 | [Ver relatório](https://htmlpreview.github.io/?https://raw.githubusercontent.com/Julia-cel/Analise-Automatizada-de-Testes-A-B/main/relatorios/relatorio_parceiro_c.html) |

## Metodologia (resumo)

Cada teste foi analisado comparando o grupo controle contra cada variante,
usando teste t de Welch (nível de significância de 5%). A métrica de decisão
principal é a **margem** (comissão − cashback); métricas de compradores,
comissão e vendas totais funcionam como indicadores de apoio. Uma variante só
é recomendada para escalar quando supera o controle em margem com
significância estatística, ou quando mantém a margem estável e apresenta
ganho comprovado em algum indicador de apoio. Detalhes completos da
metodologia e do código estão no [README](README.md).