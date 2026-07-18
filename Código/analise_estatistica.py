import pandas as pd
from scipy import stats
from cleaning_datasets import carregar_e_limpar


METRICAS = ["compradores", "comissão", "cashback", "vendas totais", "margem"]

def analisar_teste_ab(caminho_csv_ou_df):
    """
    Recebe o caminho de um CSV de teste A/B e devolve um dicionário com:
    - métricas resumidas por grupo (total e média diária)
    - comparação estatística de cada variante contra o grupo controle
    """
    
    if isinstance(caminho_csv_ou_df, str):
        df = carregar_e_limpar(caminho_csv_ou_df)
    else:
        df = caminho_csv_ou_df.copy()
    # Métrica principal para avaliar os grupos: lucro pra Méliuz depois de pagar o cashback
    df["margem"] = df["comissão"] - df["cashback"]

    grupos = sorted(df["Grupos de usuários"].unique())
    controle = grupos[0]  # assumimos que o grupo com rótulo menor é o controle

    # 1) Resumo descritivo por grupo (total e média diária de cada métrica)
    resumo_por_grupo = {}
    for grupo in grupos:
        dados_grupo = df[df["Grupos de usuários"] == grupo]
        resumo_por_grupo[grupo] = {}
        for metrica in METRICAS:
            total = dados_grupo[metrica].sum()
            media = dados_grupo[metrica].mean()
            resumo_por_grupo[grupo][metrica] = {"total": total, "media_diaria": media}
        

    # 2) Comparação estatística: cada variante vs o controle
    comparacoes = {}
    dados_controle = df[df["Grupos de usuários"] == controle]

    for grupo in grupos:
        if grupo == controle:
            continue  # não compara o controle com ele mesmo

        dados_variante = df[df["Grupos de usuários"] == grupo]
        comparacoes[grupo] = {}

        for metrica in METRICAS:
            valores_controle = dados_controle[metrica].dropna()
            valores_variante = dados_variante[metrica].dropna()

            # Precisamos de pelo menos 2 observações por grupo pra calcular variância
            if len(valores_controle) < 2 or len(valores_variante) < 2:
                comparacoes[grupo][metrica] = {
                    "p_valor": None,
                    "significativo": False,
                    "diferenca_pct": None,
                    "aviso": f"Dados insuficientes (controle={len(valores_controle)} dias, "
                             f"variante={len(valores_variante)} dias) — mínimo 2 dias por grupo",
                }
                continue

            t_stat, p_valor = stats.ttest_ind(
                valores_variante, valores_controle, equal_var=False
            )

            media_controle = valores_controle.mean()
            media_variante = valores_variante.mean()
            diferenca_pct = ((media_variante - media_controle) / media_controle) * 100

            comparacoes[grupo][metrica] = {
                "p_valor": round(p_valor, 4),
                "significativo": p_valor < 0.05,
                "diferenca_pct": round(diferenca_pct, 2)
            }

    return {
        "grupo_controle": controle,
        "resumo_por_grupo": resumo_por_grupo,
        "comparacoes": comparacoes,
    }


if __name__ == "__main__":
    resultado = analisar_teste_ab("datasets\dataset_03_parceiroC.csv")

    print(f"Grupo controle: {resultado['grupo_controle']}\n")

    for grupo, metricas in resultado["comparacoes"].items():
        print(f"--- {grupo} vs controle ---")
        for metrica, valores in metricas.items():
            if valores.get("aviso"):
                print(f"  {metrica:15}   {valores['aviso']}")
                continue
            status = " significativo" if valores["significativo"] else " não significativo"
            print(f"  {metrica:15} diferença: {valores['diferenca_pct']:+.1f}%   p={valores['p_valor']}   {status}")
        print()