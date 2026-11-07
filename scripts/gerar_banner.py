"""Gera assets/banner.svg: o nome ROCHA desenhado como constelação sobre uma nebulosa animada.

Tudo é SVG puro (sem fonte nem imagem externa), então o GitHub renderiza a animação direto no README.
Uso: python scripts/gerar_banner.py
"""
import math
import random
from pathlib import Path

W, H = 1200, 400
SAIDA = Path(__file__).resolve().parents[1] / "assets" / "banner.svg"
rnd = random.Random(2005)

# letras em uma caixa 100 x 150: cada traço é uma lista de vértices
LETRAS = {
    "R": [[(0, 150), (0, 0), (68, 0), (100, 34), (68, 74), (0, 74)], [(52, 74), (100, 150)]],
    "O": [[(32, 0), (68, 0), (100, 42), (100, 108), (68, 150), (32, 150), (0, 108), (0, 42), (32, 0)]],
    "C": [[(100, 26), (68, 0), (32, 0), (0, 42), (0, 108), (32, 150), (68, 150), (100, 124)]],
    "H": [[(0, 0), (0, 150)], [(100, 0), (100, 150)], [(0, 76), (100, 76)]],
    "A": [[(0, 150), (50, 0), (100, 150)], [(24, 92), (76, 92)]],
}
NOME, ESCALA, ESPACO, TOPO = "ROCHA", 0.86, 62, 82


def estrelas_de_fundo():
    partes = []
    for i in range(240):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        r = rnd.choice([0.5, 0.6, 0.7, 0.8, 1.0, 1.2, 1.5])
        cor = rnd.choice(["#ffffff", "#ffffff", "#dfe6ff", "#ffe2d1", "#c9b8ff"])
        op = rnd.uniform(0.35, 0.95)
        if rnd.random() < 0.4:
            dur, atraso = rnd.uniform(2.2, 6.5), rnd.uniform(0, 6)
            partes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{cor}" opacity="{op:.2f}" class="pisca" '
                          f'style="animation-duration:{dur:.1f}s;animation-delay:-{atraso:.1f}s"/>')
        else:
            partes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{cor}" opacity="{op:.2f}"/>')
    return "\n    ".join(partes)


def galaxia_espiral(cx, cy):
    """Galáxia pequena no canto, girando devagar: pontos ao longo de dois braços em espiral logarítmica."""
    pontos = []
    for braco in range(2):
        for k in range(110):
            t = k / 110 * 3.4 * math.pi
            raio = 4 + 6.2 * math.exp(0.21 * t)
            ang = t + braco * math.pi
            x = cx + raio * math.cos(ang) + rnd.gauss(0, 1.6)
            y = cy + raio * math.sin(ang) * 0.55 + rnd.gauss(0, 1.0)
            op = max(0.15, 0.9 - k / 140)
            cor = "#ffd7c2" if k < 25 else "#cdbdff"
            pontos.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rnd.choice([0.6, 0.8, 1.1])}" fill="{cor}" '
                          f'opacity="{op:.2f}"/>')
    nucleo = (f'<circle cx="{cx}" cy="{cy}" r="16" fill="url(#nucleo)"/>'
              f'<circle cx="{cx}" cy="{cy}" r="2.2" fill="#fff"/>')
    return (f'<g class="gira" style="transform-origin:{cx}px {cy}px">' + "".join(pontos) + nucleo + "</g>")


def constelacao():
    largura = len(NOME) * 100 * ESCALA + (len(NOME) - 1) * ESPACO
    x0 = (W - largura) / 2
    tracos, vertices, ordem = [], {}, 0
    for i, letra in enumerate(NOME):
        ox = x0 + i * (100 * ESCALA + ESPACO)
        for traco in LETRAS[letra]:
            pts = [(ox + px * ESCALA, TOPO + py * ESCALA) for px, py in traco]
            for a, b in zip(pts, pts[1:]):
                tracos.append(f'<path d="M{a[0]:.1f} {a[1]:.1f} L{b[0]:.1f} {b[1]:.1f}" pathLength="1" class="linha" '
                              f'style="animation-delay:{0.25 + ordem * 0.07:.2f}s"/>')
                ordem += 1
            for p in pts:
                vertices[(round(p[0], 1), round(p[1], 1))] = True
    estrelas = []
    for j, (x, y) in enumerate(vertices):
        brilho = rnd.choice([2.6, 3.0, 3.4, 3.8])
        estrelas.append(
            f'<g class="astro" style="animation-delay:{0.2 + j * 0.05:.2f}s">'
            f'<circle cx="{x}" cy="{y}" r="{brilho * 3.2:.1f}" fill="url(#halo)"/>'
            f'<circle cx="{x}" cy="{y}" r="{brilho:.1f}" fill="#fff" class="pulsa" '
            f'style="animation-delay:-{rnd.uniform(0, 4):.1f}s"/></g>')
    return "\n    ".join(tracos), "\n    ".join(estrelas)


def estrela_cadente(x, y, dx, dy, dur, atraso):
    return (f'<g class="cadente" style="--dx:{dx}px;--dy:{dy}px;animation-duration:{dur}s;animation-delay:{atraso}s">'
            f'<line x1="{x}" y1="{y}" x2="{x - 90}" y2="{y - 32}" stroke="url(#rastro)" stroke-width="1.6" '
            f'stroke-linecap="round"/><circle cx="{x}" cy="{y}" r="1.6" fill="#fff"/></g>')


def main():
    linhas, astros = constelacao()
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img"
     aria-labelledby="titulo desc">
  <title id="titulo">Rocha</title>
  <desc id="desc">O nome ROCHA desenhado como uma constelação sobre uma nebulosa, com estrelas piscando, uma galáxia
  espiral girando e estrelas cadentes. Engenharia de dados, automação e ETL.</desc>
  <defs>
    <radialGradient id="ceu" cx="50%" cy="45%" r="75%">
      <stop offset="0" stop-color="#140c33"/><stop offset=".55" stop-color="#080716"/>
      <stop offset="1" stop-color="#030308"/>
    </radialGradient>
    <radialGradient id="halo"><stop offset="0" stop-color="#ffd2bd" stop-opacity=".75"/>
      <stop offset=".35" stop-color="#ff8a5b" stop-opacity=".25"/><stop offset="1" stop-color="#ff8a5b" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="nucleo"><stop offset="0" stop-color="#fff2e8"/>
      <stop offset=".4" stop-color="#ffb08a" stop-opacity=".55"/><stop offset="1" stop-color="#ffb08a" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="rastro" x1="1" y1="1" x2="0" y2="0">
      <stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="borda" x1="0" x2="1">
      <stop offset="0" stop-color="#7c3aed" stop-opacity="0"/><stop offset=".5" stop-color="#ff8a5b"/>
      <stop offset="1" stop-color="#7c3aed" stop-opacity="0"/>
    </linearGradient>
    <filter id="nevoa" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="46"/></filter>
    <clipPath id="quadro"><rect width="{W}" height="{H}" rx="18"/></clipPath>
  </defs>
  <style>
    .pisca{{animation:pisca ease-in-out infinite alternate}}
    @keyframes pisca{{from{{opacity:.15}}to{{opacity:1}}}}
    .nuvem{{animation:deriva 22s ease-in-out infinite alternate}}
    .nuvem.b{{animation-duration:30s;animation-direction:alternate-reverse}}
    @keyframes deriva{{from{{transform:translate(-30px,-8px) scale(1)}}to{{transform:translate(34px,10px) scale(1.08)}}}}
    .gira{{animation:gira 140s linear infinite}}
    @keyframes gira{{to{{transform:rotate(-360deg)}}}}
    .linha{{fill:none;stroke:#d9d2ff;stroke-opacity:.72;stroke-width:1.7;stroke-linecap:round;
      stroke-dasharray:1;stroke-dashoffset:1;animation:traca .55s ease-out forwards}}
    @keyframes traca{{to{{stroke-dashoffset:0}}}}
    .astro{{opacity:0;animation:acende .6s ease-out forwards}}
    @keyframes acende{{from{{opacity:0;transform:scale(.4)}}to{{opacity:1;transform:scale(1)}}}}
    .astro{{transform-box:fill-box;transform-origin:center}}
    .pulsa{{animation:pulsa 3.8s ease-in-out infinite}}
    @keyframes pulsa{{0%,100%{{opacity:1}}50%{{opacity:.55}}}}
    .cadente{{opacity:0;animation-name:cai;animation-iteration-count:infinite;animation-timing-function:ease-in}}
    @keyframes cai{{0%{{opacity:0;transform:translate(0,0)}}4%{{opacity:1}}
      14%{{opacity:0;transform:translate(var(--dx),var(--dy))}}100%{{opacity:0;transform:translate(var(--dx),var(--dy))}}}}
    .sub{{font:600 15px 'JetBrains Mono','Fira Code',Consolas,'Courier New',monospace;letter-spacing:6px;fill:#e9e4ff}}
    .coord{{font:500 11px 'JetBrains Mono','Fira Code',Consolas,'Courier New',monospace;letter-spacing:2.5px;fill:#a99ed6}}
    .surge{{opacity:0;animation:surge 1.2s ease-out 2.6s forwards}}
    @keyframes surge{{to{{opacity:1}}}}
  </style>
  <g clip-path="url(#quadro)">
    <rect width="{W}" height="{H}" fill="url(#ceu)"/>
    <g filter="url(#nevoa)">
      <ellipse class="nuvem" cx="260" cy="130" rx="300" ry="120" fill="#6d28d9" opacity=".42"/>
      <ellipse class="nuvem b" cx="930" cy="300" rx="280" ry="110" fill="#be185d" opacity=".24"/>
      <ellipse class="nuvem" cx="610" cy="185" rx="250" ry="85" fill="#ff8a5b" opacity=".2"/>
      <ellipse class="nuvem b" cx="1080" cy="80" rx="200" ry="90" fill="#1d4ed8" opacity=".3"/>
    </g>
    {estrelas_de_fundo()}
    {galaxia_espiral(1072, 300)}
    {estrela_cadente(380, 40, 520, 190, 9, 1.5)}
    {estrela_cadente(1000, 30, 380, 140, 13, 6)}
    {linhas}
    {astros}
    <text class="sub surge" x="{W / 2}" y="{TOPO + 150 * ESCALA + 62}" text-anchor="middle">ENGENHARIA DE DADOS  ·  AUTOMAÇÃO  ·  ETL</text>
    <text class="coord surge" x="28" y="{H - 24}">10°56′S  37°04′W  ·  ARACAJU, BR</text>
    <text class="coord surge" x="{W - 28}" y="{H - 24}" text-anchor="end">CONSTELAÇÃO ROCHA</text>
    <rect x="0" y="{H - 2}" width="{W}" height="2" fill="url(#borda)" opacity=".8"/>
  </g>
</svg>
'''
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(svg, encoding="utf-8")
    print(f"{SAIDA} ({len(svg.encode()) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
