import os
import sys
import json
import argparse
import pandas as pd
from datetime import datetime

# Corrige problemas de encoding no terminal do Windows (emoji/acentos causando erro)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass  # Python mais antigo, sem esse método -- segue sem quebrar

caminho_projeto = os.path.dirname(os.path.abspath(__file__))

try:
    from cleaning_datasets import carregar_e_limpar
    from analise_estatistica import analisar_teste_ab
    from recommendations import decidir_recomendacao
    from resumo_sheets import escrever_resultado_sheets
except ImportError as e:
    print(f"[ERRO] Falha ao importar os scripts locais: {e}")
    sys.exit(1)


def converter_tipos(obj):
    """Converte recursivamente tipos numpy/pandas para tipos nativos do Python."""
    if isinstance(obj, dict):
        return {k: converter_tipos(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [converter_tipos(v) for v in obj]
    elif hasattr(obj, "item"):
        return obj.item()
    elif isinstance(obj, float) and pd.isna(obj):
        return None
    else:
        return obj


def formatar_moeda(valor):
    """Formata um número como moeda brasileira: 12345.6 -> R$ 12.345,60"""
    if valor is None:
        return "N/D"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def gerar_linha_metrica_html(nome_exibicao, dados_controle, dados_variante, comparacao, e_custo=False):
    """
    Gera uma linha de tabela HTML comparando uma métrica entre controle e variante.
    'e_custo' marca métricas onde aumentar NÃO é necessariamente bom (ex: cashback é
    um custo -- crescer não deve ser colorido como "positivo" igual a uma métrica
    de resultado, mesmo que a diferença seja estatisticamente significativa).
    """
    if comparacao.get("aviso"):
        return f"""
        <tr>
            <td>{nome_exibicao}</td>
            <td colspan="4" class="aviso">⚠ {comparacao['aviso']}</td>
        </tr>"""

    diff = comparacao["diferenca_pct"]
    sig = comparacao["significativo"]
    p_valor = comparacao["p_valor"]

    if e_custo:
        # Cashback é custo: só descrevemos a variação, sem julgar como bom/ruim
        classe_css = "neutro"
        rotulo = "Significativo (variação de custo)" if sig else "Não significativo"
    elif sig and diff > 0:
        classe_css, rotulo = "positivo", "Significativo ↑"
    elif sig and diff < 0:
        classe_css, rotulo = "negativo", "Significativo ↓"
    else:
        classe_css, rotulo = "neutro", "Não significativo"

    is_monetario = nome_exibicao.lower() in ("comissão", "cashback", "vendas totais", "margem")
    fmt = formatar_moeda if is_monetario else (lambda v: f"{v:,.0f}".replace(",", "."))

    return f"""
    <tr>
        <td>{nome_exibicao}</td>
        <td>{fmt(dados_controle['media_diaria'])}/dia</td>
        <td>{fmt(dados_variante['media_diaria'])}/dia</td>
        <td class="{classe_css}">{diff:+.1f}%</td>
        <td class="{classe_css}">{rotulo} (p={p_valor})</td>
    </tr>"""


def gerar_relatorio_html(nome_parceiro, data_inicio, data_fim, resultado_analise, decisao):
    """
    Gera um relatório HTML autocontido (sem dependências externas) e
    apresentável para um gestor: recomendação em destaque no topo,
    seguida da tabela comparativa detalhada por variante.
    """
    controle = resultado_analise["grupo_controle"]
    resumo = resultado_analise["resumo_por_grupo"]
    comparacoes = resultado_analise["comparacoes"]

    metricas_exibicao = {
        "compradores": "Compradores",
        "comissão": "Comissão",
        "cashback": "Cashback",
        "vendas totais": "Vendas Totais",
        "margem": "Margem",
    }

    escalar = decisao["recomendacao"] != controle
    cor_recomendacao = "#0a7d3c" if escalar else "#6b6b6b"
    texto_acao = (
        f"Escalar {decisao['recomendacao']} para 100% do tráfego"
        if escalar
        else f"Manter {controle} (controle) — nenhuma variante superou com confiança estatística"
    )

    blocos_variantes = ""
    for variante, metricas_comp in comparacoes.items():
        linhas = "".join(
            gerar_linha_metrica_html(
                nome_exibicao,
                resumo[controle][chave_metrica],
                resumo[variante][chave_metrica],
                metricas_comp[chave_metrica],
                e_custo=(chave_metrica == "cashback"),
            )
            for chave_metrica, nome_exibicao in metricas_exibicao.items()
        )
        blocos_variantes += f"""
        <div class="bloco-variante">
            <h3>{variante} <span class="vs">vs. controle ({controle})</span></h3>
            <table>
                <thead>
                    <tr><th>Métrica</th><th>{controle} (média/dia)</th><th>{variante} (média/dia)</th><th>Diferença</th><th>Significância</th></tr>
                </thead>
                <tbody>{linhas}</tbody>
            </table>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Relatório de Teste A/B — {nome_parceiro}</title>
<style>
    body {{ font-family: -apple-system, Segoe UI, Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; color: #1a1a1a; line-height: 1.5; }}
    h1 {{ font-size: 24px; border-bottom: 3px solid #1a1a1a; padding-bottom: 10px; }}
    h2 {{ font-size: 18px; margin-top: 30px; }}
    h3 {{ font-size: 15px; margin-bottom: 8px; }}
    .vs {{ font-weight: normal; color: #777; font-size: 13px; }}
    .meta {{ color: #666; font-size: 14px; margin-bottom: 20px; }}
    .caixa-recomendacao {{ background: #f5f5f5; border-left: 5px solid {cor_recomendacao}; padding: 18px 22px; margin: 20px 0; border-radius: 4px; }}
    .caixa-recomendacao .titulo {{ font-size: 13px; text-transform: uppercase; color: #666; letter-spacing: 0.5px; }}
    .caixa-recomendacao .acao {{ font-size: 20px; font-weight: 700; color: {cor_recomendacao}; margin: 6px 0; }}
    .caixa-recomendacao .motivo {{ font-size: 14px; color: #333; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 13px; }}
    th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid #e0e0e0; }}
    th {{ background: #fafafa; font-weight: 600; color: #444; }}
    .positivo {{ color: #0a7d3c; font-weight: 600; }}
    .negativo {{ color: #b3261e; font-weight: 600; }}
    .neutro {{ color: #777; }}
    .aviso {{ color: #9a6700; font-style: italic; }}
    .bloco-variante {{ margin-bottom: 28px; }}
    footer {{ margin-top: 40px; padding-top: 16px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #999; }}
</style>
</head>
<body>
    <h1>Relatório de Teste A/B — {nome_parceiro}</h1>
    <div class="meta">
        Período analisado: {data_inicio} a {data_fim} &nbsp;|&nbsp;
        Grupo controle: {controle} &nbsp;|&nbsp;
        Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}
    </div>

    <div class="caixa-recomendacao">
        <div class="titulo">Recomendação</div>
        <div class="acao">{texto_acao}</div>
        <div class="motivo">{decisao['motivo']}</div>
    </div>

    <h2>Detalhamento por variante</h2>
    {blocos_variantes}

    <footer>
        Metodologia: teste t de Welch comparando cada variante contra o grupo controle,
        com nível de significância de 5% (p &lt; 0.05). Métrica de decisão principal: margem
        (comissão − cashback). Relatório gerado automaticamente.
    </footer>
</body>
</html>"""

    return html


def atualizar_indice_relatorios(pasta_relatorios):
    """
    Escaneia a pasta de relatórios e regenera uma página índice (index.html)
    listando TODOS os testes já analisados até agora -- sem depender de
    nenhuma lista fixa. Isso é o que torna o "acesso ao relatório" escalável:
    a cada novo teste rodado, essa função é chamada de novo e o índice se
    atualiza sozinho, sem precisar editar README nem nenhum link manualmente.
    """
    arquivos_json = sorted(
        [f for f in os.listdir(pasta_relatorios) if f.startswith("resumo_") and f.endswith(".json")]
    )

    linhas_tabela = ""
    for nome_arquivo in arquivos_json:
        with open(os.path.join(pasta_relatorios, nome_arquivo), "r", encoding="utf-8") as f:
            dados = json.load(f)

        nome_arquivo_limpo = dados["parceiro"].replace(" ", "_").lower()
        caminho_relatorio_relativo = f"relatorio_{nome_arquivo_limpo}.html"

        escalou = dados["recomendacao"] != dados["resultado_analise"]["grupo_controle"]
        cor = "#0a7d3c" if escalou else "#6b6b6b"

        linhas_tabela += f"""
        <tr>
            <td>{dados['parceiro']}</td>
            <td>{dados['data_inicio']} a {dados['data_fim']}</td>
            <td style="color:{cor}; font-weight:600;">{dados['recomendacao']}</td>
            <td>{dados['data_execucao']}</td>
            <td><a href="{caminho_relatorio_relativo}">Ver relatório completo →</a></td>
        </tr>"""

    html_indice = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Índice de Testes A/B — Méliuz</title>
<style>
    body {{ font-family: -apple-system, Segoe UI, Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; color: #1a1a1a; }}
    h1 {{ font-size: 22px; border-bottom: 3px solid #1a1a1a; padding-bottom: 10px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; }}
    th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid #e0e0e0; }}
    th {{ background: #fafafa; }}
    .vazio {{ color: #999; font-style: italic; padding: 20px 0; }}
</style>
</head>
<body>
    <h1>Testes A/B Analisados</h1>
    <p>Atualizado automaticamente a cada execução de <code>main.py</code>. Total: {len(arquivos_json)} teste(s).</p>
    {"<table><thead><tr><th>Parceiro</th><th>Período</th><th>Recomendação</th><th>Analisado em</th><th></th></tr></thead><tbody>" + linhas_tabela + "</tbody></table>" if arquivos_json else '<p class="vazio">Nenhum teste analisado ainda.</p>'}
</body>
</html>"""

    caminho_indice = os.path.join(pasta_relatorios, "index.html")
    with open(caminho_indice, "w", encoding="utf-8") as f:
        f.write(html_indice)

    return caminho_indice


# Dados do repositório GitHub, usados para montar o link público do relatório
# (assim a planilha compartilhada aponta para um link que qualquer pessoa do
# time consegue abrir, não um caminho local que só existe no seu computador)
GITHUB_USUARIO = "Julia-cel"
GITHUB_REPO = "Analise-Automatizada-de-Testes-A-B"


def montar_link_relatorio(nome_arquivo_limpo: str) -> str:
    """Monta o link público (via htmlpreview.github.io) para o relatório HTML no GitHub."""
    url_bruta = (
        f"https://raw.githubusercontent.com/{GITHUB_USUARIO}/{GITHUB_REPO}/main/"
        f"relatorios/relatorio_{nome_arquivo_limpo}.html"
    )
    return f"https://htmlpreview.github.io/?{url_bruta}"


def processar_teste_ab(caminho_csv, abrir_navegador=False):
    """
    Executa a pipeline completa de análise:
    1. Carrega e limpa o dataset.
    2. Identifica parceiro e metadados.
    3. Executa a análise estatística.
    4. Gera a recomendação final de negócio.
    5. Gera o relatório HTML apresentável.
    6. Atualiza a planilha no Google Sheets.
    """
    if not os.path.exists(caminho_csv):
        print(f"[ERRO] O arquivo especificado nao existe: {caminho_csv}")
        sys.exit(1)

    print(f"\n--- [1/6] Carregando e limpando dataset: {caminho_csv} ---")
    df_limpo = carregar_e_limpar(caminho_csv)

    if "Parceiro" in df_limpo.columns:
        nome_parceiro = df_limpo["Parceiro"].iloc[0]
    else:
        nome_parceiro = os.path.basename(caminho_csv).replace(".csv", "").replace("dataset_", "").title()

    data_inicio = df_limpo["Data"].min().strftime("%Y-%m-%d")
    data_fim = df_limpo["Data"].max().strftime("%Y-%m-%d")

    nome_teste = f"Teste A/B - {nome_parceiro}"
    descricao_teste = f"Analise automatizada executada para o parceiro {nome_parceiro}. Periodo dos dados: {data_inicio} ate {data_fim}."

    print(f"Parceiro identificado: {nome_parceiro}")
    print(f"Periodo: {data_inicio} ate {data_fim}")

    print("\n--- [2/6] Rodando analise estatistica ---")
    resultado_analise = analisar_teste_ab(df_limpo)

    print("\n--- [3/6] Gerando recomendacoes de negocio ---")
    decisao = decidir_recomendacao(resultado_analise)
    print(f"Recomendacao: {decisao['recomendacao']}")
    print(f"Motivo: {decisao['motivo']}")

    PASTA_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
    PASTA_PROJETO = os.path.dirname(PASTA_SCRIPTS)
    PASTA_RELATORIOS = os.path.join(PASTA_PROJETO, "relatorios")
    os.makedirs(PASTA_RELATORIOS, exist_ok=True)

    nome_arquivo_limpo = nome_parceiro.replace(" ", "_").lower()
    caminho_json = os.path.join(PASTA_RELATORIOS, f"resumo_{nome_arquivo_limpo}.json")
    caminho_html = os.path.join(PASTA_RELATORIOS, f"relatorio_{nome_arquivo_limpo}.html")

    print("\n--- [4/6] Salvando resumo estruturado (JSON) ---")
    resumo_geral = converter_tipos({
        "parceiro": nome_parceiro,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "descricao": descricao_teste,
        "resultado_analise": resultado_analise,
        "recomendacao": decisao["recomendacao"],
        "motivo": decisao["motivo"],
        "data_execucao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(resumo_geral, f, indent=4, ensure_ascii=False)
    print(f"JSON salvo em: {caminho_json}")

    print("\n--- [5/6] Gerando relatório HTML apresentável ---")
    html = gerar_relatorio_html(nome_parceiro, data_inicio, data_fim, resultado_analise, decisao)
    with open(caminho_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Relatorio HTML salvo em: {caminho_html}")

    print("\n--- [6/6] Registrando dados no Google Sheets ---")
    link_relatorio = montar_link_relatorio(nome_arquivo_limpo)
    try:
        escrever_resultado_sheets(
            nome_planilha="Registro- Análise Teste A/B ",
            nome_teste=nome_teste,
            descricao=descricao_teste,
            resultado_analise=resultado_analise,
            decisao_recomendacao=decisao,
            link_relatorio=link_relatorio,
        )
    except Exception as e:
        print(f"[AVISO] Nao foi possivel escrever na planilha do Google Sheets: {e}")
        print("Verifique suas credenciais e conexao com a internet.")

    exibir_resumo_terminal(nome_parceiro, data_inicio, data_fim, resultado_analise, decisao)

    print("\n--- Atualizando índice de relatórios ---")
    caminho_indice = atualizar_indice_relatorios(PASTA_RELATORIOS)
    print(f"Índice atualizado: {caminho_indice}")

    print(f"\nRelatório disponível em: {os.path.abspath(caminho_html)}")
    print(f"Índice com todos os testes em: {os.path.abspath(caminho_indice)}")

    if abrir_navegador:
        try:
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(caminho_html)}")
        except Exception as e:
            print(f"[AVISO] Nao foi possivel abrir o navegador automaticamente: {e}")


def exibir_resumo_terminal(parceiro, data_inicio, data_fim, resultado_analise, decisao):
    """Exibe um painel visual formatado no terminal com o resumo da análise."""
    controle = resultado_analise["grupo_controle"]
    comparacoes = resultado_analise["comparacoes"]

    print("\n" + "=" * 70)
    print(f"PAINEL DE RESULTADOS - TESTE A/B: {parceiro.upper()}")
    print("=" * 70)
    print(f" Periodo dos dados: {data_inicio} ate {data_fim}")
    print(f" Grupo Controle   : {controle}")
    print("-" * 70)
    print(" RECOMENDACAO:")
    print(f" >> {decisao['recomendacao'].upper()}")
    print(f" Motivo: {decisao['motivo']}")
    print("-" * 70)
    print(" COMPARATIVOS CONTRA O CONTROLE:")

    for variante, metricas in comparacoes.items():
        print(f"\n Variante: {variante}")
        for metrica, valores in metricas.items():
            if valores.get("aviso"):
                print(f"   - {metrica.capitalize():15}: {valores['aviso']}")
                continue
            sig_str = "SIGNIFICATIVO" if valores["significativo"] else "NAO SIGNIFICATIVO"
            dif_str = f"{valores['diferenca_pct']:+.2f}%" if valores["diferenca_pct"] is not None else "N/A"
            p_val = valores["p_valor"]
            print(f"   - {metrica.capitalize():15}: {dif_str:8} | p={p_val:<6} | {sig_str}")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Motor de automacao e analise de testes A/B.")
    parser.add_argument("dataset", help="Caminho do arquivo CSV contendo os dados do teste A/B.")
    parser.add_argument(
        "--abrir",
        action="store_true",
        help="Abre o relatório automaticamente no navegador ao final (desativado por padrão).",
    )
    args = parser.parse_args()
    processar_teste_ab(args.dataset, abrir_navegador=args.abrir)