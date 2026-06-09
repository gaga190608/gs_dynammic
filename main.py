"""
╔══════════════════════════════════════════════════════════════╗
║        EXOSCORE — Índice de Habitabilidade Exoplanetária     ║
║        Dynamic Programming — FIAP 2ESPY 2026                ║
╚══════════════════════════════════════════════════════════════╝

Estruturas e algoritmos utilizados:
  - Fila (deque): pipeline de processamento de exoplanetas
  - Busca Binária Recursiva: localização de exoplaneta por nome
  - Recursividade: implementada na busca binária e no score
"""

import json
import math
import requests
from collections import deque

# ─────────────────────────────────────────────
# 1. CARREGAMENTO DE DADOS
# ─────────────────────────────────────────────

NASA_API_URL = (
    "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
    "?query=select+pl_name,pl_rade,pl_eqt,pl_orbsmax,st_teff"
    "+from+pscomppars"
    "+where+pl_rade+is+not+null+and+pl_eqt+is+not+null"
    "+and+pl_orbsmax+is+not+null+and+pl_rade+%3C+2.5"
    "+order+by+pl_name+asc"
    "&format=json&maxrec=50"
)

ARQUIVO_LOCAL = "exoplanetas.json"


def carregar_dados_api() -> list:
    """Tenta buscar dados da NASA Exoplanet Archive via API REST."""
    print("  📡 Conectando à NASA Exoplanet Archive...")
    response = requests.get(NASA_API_URL, timeout=10)
    response.raise_for_status()
    dados = response.json()
    print(f"  ✅ {len(dados)} registros obtidos da API NASA.")
    return dados


def carregar_dados_arquivo(caminho: str) -> list:
    """Carrega exoplanetas de arquivo JSON local."""
    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)
    print(f"  ✅ {len(dados)} registros carregados de '{caminho}'.")
    return dados


def obter_dados() -> list:
    """
    Tenta carregar da API. Em caso de falha, usa o arquivo local.
    Garante no mínimo 30 registros para processamento.
    """
    try:
        dados = carregar_dados_api()
    except Exception as e:
        print(f"  ⚠️  API indisponível ({type(e).__name__}). Usando arquivo local.")
        dados = carregar_dados_arquivo(ARQUIVO_LOCAL)

    if len(dados) < 30:
        raise ValueError(f"Base de dados insuficiente: {len(dados)} registros (mínimo: 30).")

    return dados


# ─────────────────────────────────────────────
# 2. CÁLCULO DO EXOSCORE
# ─────────────────────────────────────────────

def calcular_score_temperatura(eqt: float) -> float:
    """
    Pontuação de temperatura de equilíbrio (0–100).
    Faixa ideal: 273–323 K (0 °C a 50 °C — água líquida possível).
    Penalidade progressiva fora da faixa.
    """
    if 273 <= eqt <= 323:
        return 100.0
    distancia = min(abs(eqt - 273), abs(eqt - 323))
    return max(0.0, 100.0 - distancia * 0.55)


def calcular_score_raio(rade: float) -> float:
    """
    Pontuação de raio planetário (0–100).
    Perfil rochoso: 0.5 – 1.6 R⊕ (conservador) / até 2.5 R⊕ (otimista).
    Máximo próximo de 1.0 R⊕ (Terra).
    """
    if 0.5 <= rade <= 1.6:
        return max(0.0, 100.0 - abs(rade - 1.0) * 28.0)
    elif 1.6 < rade <= 2.5:
        return max(0.0, 45.0 - (rade - 1.6) * 50.0)
    else:
        return max(0.0, 20.0 - abs(rade - 1.0) * 10.0)


def calcular_score_zona(orbsmax: float, st_teff: float) -> float:
    """
    Pontuação de zona habitável estelar (0–100).
    Estima os limites interno/externo da zona habitável
    com base na luminosidade da estrela (aproximação por Teff).
    """
    # Luminosidade relativa ao Sol: L ∝ (Teff / 5778)^4 (estrela de sequência principal)
    luminosidade = (st_teff / 5778) ** 4
    zh_interno = math.sqrt(luminosidade / 1.1)   # limite quente (AU)
    zh_externo = math.sqrt(luminosidade / 0.53)  # limite frio  (AU)

    if zh_interno <= orbsmax <= zh_externo:
        return 100.0
    elif orbsmax < zh_interno:
        proporcao = (zh_interno - orbsmax) / zh_interno
        return max(0.0, 100.0 - proporcao * 110.0)
    else:
        proporcao = (orbsmax - zh_externo) / zh_externo
        return max(0.0, 100.0 - proporcao * 90.0)


def calcular_exoscore(pl_rade: float, pl_eqt: float,
                      pl_orbsmax: float, st_teff: float = 5778) -> float:
    """
    Score final de habitabilidade (0–100), ponderado:
      40% temperatura | 35% raio | 25% zona estelar
    """
    s_temp  = calcular_score_temperatura(pl_eqt)
    s_raio  = calcular_score_raio(pl_rade)
    s_zona  = calcular_score_zona(pl_orbsmax, st_teff)
    score   = s_temp * 0.40 + s_raio * 0.35 + s_zona * 0.25
    return round(min(100.0, max(0.0, score)), 2)


# ─────────────────────────────────────────────
# 3. FILA DE PROCESSAMENTO (QUEUE)
# ─────────────────────────────────────────────

def criar_fila_processamento(dados_brutos: list) -> deque:
    """
    Carrega todos os exoplanetas em uma Fila (deque).
    A fila representa o pipeline de triagem: cada planeta
    aguarda sua vez de ter o ExoScore calculado (FIFO).
    """
    fila = deque()
    for planeta in dados_brutos:
        fila.append(planeta)
    return fila


def processar_fila(fila: deque) -> list:
    """
    Consome a fila (FIFO), calcula o ExoScore de cada planeta
    e retorna a lista de planetas processados.
    Planetas com dados insuficientes são ignorados com aviso.
    """
    processados = []
    ignorados   = 0

    while fila:
        planeta = fila.popleft()

        nome     = planeta.get("pl_name")
        rade     = planeta.get("pl_rade")
        eqt      = planeta.get("pl_eqt")
        orbsmax  = planeta.get("pl_orbsmax")
        st_teff  = planeta.get("st_teff", 5778)

        # Regra de negócio: score só é calculado com todos os parâmetros
        if None in (nome, rade, eqt, orbsmax):
            ignorados += 1
            continue

        score = calcular_exoscore(
            pl_rade=float(rade),
            pl_eqt=float(eqt),
            pl_orbsmax=float(orbsmax),
            st_teff=float(st_teff) if st_teff else 5778,
        )

        processados.append({
            "pl_name":   nome,
            "pl_rade":   float(rade),
            "pl_eqt":    float(eqt),
            "pl_orbsmax":float(orbsmax),
            "st_teff":   float(st_teff) if st_teff else 5778,
            "exoscore":  score,
        })

    if ignorados:
        print(f"  ⚠️  {ignorados} planeta(s) ignorado(s) por dados insuficientes.")

    return processados


# ─────────────────────────────────────────────
# 4. BUSCA BINÁRIA RECURSIVA
# ─────────────────────────────────────────────

def busca_binaria_recursiva(lista_ordenada: list, alvo: str,
                            inicio: int, fim: int) -> int:
    """
    Busca binária recursiva por nome de exoplaneta (case-insensitive).

    Parâmetros:
        lista_ordenada : lista de dicionários ordenada por 'pl_name'
        alvo           : nome buscado
        inicio, fim    : índices do subarray atual

    Retorna:
        Índice do elemento encontrado, ou -1 se não existir.

    Base da recursão: inicio > fim → elemento não existe.
    Passo recursivo: compara o meio e descarta metade da lista.
    """
    # Caso base: intervalo vazio → não encontrado
    if inicio > fim:
        return -1

    meio      = (inicio + fim) // 2
    nome_meio = lista_ordenada[meio]["pl_name"].lower()
    alvo_low  = alvo.lower()

    if nome_meio == alvo_low:
        return meio                                              # encontrado
    elif nome_meio < alvo_low:
        return busca_binaria_recursiva(lista_ordenada, alvo, meio + 1, fim)   # busca direita
    else:
        return busca_binaria_recursiva(lista_ordenada, alvo, inicio, meio - 1) # busca esquerda


def buscar_planeta(lista_por_nome: list, nome: str) -> dict | None:
    """Wrapper da busca binária. Retorna o dicionário do planeta ou None."""
    idx = busca_binaria_recursiva(lista_por_nome, nome, 0, len(lista_por_nome) - 1)
    return lista_por_nome[idx] if idx != -1 else None


def buscar_parcial(lista_por_nome: list, fragmento: str) -> list:
    """
    Busca linear auxiliar por substring (case-insensitive).
    Útil quando o usuário não lembra o nome exato.
    """
    fragmento_low = fragmento.lower()
    return [p for p in lista_por_nome if fragmento_low in p["pl_name"].lower()]


# ─────────────────────────────────────────────
# 5. EXIBIÇÃO / RELATÓRIOS
# ─────────────────────────────────────────────

LINHA = "─" * 70

def classificar_score(score: float) -> str:
    """Rótulo qualitativo para o ExoScore."""
    if score >= 80:  return "🟢 MUITO ALTO"
    if score >= 60:  return "🔵 ALTO"
    if score >= 40:  return "🟡 MODERADO"
    if score >= 20:  return "🟠 BAIXO"
    return               "🔴 MUITO BAIXO"


def exibir_ficha(planeta: dict) -> None:
    """Exibe a ficha detalhada de um exoplaneta."""
    print(f"\n{LINHA}")
    print(f"  🪐  {planeta['pl_name']}")
    print(LINHA)
    print(f"  ExoScore            : {planeta['exoscore']:6.2f} / 100  {classificar_score(planeta['exoscore'])}")
    print(f"  Raio (R⊕)           : {planeta['pl_rade']:.3f}")
    print(f"  Temp. equilíbrio (K): {planeta['pl_eqt']:.1f}")
    print(f"  Semi-eixo maior (AU): {planeta['pl_orbsmax']:.5f}")
    print(f"  Temp. estelar (K)   : {planeta['st_teff']:.0f}")
    print(f"  Perfil rochoso      : {'✔ Sim' if planeta['pl_rade'] <= 1.6 else '✖ Fora do perfil'}")
    print(LINHA)


def exibir_ranking(planetas: list, top_n: int = 10) -> None:
    """Exibe o ranking dos planetas com maior ExoScore."""
    ordenados = sorted(planetas, key=lambda x: x["exoscore"], reverse=True)
    print(f"\n{'─'*70}")
    print(f"  🏆  TOP {top_n} — RANKING DE HABITABILIDADE (EXOSCORE)")
    print(f"{'─'*70}")
    print(f"  {'#':<4} {'Nome':<26} {'Score':>6}  {'Raio':>6}  {'Temp(K)':>8}  Nível")
    print(f"  {'─'*4} {'─'*26} {'─'*6}  {'─'*6}  {'─'*8}  {'─'*14}")
    for i, p in enumerate(ordenados[:top_n], start=1):
        print(
            f"  {i:<4} {p['pl_name']:<26} {p['exoscore']:>6.2f}  "
            f"{p['pl_rade']:>6.3f}  {p['pl_eqt']:>8.1f}  {classificar_score(p['exoscore'])}"
        )
    print(f"{'─'*70}")


def exibir_todos(planetas: list) -> None:
    """Lista todos os exoplanetas ordenados por nome."""
    print(f"\n{'─'*70}")
    print(f"  📋  TODOS OS EXOPLANETAS ({len(planetas)} registros — ordenados por nome)")
    print(f"{'─'*70}")
    print(f"  {'Nome':<26} {'Score':>6}  {'Raio':>6}  {'Temp(K)':>8}")
    print(f"  {'─'*26} {'─'*6}  {'─'*6}  {'─'*8}")
    for p in planetas:
        print(f"  {p['pl_name']:<26} {p['exoscore']:>6.2f}  {p['pl_rade']:>6.3f}  {p['pl_eqt']:>8.1f}")
    print(f"{'─'*70}")


# ─────────────────────────────────────────────
# 6. MENU INTERATIVO
# ─────────────────────────────────────────────

def menu_buscar(lista_por_nome: list) -> None:
    """Submenu de busca: exata (binária recursiva) ou parcial (linear)."""
    print("\n  Tipo de busca:")
    print("  a) Busca exata por nome  (Busca Binária Recursiva)")
    print("  b) Busca parcial por fragmento  (busca linear auxiliar)")
    tipo = input("  Escolha (a/b): ").strip().lower()

    if tipo == "a":
        nome = input("  Nome exato do exoplaneta: ").strip()
        resultado = buscar_planeta(lista_por_nome, nome)
        if resultado:
            print("\n  ✅ Exoplaneta encontrado via Busca Binária Recursiva!")
            exibir_ficha(resultado)
        else:
            print(f"\n  ❌ '{nome}' não encontrado.")
            print("     Dica: use a busca parcial (opção b) se não souber o nome exato.")

    elif tipo == "b":
        fragmento = input("  Fragmento do nome: ").strip()
        resultados = buscar_parcial(lista_por_nome, fragmento)
        if resultados:
            print(f"\n  🔍 {len(resultados)} resultado(s) encontrado(s):")
            for p in resultados:
                print(f"     • {p['pl_name']}  (ExoScore: {p['exoscore']})")
        else:
            print(f"\n  ❌ Nenhum planeta com '{fragmento}' no nome.")
    else:
        print("  Opção inválida.")


def menu_ranking(planetas: list) -> None:
    """Submenu de ranking com escolha de quantidade."""
    try:
        top_n = int(input("  Quantos planetas exibir no ranking? (padrão: 10): ").strip() or "10")
        top_n = max(1, min(top_n, len(planetas)))
    except ValueError:
        top_n = 10
    exibir_ranking(planetas, top_n)


def exibir_estatisticas(planetas: list) -> None:
    """Exibe estatísticas gerais da base processada."""
    scores = [p["exoscore"] for p in planetas]
    rochosos = [p for p in planetas if p["pl_rade"] <= 1.6]
    print(f"\n{'─'*70}")
    print("  📊  ESTATÍSTICAS DA BASE")
    print(f"{'─'*70}")
    print(f"  Total de exoplanetas    : {len(planetas)}")
    print(f"  Perfil rochoso (≤1.6 R⊕): {len(rochosos)}")
    print(f"  Score médio             : {sum(scores)/len(scores):.2f}")
    print(f"  Score máximo            : {max(scores):.2f}  →  {max(planetas, key=lambda x: x['exoscore'])['pl_name']}")
    print(f"  Score mínimo            : {min(scores):.2f}  →  {min(planetas, key=lambda x: x['exoscore'])['pl_name']}")
    print(f"  Score ≥ 60 (alto)       : {sum(1 for s in scores if s >= 60)}")
    print(f"{'─'*70}")


# ─────────────────────────────────────────────
# 7. PONTO DE ENTRADA
# ─────────────────────────────────────────────

def main() -> None:
    print("\n" + "═" * 70)
    print("   🚀  EXOSCORE — Índice Visual de Habitabilidade Exoplanetária")
    print("   Dynamic Programming · FIAP 2ESPY 2026")
    print("═" * 70)

    # ── Etapa 1: obter dados ──────────────────────────────────────────
    print("\n[1/3] Obtendo dados de exoplanetas...")
    dados_brutos = obter_dados()

    # ── Etapa 2: fila de processamento ───────────────────────────────
    print(f"\n[2/3] Carregando {len(dados_brutos)} exoplanetas na fila de processamento...")
    fila = criar_fila_processamento(dados_brutos)
    print(f"  📋 Fila criada. Itens aguardando processamento: {len(fila)}")

    print("  ⚙️  Processando fila e calculando ExoScores...")
    planetas = processar_fila(fila)
    print(f"  ✅ {len(planetas)} exoplanetas processados com sucesso.")

    # ── Etapa 3: indexar por nome (para busca binária) ────────────────
    print("\n[3/3] Indexando base por nome para busca binária...")
    por_nome = sorted(planetas, key=lambda x: x["pl_name"].lower())
    print("  ✅ Base indexada e pronta.")

    # ── Menu principal ────────────────────────────────────────────────
    opcoes = {
        "1": ("🏆 Ranking de habitabilidade",  lambda: menu_ranking(planetas)),
        "2": ("🔍 Buscar exoplaneta",          lambda: menu_buscar(por_nome)),
        "3": ("📋 Listar todos",               lambda: exibir_todos(por_nome)),
        "4": ("📊 Estatísticas da base",       lambda: exibir_estatisticas(planetas)),
        "5": ("🚪 Sair",                       None),
    }

    while True:
        print("\n" + "═" * 70)
        print("  MENU PRINCIPAL")
        print("═" * 70)
        for k, (desc, _) in opcoes.items():
            print(f"  {k} — {desc}")
        print("═" * 70)

        escolha = input("  Opção: ").strip()

        if escolha not in opcoes:
            print("  ⚠️  Opção inválida.")
            continue

        desc, acao = opcoes[escolha]

        if acao is None:
            print("\n  👋 Encerrando o ExoScore. Até logo!\n")
            break

        acao()


if __name__ == "__main__":
    main()
