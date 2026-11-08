"""Monitor de cargas: as contribuições do último ano no tema "fábrica de dados". Cada dia é uma caixa que acende
conforme o volume do dia; os mostradores trazem o total, a sequência atual, a maior sequência e os repositórios
públicos; a barra de baixo mostra a mistura de linguagens. Um leitor de luz varre as caixas e o dia de hoje pisca.

Roda todo dia pelo GitHub Actions (.github/workflows/monitor-cargas.yml) com o GITHUB_TOKEN.
Uso: python -m pip install fonttools && GITHUB_TOKEN=... python scripts/painel_cargas.py <login> <saida.svg>
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

from gerar_banner_fabrica import COR, TEKTUR, Fonte, Glifos, bloco, n

PLEX = Path(__file__).resolve().parent / "fontes" / "ibmplexsans" / "IBMPlexSans[wdth,wght].ttf"
W, H = 1200, 470
CONSULTA = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      nodes { languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } } }
    }
  }
}"""
NIVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def consultar(login, token):
    corpo = json.dumps({"query": CONSULTA, "variables": {"login": login}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=corpo, method="POST",
                                 headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        dados = json.load(resp)
    if "errors" in dados:
        raise SystemExit(f"GraphQL: {dados['errors']}")
    return dados["data"]["user"]


def sequencias(dias):
    """(sequência atual, maior sequência) em dias seguidos com contribuição; hoje sem atividade ainda não quebra."""
    maior = atual = 0
    for d in dias:
        atual = atual + 1 if d["contributionCount"] else 0
        maior = max(maior, atual)
    atual = 0
    for i, d in enumerate(reversed(dias)):
        if d["contributionCount"]:
            atual += 1
        elif i > 0:
            break
    return atual, maior


def visivel(cor):
    """Clareia cores de linguagem escuras demais para o fundo do painel."""
    r, g, b = (int(cor[i:i + 2], 16) for i in (1, 3, 5))
    if 0.2126 * r + 0.7152 * g + 0.0722 * b >= 90:
        return cor
    r, g, b = (int(c + (255 - c) * 0.5) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def linguagens(repos):
    soma = {}
    for repo in repos:
        for aresta in repo["languages"]["edges"]:
            nome, cor = aresta["node"]["name"], visivel(aresta["node"]["color"] or "#9aa3ae")
            tam, _ = soma.get(nome, (0, cor))
            soma[nome] = (tam + aresta["size"], cor)
    total = sum(t for t, _ in soma.values()) or 1
    lista = sorted(((nome, t / total, c) for nome, (t, c) in soma.items()), key=lambda x: -x[1])
    principais = lista[:5]
    resto = sum(p for _, p, _ in lista[5:])
    if resto > 0.005:
        principais.append(("Outras", resto, "#5b5675"))
    return principais


def gerar(usuario, hoje):
    c = COR
    tk900 = Fonte(TEKTUR, {"wght": 900, "wdth": 100}, "a")
    tk700 = Fonte(TEKTUR, {"wght": 700, "wdth": 85}, "b")
    px = Fonte(PLEX, {"wght": 500, "wdth": 100}, "p")
    g = Glifos("m")
    cal = usuario["contributionsCollection"]["contributionCalendar"]
    semanas = cal["weeks"]
    dias = [d for s in semanas for d in s["contributionDays"]]
    atual, maior = sequencias(dias)

    # cabeçalho
    cab, _ = g.escrever(tk900, tk900.tamanho_para_cap(13), "CONTRIBUIÇÕES · ÚLTIMOS 12 MESES", 64, 50, 2.4)
    data, _ = g.escrever(tk700, tk700.tamanho_para_cap(9.5), f"ATUALIZADO EM {hoje:%d/%m/%Y}", W - 48, 50, 1.6, "end")

    # mostradores
    numeros = [(f'{cal["totalContributions"]:,}'.replace(",", "."), "contribuições no último ano"),
               (str(atual), "dias na sequência atual"), (str(maior), "dias na maior sequência"),
               (str(usuario["repositories"]["totalCount"]), "repositórios públicos")]
    telas = []
    for k, (valor, rotulo) in enumerate(numeros):
        x = 48 + k * 282
        num, _ = g.escrever(tk900, tk900.tamanho_para_cap(28), valor, x + 20, 116, 2)
        rot, _ = g.escrever(px, 12, rotulo, x + 20, 138)
        telas.append(f'<rect x="{x}" y="74" width="258" height="78" rx="9" fill="#070b14" stroke="{c["aco2"]}"/>'
                     f'<rect x="{x}" y="74" width="258" height="1.5" fill="{c["aco3"]}"/>'
                     f'<g fill="{c["dado3"]}" transform="translate(1.5 1.5)">{num}</g><g fill="{c["dado_claro"]}">{num}</g>'
                     f'<g fill="#8fa3c8">{rot}</g>'
                     f'<circle class="led" style="animation-delay:-{k * 0.6:.1f}s" cx="{x + 240}" cy="90" r="3" fill="{c["dado"]}"/>')

    # caixas: uma por dia
    x0, passo_x, y0, passo_y = 66, (W - 132) / max(len(semanas) - 1, 1), 192, 21
    cores = [(c["aco1"], c["aco2"], c["aco0"]), (c["dado3"], c["dado2"], "#08463f"), (c["dado2"], c["dado"], c["dado3"]),
             (c["dado"], c["dado_claro"], c["dado2"]), (c["dado_claro"], "#e3fffa", c["dado"])]
    simbolos = "".join(f'<g id="n{k}">{bloco(*cs, "", w=13, h=13, d=3.5)}</g>' for k, cs in enumerate(cores))
    caixas, rotulos, mes_anterior, hoje_xy = [], [], None, None
    for i, semana in enumerate(semanas):
        primeiro = dt.date.fromisoformat(semana["contributionDays"][0]["date"])
        if primeiro.month != mes_anterior and primeiro.day <= 7:
            r, _ = g.escrever(tk700, tk700.tamanho_para_cap(8.5), MESES[primeiro.month - 1].upper(),
                              x0 + i * passo_x - 6, y0 + 6 * passo_y + 34, 1.2)
            rotulos.append(r)
            mes_anterior = primeiro.month
        for d in semana["contributionDays"]:
            linha = (dt.date.fromisoformat(d["date"]).weekday() + 1) % 7
            x, y = x0 + i * passo_x, y0 + linha * passo_y + 13
            nivel = NIVEL.get(d["contributionLevel"], 0)
            caixas.append(f'<use href="#n{nivel}" x="{n(x)}" y="{n(y)}"/>')
            hoje_xy = (x, y)
    marco = ""
    if hoje_xy:
        hx, hy = hoje_xy
        marco = (f'<rect class="hoje" x="{n(hx - 9.5)}" y="{n(hy - 19)}" width="22" height="22" rx="3" fill="none" '
                 f'stroke="{c["brasa"]}" stroke-width="2"/>')

    # mistura de linguagens
    barra, legenda, x = [], [], 64.0
    largura = W - 128
    for nome, parte, cor in linguagens(usuario["repositories"]["nodes"]):
        w = largura * parte
        barra.append(f'<rect x="{n(x)}" y="398" width="{n(max(w - 2, 1))}" height="10" fill="{cor}"/>')
        x += w
    lx = 64
    for nome, parte, cor in linguagens(usuario["repositories"]["nodes"]):
        texto = f"{nome} {parte * 100:.1f}%".replace(".", ",")
        t, larg = g.escrever(px, 12.5, texto, lx + 16, 440)
        legenda.append(f'<rect x="{lx}" y="430" width="10" height="10" rx="2" fill="{cor}"/><g fill="#cfd8ea">{t}</g>')
        lx += larg + 44

    zona = (x0 - 12, y0 - 6, W - 2 * x0 + 30, 7 * passo_y + 12)
    defs = (simbolos + "".join(g.defs)
            + f'<linearGradient id="painel" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c["aco1"]}"/>'
              f'<stop offset="1" stop-color="{c["parede2"]}"/></linearGradient>'
            + '<pattern id="pontos" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="11" cy="11" r=".9" fill="#2b3b5e"/></pattern>'
            + f'<linearGradient id="luz" x1="0" x2="1"><stop offset="0" stop-color="{c["dado"]}" stop-opacity="0"/>'
              f'<stop offset=".5" stop-color="{c["dado_claro"]}" stop-opacity=".3"/><stop offset="1" stop-color="{c["dado"]}" stop-opacity="0"/></linearGradient>'
            + f'<clipPath id="moldura"><rect width="{W}" height="{H}" rx="18"/></clipPath>'
            + f'<clipPath id="zona"><rect x="{n(zona[0])}" y="{n(zona[1])}" width="{n(zona[2])}" height="{n(zona[3])}"/></clipPath>'
            + f'<clipPath id="arred"><rect x="64" y="398" width="{W - 128}" height="10" rx="5"/></clipPath>')
    css = ("@keyframes led{0%,100%{opacity:1}50%{opacity:.2}}.led{animation:led 2.4s ease-in-out infinite}"
           "@keyframes hoje{0%,100%{opacity:1}50%{opacity:.25}}.hoje{animation:hoje 1.6s ease-in-out infinite}"
           f"@keyframes scan{{0%{{transform:translateX(0)}}70%,100%{{transform:translateX({n(zona[2] + 120)}px)}}}}"
           ".scan{animation:scan 7s ease-in-out infinite}")
    titulo = (f'Monitor de cargas: {cal["totalContributions"]} contribuições no último ano, sequência atual de {atual} dias, '
              f'maior sequência de {maior} dias, {usuario["repositories"]["totalCount"]} repositórios públicos')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-labelledby="t"><title id="t">{titulo}</title><defs>{defs}</defs><style>{css}</style>'
            f'<g clip-path="url(#moldura)"><rect width="{W}" height="{H}" fill="url(#painel)"/>'
            f'<rect width="{W}" height="{H}" fill="url(#pontos)" opacity=".5"/>'
            f'<rect x="48" y="36" width="5" height="16" fill="{c["brasa"]}"/>'
            f'<g fill="{c["texto"]}">{cab}</g><g fill="#8fa3c8">{data}</g>'
            f'<rect x="48" y="60" width="{W - 96}" height="1" fill="{c["aco2"]}"/>'
            + "".join(telas)
            + f'<rect x="{n(zona[0])}" y="{n(zona[1])}" width="{n(zona[2])}" height="{n(zona[3])}" rx="8" fill="#070b14" opacity=".55"/>'
            + "".join(caixas) + marco
            + f'<g clip-path="url(#zona)"><g class="scan"><rect x="{n(zona[0] - 110)}" y="{n(zona[1])}" width="90" '
              f'height="{n(zona[3])}" fill="url(#luz)"/></g></g>'
            + f'<g fill="#7d8db0">{"".join(rotulos)}</g>'
            + f'<g clip-path="url(#arred)">{"".join(barra)}</g>' + "".join(legenda)
            + f'</g><rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="17.5" fill="none" stroke="{c["aco2"]}"/></svg>\n')


def main():
    login, saida = sys.argv[1], sys.argv[2]
    svg = gerar(consultar(login, os.environ["GITHUB_TOKEN"]), dt.date.today())
    Path(saida).write_text(svg, encoding="utf-8")
    print(f"{saida}: {len(svg.encode()) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
