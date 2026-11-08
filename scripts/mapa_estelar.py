"""Gera o mapa estelar de contribuições: cada dia do último ano vira uma estrela, mais brilhante quanto mais
contribuições teve; dias seguidos com atividade se ligam como constelações.

Roda todo dia pelo GitHub Actions (.github/workflows/mapa-estelar.yml) usando o GITHUB_TOKEN; só biblioteca padrão.
Uso: GITHUB_TOKEN=... python scripts/mapa_estelar.py <login> <saida.svg>
"""
import datetime as dt
import hashlib
import json
import os
import sys
import urllib.request

W, H = 1200, 440
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
SANS = "'Segoe UI',Inter,'Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono','Fira Code',Consolas,'Courier New',monospace"


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


def sorteio(chave):
    """Número entre 0 e 1 fixo para cada chave (o céu não muda de lugar a cada atualização)."""
    return int(hashlib.md5(chave.encode()).hexdigest()[:6], 16) / 0xFFFFFF


def tremor(data, eixo):
    return sorteio(f"{data}{eixo}") * 14 - 7


def ceu_de_fundo():
    """Nebulosa e estrelas de fundo: o mapa parece céu mesmo num ano com poucas contribuições."""
    nuvens = ('<g filter="url(#nevoa)" opacity=".9">'
              '<ellipse cx="230" cy="250" rx="260" ry="90" fill="#6d28d9" opacity=".30"/>'
              '<ellipse cx="640" cy="230" rx="300" ry="70" fill="#ff8a5b" opacity=".10"/>'
              '<ellipse cx="1000" cy="280" rx="240" ry="95" fill="#be185d" opacity=".18"/>'
              '<ellipse cx="1060" cy="120" rx="180" ry="70" fill="#1d4ed8" opacity=".22"/></g>')
    pontos = []
    for i in range(170):
        x, y = 20 + sorteio(f"fx{i}") * (W - 40), 20 + sorteio(f"fy{i}") * (H - 30)
        r = 0.4 + sorteio(f"fr{i}") * 0.8
        op = 0.12 + sorteio(f"fo{i}") * 0.38
        cor = "#ffffff" if sorteio(f"fc{i}") < 0.7 else "#c9b8ff"
        pisca = ' class="brilho" style="animation-delay:-%.1fs"' % (sorteio(f"fd{i}") * 5) if i % 4 == 0 else ""
        pontos.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{cor}" opacity="{op:.2f}"{pisca}/>')
    return nuvens + "".join(pontos)


def visivel(cor):
    """Clareia cores de linguagem escuras demais para o fundo do céu."""
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
    lista = sorted(((n, t / total, c) for n, (t, c) in soma.items()), key=lambda x: -x[1])
    principais = lista[:5]
    resto = sum(p for _, p, _ in lista[5:])
    if resto > 0.005:
        principais.append(("Outras", resto, "#5b5675"))
    return principais


def gerar(usuario, hoje):
    cal = usuario["contributionsCollection"]["contributionCalendar"]
    semanas = cal["weeks"]
    dias = [d for s in semanas for d in s["contributionDays"]]
    atual, maior = sequencias(dias)
    x0, passo_x, y0, passo_y = 64, (W - 128) / max(len(semanas) - 1, 1), 150, 27

    pos, estrelas, linhas, rotulos = {}, [], [], []
    mes_anterior = None
    for i, semana in enumerate(semanas):
        primeiro = dt.date.fromisoformat(semana["contributionDays"][0]["date"])
        if primeiro.month != mes_anterior and primeiro.day <= 7:
            rotulos.append(f'<text x="{x0 + i * passo_x:.1f}" y="{y0 + 6 * passo_y + 38}" class="mes">'
                           f'{MESES[primeiro.month - 1]}</text>')
            mes_anterior = primeiro.month
        for d in semana["contributionDays"]:
            dia = dt.date.fromisoformat(d["date"])
            linha = (dia.weekday() + 1) % 7
            x = x0 + i * passo_x + tremor(d["date"], "x")
            y = y0 + linha * passo_y + tremor(d["date"], "y")
            pos[d["date"]] = (x, y)
            nivel = NIVEL.get(d["contributionLevel"], 0)
            if nivel == 0:
                r0 = 0.6 + sorteio(d["date"] + "r") * 0.6
                op0 = 0.16 + sorteio(d["date"] + "o") * 0.22
                estrelas.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r0:.2f}" fill="#a49bd0" opacity="{op0:.2f}"/>')
                continue
            raio = [0, 1.7, 2.3, 3.0, 3.7][nivel]
            cor = ["", "#cfd8ff", "#e6dcff", "#ffd2bd", "#ff9e72"][nivel]
            atraso = int(hashlib.md5(d["date"].encode()).hexdigest()[:2], 16) / 255 * 4
            estrelas.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{raio * 3.4:.1f}" fill="url(#halo{nivel})"/>'
                            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{raio}" fill="{cor}" class="pisca" '
                            f'style="animation-delay:-{atraso:.1f}s"><title>{dia:%d/%m/%Y}: '
                            f'{d["contributionCount"]} contribuições</title></circle>')

    for a, b in zip(dias, dias[1:]):
        if a["contributionCount"] and b["contributionCount"]:
            (xa, ya), (xb, yb) = pos[a["date"]], pos[b["date"]]
            if abs(xa - xb) + abs(ya - yb) < 90:
                linhas.append(f'<line x1="{xa:.1f}" y1="{ya:.1f}" x2="{xb:.1f}" y2="{yb:.1f}" class="liga"/>')

    marco = ""
    if dias:
        xh, yh = pos[dias[-1]["date"]]
        marco = (f'<circle cx="{xh:.1f}" cy="{yh:.1f}" r="7" class="radar"/>'
                 f'<circle cx="{xh:.1f}" cy="{yh:.1f}" r="7" class="radar b"/>')

    numeros = [(f'{cal["totalContributions"]:,}'.replace(",", "."), "contribuições no último ano"),
               (f"{atual}", "dias na sequência atual"), (f"{maior}", "dias na maior sequência"),
               (f'{usuario["repositories"]["totalCount"]}', "repositórios públicos")]
    blocos = []
    for k, (valor, rotulo) in enumerate(numeros):
        x = 64 + k * 280
        blocos.append(f'<text x="{x}" y="104" class="num">{valor}</text><text x="{x}" y="124" class="rot">{rotulo}</text>')

    barra, legenda, x = [], [], 64.0
    largura = W - 128
    langs = linguagens(usuario["repositories"]["nodes"])
    for nome, parte, cor in langs:
        w = largura * parte
        barra.append(f'<rect x="{x:.1f}" y="398" width="{max(w - 2, 1):.1f}" height="6" fill="{cor}"/>')
        x += w
    lx = 64
    for nome, parte, cor in langs:
        legenda.append(f'<circle cx="{lx + 4}" cy="422" r="4" fill="{cor}"/>'
                       f'<text x="{lx + 14}" y="426" class="lang">{nome} {parte * 100:.1f}%</text>')
        lx += 30 + len(nome) * 8 + 46

    halos = "".join(
        f'<radialGradient id="halo{n}"><stop offset="0" stop-color="{c}" stop-opacity=".55"/>'
        f'<stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>'
        for n, c in [(1, "#9fb2ff"), (2, "#c4b0ff"), (3, "#ffb08a"), (4, "#ff7a45")])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H + 16}" width="{W}" height="{H + 16}" role="img"
     aria-label="Mapa estelar de contribuições: {cal["totalContributions"]} no último ano, sequência atual de {atual} dias, maior sequência de {maior} dias">
  <defs>
    <radialGradient id="ceu" cx="50%" cy="40%" r="80%"><stop offset="0" stop-color="#120b2c"/>
      <stop offset="1" stop-color="#05050d"/></radialGradient>
    <linearGradient id="borda" x1="0" x2="1"><stop offset="0" stop-color="#7c3aed" stop-opacity=".1"/>
      <stop offset=".5" stop-color="#ff8a5b" stop-opacity=".7"/><stop offset="1" stop-color="#7c3aed" stop-opacity=".1"/>
    </linearGradient>
    <clipPath id="arred"><rect x="64" y="398" width="{W - 128}" height="6" rx="3"/></clipPath>
    <clipPath id="cartao"><rect x="1" y="1" width="{W - 2}" height="{H + 14}" rx="18"/></clipPath>
    <filter id="nevoa" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="42"/></filter>
    {halos}
  </defs>
  <style>
    .tit{{font:600 13px {MONO};letter-spacing:5px;fill:#e9e4ff}}
    .data{{font:500 11px {MONO};letter-spacing:1.5px;fill:#8f86b8}}
    .num{{font:700 30px {SANS};fill:#ffffff}}
    .rot{{font:500 12px {SANS};letter-spacing:.6px;fill:#a99ed6}}
    .mes{{font:500 11px {MONO};fill:#7e76a6}}
    .lang{{font:500 12px {SANS};fill:#cfc8f0}}
    .liga{{stroke:#d9d2ff;stroke-opacity:.38;stroke-width:1}}
    .pisca{{animation:pisca 3.6s ease-in-out infinite alternate}}
    @keyframes pisca{{from{{opacity:.55}}to{{opacity:1}}}}
    .radar{{fill:none;stroke:#ff8a5b;stroke-width:1.4;transform-box:fill-box;transform-origin:center;
      animation:radar 2.6s ease-out infinite}}
    .radar.b{{animation-delay:1.3s}}
    @keyframes radar{{from{{opacity:.9;transform:scale(.5)}}to{{opacity:0;transform:scale(2.6)}}}}
    .brilho{{animation:brilho 4.5s ease-in-out infinite alternate}}
    @keyframes brilho{{from{{opacity:.08}}to{{opacity:.6}}}}
  </style>
  <rect x=".5" y=".5" width="{W - 1}" height="{H + 15}" rx="18" fill="url(#ceu)"/>
  <g clip-path="url(#cartao)">{ceu_de_fundo()}</g>
  <rect x=".5" y=".5" width="{W - 1}" height="{H + 15}" rx="18" fill="none" stroke="#2a2346"/>
  <text x="64" y="52" class="tit">MAPA ESTELAR DE CONTRIBUIÇÕES</text>
  <text x="{W - 64}" y="52" class="data" text-anchor="end">atualizado em {hoje:%d/%m/%Y}</text>
  <rect x="64" y="66" width="{W - 128}" height="1" fill="url(#borda)"/>
  {"".join(blocos)}
  {"".join(linhas)}
  {"".join(estrelas)}
  {marco}
  {"".join(rotulos)}
  <g clip-path="url(#arred)">{"".join(barra)}</g>
  {"".join(legenda)}
</svg>
'''


def main():
    login, saida = sys.argv[1], sys.argv[2]
    usuario = consultar(login, os.environ["GITHUB_TOKEN"])
    svg = gerar(usuario, dt.date.today())
    with open(saida, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"{saida}: {len(svg.encode()) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
