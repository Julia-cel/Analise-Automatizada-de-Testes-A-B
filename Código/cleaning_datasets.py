import pandas as pd
import re


def formatar_valor_monetario(valor):
    """
    Converte uma string de moeda no formato brasileiro para float.
    Exemplos de entrada: 'R$ 1.478' -> 1478.0
                          'R$ 1.202,50' -> 1202.5
                          '' ou None -> None 
    """
    ## Caso 1: célula vazia ou NaN ##

    if pd.isna(valor):
        return None

    s = str(valor).strip()

    # Caso 2: string vazia mesmo depois de tirar espaços 
    if s == "":
        return None

    s = re.sub(r"[R$\s]", "", s)  # remove "R$" e espaços internos

    if "," in s:
        # Tem vírgula -> formato completo BR: ponto é milhar, vírgula é decimal
        s = s.replace(".", "").replace(",", ".")
    else:
        # Sem vírgula -> o ponto que aparece é separador de milhar
        s = s.replace(".", "")

    try:
        return float(s)
    except ValueError:
        # Valor que não conseguimos interpretar - melhor sinalizar que 'quebrar' o pipeline
        return None


def carregar_e_limpar(caminho_csv):
    """
    Lê o CSV de um teste A/B e devolve um DataFrame limpo, pronto pra análise.
    Funciona pra qualquer parceiro (A, B ou C) sem alteração de código.
    """
    df = pd.read_csv(caminho_csv)

    # Converte a coluna de data pro tipo datetime de verdade (não string)
    df["Data"] = pd.to_datetime(df["Data"], format="%Y-%m-%d")

    # Aplica a função de formatação monetária nas 3 colunas de valor
    colunas_monetarias = ["comissão", "cashback", "vendas totais"]
    for col in colunas_monetarias:
        df[col] = df[col].apply(formatar_valor_monetario)

    # Detecta quais grupos existem nesse dataset específico
    grupos = sorted(df["Grupos de usuários"].unique())
    print(f"Grupos encontrados: {grupos}")

    # Relatório rápido de qualidade de dados: quantas linhas têm valor ausente? #
    linhas_com_problema = df[colunas_monetarias].isna().any(axis=1).sum()
    if linhas_com_problema > 0:
        print(f"{linhas_com_problema} linha(s) com valor monetário ausente/inválido")

    return df


if __name__ == "__main__":
    # Testando a função isoladamente antes de usar no dataset inteiro
    testes = ["R$ 1.478", "R$ 131.409", "R$ 1.202,50", "", None, "R$ -"]
    for t in testes:
        print(f"{str(t):15} -> {formatar_valor_monetario(t)}")

    print("\n--- Testando carregamento do CSV completo ---")
    df = carregar_e_limpar("datasets/dataset_02_parceiroB.csv")
    print(df)