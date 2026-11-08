"""Gera os cartões dos projetos (assets/cards/*.svg) no mesmo céu do banner.

Uso: python scripts/gerar_cards.py
"""
import html
import random
from pathlib import Path

PASTA = Path(__file__).resolve().parents[1] / "assets" / "cards"
W, H = 420, 196
SANS = "'Segoe UI',Inter,'Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono','Fira Code',Consolas,'Courier New',monospace"

PROJETOS = [
    ("dw-tempo-real", "DW em tempo real", "01",
     ["Espelho incremental ERP → DW de minuto", "em minuto, por impressão digital de linha", "e com travas contra carga ruim."],
     ["Python", "SQL Server", "ETL"]),
    ("conferencia-nfse", "Conferência de NFS-e", "02",
     ["Confere nota × lançamento e retenções", "(ISS, INSS, IRRF, PIS/COFINS/CSLL) e", "devolve um parecer em PDF."],
     ["Python", "Regras fiscais", "PDF"]),
    ("robo-portal-web", "Robô de portal web", "03",
     ["RPA com Playwright: fila, novas tentativas,", "evidência em print e CPF mascarado no", "log. Testes sem abrir navegador."],
     ["Playwright", "RPA", "SQLite"]),
    ("robo-erp-desktop", "Robô de ERP desktop", "04",
     ["UI Automation no Windows: acha o campo", "pelo nome e lança títulos de uma", "planilha, até com a janela minimizada."],
     ["pywinauto", "WinForms", "RPA"]),
    ("relatorios-automaticos", "Relatórios automáticos", "05",
     ["Do banco para um e-mail pronto para agir,", "com a planilha em anexo e agendamento", "oculto no Windows."],
     ["Python", "Excel", "Agendador"]),
    ("EdyVerder", "Este perfil", "06",
     ["Banner em constelação e mapa estelar", "de contribuições, gerados por código e", "atualizados pelo GitHub Actions."],
     ["SVG", "GitHub Actions", "Python"]),
]


def estrelas(semente):
    rnd = random.Random(semente)
    return "".join(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(0, H):.0f}" r="{rnd.choice([.5, .7, .9])}" '
                   f'fill="#fff" opacity="{rnd.uniform(.15, .55):.2f}"/>' for _ in range(34))


def cartao(repo, titulo, numero, linhas, tags):
    e = html.escape
    texto = "".join(f'<text x="26" y="{96 + i * 19}" class="desc">{e(l)}</text>' for i, l in enumerate(linhas))
    x, pilulas = 26, []
    for t in tags:
        w = 16 + len(t) * 7.2
        pilulas.append(f'<rect x="{x}" y="160" width="{w:.0f}" height="20" rx="10" fill="#21184a" stroke="#3a2d70"/>'
                       f'<text x="{x + w / 2:.0f}" y="174" class="tag" text-anchor="middle">{e(t)}</text>')
        x += w + 8
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{e(titulo)}">
  <defs>
    <linearGradient id="f" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#150d34"/><stop offset="1" stop-color="#08070f"/></linearGradient>
    <radialGradient id="n" cx="85%" cy="15%" r="60%"><stop offset="0" stop-color="#7c3aed" stop-opacity=".35"/><stop offset="1" stop-color="#7c3aed" stop-opacity="0"/></radialGradient>
    <linearGradient id="l" x1="0" x2="1"><stop offset="0" stop-color="#ff8a5b"/><stop offset="1" stop-color="#ff8a5b" stop-opacity="0"/></linearGradient>
  </defs>
  <style>
    .tit{{font:700 19px {SANS};fill:#fff}}
    .num{{font:600 11px {MONO};letter-spacing:3px;fill:#ff8a5b}}
    .desc{{font:400 13px {SANS};fill:#cfc8f0}}
    .tag{{font:600 11px {SANS};fill:#ffc6ad}}
    .orb{{transform-origin:368px 46px;animation:o 9s linear infinite}}
    @keyframes o{{to{{transform:rotate(360deg)}}}}
  </style>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="url(#f)" stroke="#2a2346"/>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="url(#n)"/>
  {estrelas(repo)}
  <circle cx="368" cy="46" r="16" fill="none" stroke="#3a2d70" stroke-dasharray="2 4"/>
  <circle cx="368" cy="46" r="4" fill="#ffd2bd"/>
  <g class="orb"><circle cx="384" cy="46" r="2.6" fill="#ff8a5b"/></g>
  <text x="26" y="36" class="num">{numero} · REPOSITÓRIO</text>
  <text x="26" y="64" class="tit">{e(titulo)}</text>
  <rect x="26" y="74" width="64" height="2" fill="url(#l)"/>
  {texto}
  {"".join(pilulas)}
</svg>
'''


def main():
    PASTA.mkdir(parents=True, exist_ok=True)
    for repo, titulo, numero, linhas, tags in PROJETOS:
        (PASTA / f"{repo}.svg").write_text(cartao(repo, titulo, numero, linhas, tags), encoding="utf-8")
    print(f"{len(PROJETOS)} cartões em {PASTA}")


if __name__ == "__main__":
    main()
