def decidir_recomendacao(resultado_analise: dict) -> dict:
    """
    Aplica a regra de negócio para decidir qual variante escalar.

    Regra:
    - MARGEM é o critério inegociável: se piorou com significância, a variante
      é descartada, não importa o que aconteceu com as outras métricas.
    - Se a margem melhorou com significância, a variante é uma CANDIDATA FORTE.
    - Se a margem NÃO teve diferença significativa (nem melhorou nem piorou),
      a variante ainda pode ser candidata SE algum indicador guardrail
      (compradores, comissão, vendas totais) melhorou com significância —
      nesse caso, ganhamos em outra frente sem sacrificar a margem.
    - Entre candidatas, prioriza sempre as fortes (ganho de margem) sobre as
      moderadas (margem estável + ganho em guardrail).
    - Se não houver nenhuma candidata, a recomendação é manter o controle.
    """
    controle = resultado_analise["grupo_controle"]
    comparacoes = resultado_analise["comparacoes"]
    metricas_guardrail = ["compradores", "comissão", "vendas totais"]

    candidatas_fortes = []
    candidatas_moderadas = []

    for grupo, metricas in comparacoes.items():
        margem = metricas["margem"]

        if margem["p_valor"] is None:
            continue  # dados insuficientes pra margem, não dá pra avaliar essa variante

        margem_piorou = margem["significativo"] and margem["diferenca_pct"] < 0
        if margem_piorou:
            continue  # descartada, critério inegociável

        margem_melhorou = margem["significativo"] and margem["diferenca_pct"] > 0

        if margem_melhorou:
            candidatas_fortes.append({
                "grupo": grupo,
                "ganho_margem_pct": margem["diferenca_pct"],
                "p_valor_margem": margem["p_valor"],
            })
            continue

        # Margem estável (não significativa) -> verifica os guardrails
        ganhos_guardrail = []
        for nome_metrica in metricas_guardrail:
            dado = metricas[nome_metrica]
            if dado["p_valor"] is None:
                continue
            melhorou_com_confianca = dado["significativo"] and dado["diferenca_pct"] > 0
            if melhorou_com_confianca:
                ganhos_guardrail.append({"metrica": nome_metrica, "diferenca_pct": dado["diferenca_pct"]})

        if ganhos_guardrail:
            candidatas_moderadas.append({"grupo": grupo, "ganhos_guardrail": ganhos_guardrail})

    # Prioridade 1: candidata forte (ganho de margem real)
    if candidatas_fortes:
        melhor = max(candidatas_fortes, key=lambda c: c["ganho_margem_pct"])
        return {
            "recomendacao": melhor["grupo"],
            "motivo": f"{melhor['grupo']} teve margem {melhor['ganho_margem_pct']:+.1f}% "
                      f"maior que o controle, com significância estatística "
                      f"(p={melhor['p_valor_margem']}).",
        }

    # Prioridade 2: candidata moderada (margem estável + ganho em outro indicador)
    if candidatas_moderadas:
        melhor = max(candidatas_moderadas, key=lambda c: len(c["ganhos_guardrail"]))
        nomes_ganhos = ", ".join(
            f"{g['metrica']} {g['diferenca_pct']:+.1f}%" for g in melhor["ganhos_guardrail"]
        )
        return {
            "recomendacao": melhor["grupo"],
            "motivo": f"{melhor['grupo']} manteve a margem estável em relação ao controle "
                      f"(sem evidência de piora) e apresentou ganho estatisticamente "
                      f"significativo em: {nomes_ganhos}.",
        }

    # Nenhuma variante se qualificou
    return {
        "recomendacao": controle,
        "motivo": f"Nenhuma variante superou o grupo controle ({controle}) em margem, "
                  f"nem manteve a margem com ganho comprovado em outros indicadores. "
                  f"Manter o controle.",
    }


if __name__ == "__main__":
    from analise_estatistica import analisar_teste_ab

    resultado = analisar_teste_ab("datasets\dataset_01_parceiroA.csv")
    decisao = decidir_recomendacao(resultado)

    print(f"\nRecomendação: escalar {decisao['recomendacao']}")
    print(f"Motivo: {decisao['motivo']}")