import os
import gspread
from google.oauth2.service_account import Credentials

# Escopos necessários: acesso a planilhas + acesso a arquivos do Drive (pra localizar a planilha)
ESCOPOS = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Caminho calculado a partir da localização deste arquivo, não de onde o
# terminal está aberto -- assim funciona igual seja chamado de scripts/,
# da raiz do projeto, ou por uma ferramenta de IA rodando de qualquer lugar.
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_PROJETO = os.path.dirname(PASTA_SCRIPT)
CAMINHO_CREDENCIAIS = os.path.join(PASTA_PROJETO, "credentials", "case-meliuz-502620-9a31b277e2e6.json")


def conectar_planilha(nome_planilha: str):
    """
    Autentica usando a conta de serviço e abre a planilha pelo nome.
    Se algo estiver errado (API não ativada, planilha não compartilhada,
    caminho errado), o erro vai aparecer aqui de forma explícita.
    """
    credenciais = Credentials.from_service_account_file(CAMINHO_CREDENCIAIS, scopes=ESCOPOS)
    cliente = gspread.authorize(credenciais)
    planilha = cliente.open(nome_planilha)
    return planilha


def escrever_resultado_sheets(nome_planilha: str, nome_teste: str, descricao: str, resultado_analise: dict, decisao_recomendacao: dict, link_relatorio: str):
    """
    Consolida as estatísticas do teste e a decisão tomada e adiciona na planilha do Google Sheets.

    Colunas escritas:
    - Resultado: resumo em linguagem natural (o "motivo" já calculado)
    - Decisão Tomada: ação por extenso ("Manter Grupo 1" / "Escalar Grupo 2")
    - Justificativa: link para o relatório HTML completo, com texto padrão
    """
    from datetime import datetime
    data_hoje = datetime.now().strftime("%Y-%m-%d")

    controle = resultado_analise["grupo_controle"]
    grupo_recomendado = decisao_recomendacao["recomendacao"]
    motivo = decisao_recomendacao["motivo"]

    # Decisão por extenso: se o grupo recomendado é o próprio controle, a ação é "manter";
    # caso contrário, a ação é "escalar" a variante vencedora.
    if grupo_recomendado == controle:
        decisao_texto = f"Manter {grupo_recomendado}"
    else:
        decisao_texto = f"Escalar {grupo_recomendado}"

    justificativa_texto = f"Para mais informações acesse o relatório: {link_relatorio}"

    planilha = conectar_planilha(nome_planilha)
    aba = planilha.sheet1

    nova_linha = [
        data_hoje,
        nome_teste,
        descricao,
        motivo,             # linguagem natural -- coluna "Resultado"
        decisao_texto,      # ação por extenso -- coluna "Decisão Tomada"
        justificativa_texto,  # link + texto padrão -- coluna "Justificativa"
    ]


    aba.append_row(nova_linha)
    print("[OK] Linha adicionada com sucesso no Google Sheets!")


if __name__ == "__main__":
    print(f"Procurando credenciais em: {CAMINHO_CREDENCIAIS}")
    print("Tentando conectar...")
    try:
        planilha = conectar_planilha("Registro- Análise Teste A/B ")
        print(f"[OK] Conectado com sucesso! Planilha: {planilha.title}")
        print(f"Abas disponiveis: {[aba.title for aba in planilha.worksheets()]}")
    except FileNotFoundError:
        print(f"[ERRO] Nao achei o arquivo de credenciais em: {CAMINHO_CREDENCIAIS}")
        print("   Confira se a pasta credentials/ esta na raiz do projeto (fora de scripts/).")
    except gspread.exceptions.SpreadsheetNotFound:
        print("[ERRO] A planilha nao foi encontrada.")
        print("   Confira se o NOME esta exatamente igual ao nome real da planilha,")
        print("   e se ela foi compartilhada com o e-mail da conta de serviço.")
    except Exception as e:
        print(f"[ERRO] Erro inesperado: {type(e).__name__}: {e}")