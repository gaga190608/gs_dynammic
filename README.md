# 🚀 ExoScore — Índice de Habitabilidade Exoplanetária
### Dynamic Programming · FIAP 2ESPY 2026

---

## 👥 Integrantes

| Nome | RM |
|---|---|
| Jéssica Domingues | 562973 |
| Kauã | 566371 |
| João Vitor Piccolo | 565127 |
| Leonardo Lopes | 561349 |
| Gabrielle Calazans | 564460 |

---

## 📌 Problema Escolhido

A confirmação de exoplanetas cresce em ritmo acelerado — já são mais de 6.000 catalogados pela NASA — mas classificar quais desses mundos têm real potencial de habitabilidade ainda é uma tarefa dispersa e técnica. Pesquisadores precisam analisar manualmente tabelas extensas com dezenas de variáveis para identificar candidatos promissores, o que torna o processo lento e pouco acessível para não-especialistas.

**Problema central:** dificuldade em triar, classificar e comparar a habitabilidade de exoplanetas de forma rápida, padronizada e visual.

---

## 💡 Solução Proposta

O sistema ExoScore calcula um **índice estatístico de habitabilidade (0 a 100)** para cada exoplaneta a partir de três parâmetros astrofísicos:

| Parâmetro | Peso | Critério |
|---|---|---|
| Temperatura de equilíbrio (K) | 40% | Faixa ideal: 273–323 K (água líquida possível) |
| Raio planetário (R⊕) | 35% | Perfil rochoso: 0.5–1.6 R⊕, ideal próximo de 1.0 |
| Posição na zona habitável estelar | 25% | Calculada via luminosidade relativa ao Sol |

O sistema processa os dados em uma **fila (Queue)**, calcula os scores e permite busca por nome usando **busca binária recursiva**.

---

## 🏗️ Arquitetura e Lógica de Resolução

```
┌─────────────────────────────────────────────────────────┐
│  1. DADOS       → NASA API (primário) ou JSON (fallback)│
│                   40 exoplanetas reais catalogados       │
│                                                          │
│  2. FILA        → deque (collections)                    │
│                   Pipeline FIFO de triagem               │
│                   cada planeta aguarda processamento      │
│                                                          │
│  3. SCORE       → calcular_exoscore()                    │
│                   Composição ponderada de 3 fatores       │
│                                                          │
│  4. BUSCA       → busca_binaria_recursiva()              │
│                   Lista ordenada por nome + recursão      │
│                                                          │
│  5. MENU        → Interface interativa no terminal        │
└─────────────────────────────────────────────────────────┘
```

### Por que Fila (Queue)?

A fila representa o **pipeline de triagem**: exoplanetas entram na ordem em que foram importados e são processados um a um (FIFO — primeiro a entrar, primeiro a sair), simulando um sistema real de análise sequencial de candidatos. Após sair da fila, cada planeta recebe seu ExoScore e é armazenado em memória para consulta.

### Por que Busca Binária Recursiva?

Com a base ordenada por nome, a busca binária encontra qualquer exoplaneta em **O(log n)** comparações — muito mais eficiente que a busca linear O(n). A recursividade foi aplicada diretamente no algoritmo: a cada chamada, o intervalo de busca é dividido ao meio, e a função se chama novamente no subarray correspondente. O caso base é quando o intervalo se esgota (não encontrado) ou o elemento é localizado no meio.

---

## 📂 Estrutura do Repositório

```
exoscore-python/
│
├── main.py            # Sistema principal — toda a lógica
├── exoplanetas.json   # Base de dados: 40 exoplanetas reais (NASA Archive)
└── README.md          # Documentação
```

---

## ▶️ Como Executar

### Pré-requisitos

- Python 3.10 ou superior
- Biblioteca `requests` (para tentativa de conexão com a API da NASA)

### Instalação

```bash
# Clone o repositório
git clone https://github.com/gaga190608/gs_dynammic
cd gs_dynammic

# Instale a dependência
pip install requests
```

### Execução

```bash
python main.py
```

> **Nota:** O sistema tentará conectar à API pública da NASA Exoplanet Archive. Caso não haja conexão, o arquivo `exoplanetas.json` é carregado automaticamente como fallback — o sistema funciona completamente offline.

---

## 🖥️ Funcionalidades do Menu

```
1 — 🏆 Ranking de habitabilidade    → top N exoplanetas por ExoScore
2 — 🔍 Buscar exoplaneta            → busca binária (exata) ou parcial
3 — 📋 Listar todos                 → tabela completa ordenada por nome
4 — 📊 Estatísticas da base         → média, máximo, mínimo, contagens
5 — 🚪 Sair
```

---

## 🧪 Demonstração dos Requisitos Técnicos

| Requisito | Implementação |
|---|---|
| ≥ 30 registros | 40 exoplanetas no JSON + API como fonte primária |
| Fila (Queue) | `collections.deque` em `criar_fila_processamento()` / `processar_fila()` |
| Busca Binária | `busca_binaria_recursiva()` — lista ordenada por `pl_name` |
| Recursividade | A busca binária **chama a si mesma** com subintervalos reduzidos |
| Modularidade | 100% encapsulado em funções `def`; zero código solto fora de funções |
| Fonte externa | NASA Exoplanet Archive TAP API ou arquivo `.json` |

---

## 📊 Exemplo de Saída

```
══════════════════════════════════════════════════════════════════════
  🚀  EXOSCORE — Índice Visual de Habitabilidade Exoplanetária
══════════════════════════════════════════════════════════════════════

[1/3] Obtendo dados de exoplanetas...
  ✅ 40 registros carregados de 'exoplanetas.json'.

[2/3] Carregando 40 exoplanetas na fila de processamento...
  📋 Fila criada. Itens aguardando processamento: 40
  ⚙️  Processando fila e calculando ExoScores...
  ✅ 40 exoplanetas processados com sucesso.

─────────────────────────────────────────────────────────────────────
  🏆  TOP 10 — RANKING DE HABITABILIDADE (EXOSCORE)
─────────────────────────────────────────────────────────────────────
  #    Nome                       Score    Raio   Temp(K)  Nível
  ──── ────────────────────────── ──────  ──────  ────────  ──────────────
  1    TOI-700 d                   83.23   1.140     269.0  🟢 MUITO ALTO
  2    TOI-700 e                   82.66   0.950     296.0  🟢 MUITO ALTO
  3    Kepler-62 f                 81.68   1.410     208.0  🟢 MUITO ALTO
  4    Kepler-442 b                80.69   1.340     233.0  🟢 MUITO ALTO
  5    Kepler-186 f                79.63   1.170     188.0  🔵 ALTO
  ...
```

---

## 🔗 Fontes

- NASA Exoplanet Archive: [exoplanetarchive.ipac.caltech.edu](https://exoplanetarchive.ipac.caltech.edu)
- Planetary Habitability Laboratory — Habitable Worlds Catalog: [phl.upr.edu/hwc](https://phl.upr.edu/hwc)
