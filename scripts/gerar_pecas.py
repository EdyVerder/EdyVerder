"""Gera as peças do perfil no tema "fábrica de dados", com as mesmas cores, fontes e desenhos do banner:
selos (assets/selos), títulos das seções (assets/titulos), cartões dos projetos (assets/cards) e a stack
montada como prateleiras de um armazém (assets/stack.svg).

Fontes: Tektur e IBM Plex Sans, licença OFL (scripts/fontes). O texto vira contorno, então nada depende de
fonte instalada. Uso: python -m pip install fonttools && python scripts/gerar_pecas.py
"""
import html
from pathlib import Path

from gerar_banner_fabrica import COR, TEKTUR, Fonte, Glifos, bloco, engrenagem, n, poli

PASTA = Path(__file__).resolve().parent
ASSETS = PASTA.parent / "assets"
PLEX = PASTA / "fontes" / "ibmplexsans" / "IBMPlexSans[wdth,wght].ttf"

TK900 = Fonte(TEKTUR, {"wght": 900, "wdth": 100}, "a")
TK700 = Fonte(TEKTUR, {"wght": 700, "wdth": 85}, "b")
PX500 = Fonte(PLEX, {"wght": 500, "wdth": 100}, "p")

SELOS = [
    ("portfolio", "PORTFÓLIO", "pasta", True),
    ("linkedin", "LINKEDIN", "in", True),
    ("aracaju", "ARACAJU · SE", "pino", False),
    ("ads", "ADS · SUPERIOR COMPLETO", "capelo", False),
]
TITULOS = [("sobre", "SOBRE"), ("em-destaque", "EM DESTAQUE"), ("projetos", "PROJETOS"), ("stack", "STACK"),
           ("monitor", "MONITOR DE CARGAS")]
PROJETOS = [
    ("dw-tempo-real", "DW em tempo real", "01", "banco",
     ["Espelho incremental ERP → DW de minuto", "em minuto, por impressão digital de linha", "e com travas contra carga ruim."],
     ["Python", "SQL Server", "ETL"]),
    ("conferencia-nfse", "Conferência de NFS-e", "02", "nota",
     ["Confere nota × lançamento e retenções", "(ISS, INSS, IRRF, PIS/COFINS/CSLL) e", "devolve um parecer em PDF."],
     ["Python", "Regras fiscais", "PDF"]),
    ("robo-portal-web", "Robô de portal web", "03", "navegador",
     ["RPA com Playwright: fila, novas tentativas,", "evidência em print e CPF mascarado no", "log. Testes sem abrir navegador."],
     ["Playwright", "RPA", "SQLite"]),
    ("robo-erp-desktop", "Robô de ERP desktop", "04", "monitor",
     ["UI Automation no Windows: acha o campo", "pelo nome e lança títulos de uma", "planilha, até com a janela minimizada."],
     ["pywinauto", "WinForms", "RPA"]),
    ("relatorios-automaticos", "Relatórios automáticos", "05", "envelope",
     ["Do banco para um e-mail pronto para agir,", "com a planilha em anexo e agendamento", "oculto no Windows."],
     ["Python", "Excel", "Agendador"]),
    ("EdyVerder", "Este perfil", "06", "fabrica",
     ["Fábrica de dados, cartões e monitor de", "cargas desenhados por código e", "atualizados todo dia pelo GitHub Actions."],
     ["SVG", "GitHub Actions", "Python"]),
]
STACK = [
    ("DADOS", COR["dado"], ["Python", "SQL Server", "pandas", "SQLite", "Pentaho PDI", "Apache Hop"]),
    ("AUTOMAÇÃO", COR["brasa"], ["Playwright", "Selenium", "pywinauto", "PowerShell", "GitHub Actions"]),
    ("WEB E IA", COR["bruto3"], ["FastAPI", "JavaScript", "Excel · openpyxl", "Claude API", "Git"]),
]


def documento(w, h, titulo, corpo, defs, css):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n(w)} {n(h)}" width="{n(w)}" height="{n(h)}" '
            f'role="img" aria-labelledby="t"><title id="t">{html.escape(titulo)}</title>'
            f'<defs>{defs}</defs><style>{css}</style>{corpo}</svg>\n')


def listras(x, y, w, h, cid):
    """Faixa de sinalização laranja e escura, como as da placa do banner."""
    faixas = "".join(f'<path d="M{n(x + i * 10)} {n(y + h)}l{n(h)} {n(-h)}h5l{n(-h)} {n(h)}z"/>'
                     for i in range(-4, int(w / 10) + 3))
    return (f'<clipPath id="{cid}"><rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}"/></clipPath>',
            f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" fill="{COR["listra"]}"/>'
            f'<g clip-path="url(#{cid})" fill="{COR["brasa"]}">{faixas}</g>')


# ------------------------------------------------------------------------------------------------ ícones

def icone(nome, cx, cy, cor, escala=1.0):
    """Ícones de traço simples, desenhados numa caixa de 24 x 24 centrada em (cx, cy)."""
    tr = f'transform="translate({n(cx - 12 * escala)} {n(cy - 12 * escala)}) scale({n(escala, 3)})"'
    traco = f'fill="none" stroke="{cor}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    desenhos = {
        "pasta": f'<g {tr} {traco}><rect x="3" y="7.5" width="18" height="12.5" rx="2"/><path d="M9 7.5V5h6v2.5M3 12.5h18"/></g>',
        "pino": f'<g {tr} {traco}><path d="M12 21s-6.5-6.2-6.5-11a6.5 6.5 0 0 1 13 0c0 4.8-6.5 11-6.5 11z"/>'
                f'<circle cx="12" cy="10" r="2.4"/></g>',
        "capelo": f'<g {tr} {traco}><path d="M12 5 2.5 9.5 12 14l9.5-4.5z"/><path d="M6.5 11.6v4.6c0 1.4 2.5 2.8 5.5 2.8s5.5-1.4 5.5-2.8v-4.6M21.5 9.5v5.5"/></g>',
        "banco": f'<g {tr} {traco}><ellipse cx="12" cy="5.5" rx="7.5" ry="2.8"/><path d="M4.5 5.5v13c0 1.5 3.4 2.8 7.5 2.8s7.5-1.3 7.5-2.8v-13M4.5 12c0 1.5 3.4 2.8 7.5 2.8s7.5-1.3 7.5-2.8"/></g>',
        "nota": f'<g {tr} {traco}><path d="M6 2.8h8.5l4 4V21H6z"/><path d="M14.5 2.8v4h4M9 14.2l2.2 2.2 4.3-4.6"/></g>',
        "navegador": f'<g {tr} {traco}><rect x="2.5" y="4" width="19" height="15" rx="2"/><path d="M2.5 8.5h19"/>'
                     f'<path d="M11.5 11.5l6 2.2-2.6 1 1.6 2.6-1.4.8-1.6-2.6-2 1.7z" fill="{cor}"/></g>',
        "monitor": f'<g {tr} {traco}><rect x="2.5" y="3.5" width="19" height="13" rx="1.8"/><path d="M9 21h6M12 16.5V21"/>'
                   f'<rect x="6" y="7" width="7" height="5.5" rx=".6"/></g>',
        "envelope": f'<g {tr} {traco}><rect x="2.5" y="5" width="19" height="14" rx="2"/><path d="m3 6.5 9 6.5 9-6.5"/></g>',
        "fabrica": f'<g {tr} {traco}><path d="M2.5 21V11l5.5 3.5V11l5.5 3.5V11l5.5 3.5V4h3v17z"/><path d="M7 17.5h2M12 17.5h2"/></g>',
    }
    if nome == "in":
        g = Glifos("i")
        usos, _ = g.escrever(TK900, TK900.tamanho_para_cap(12.5), "in", cx, cy + 6.2, 0.5, "middle")
        return "".join(g.defs), f'<rect x="{n(cx - 11)}" y="{n(cy - 11)}" width="22" height="22" rx="4" fill="{cor}"/>' \
                                f'<g fill="{COR["brasa3"]}">{usos}</g>'
    return "", desenhos[nome]


# ------------------------------------------------------------------------------------------------ selos

def selo(rotulo, nome_icone, destaque):
    c = COR
    g = Glifos("s")
    cap, H, caixa = 12.5, 40, 40
    tam = TK700.tamanho_para_cap(cap)
    _, larg = TK700.posicoes(rotulo, tam, 1.6)
    fim = 30
    W = caixa + 14 + larg + fim
    texto, _ = g.escrever(TK700, tam, rotulo, caixa + 14, H / 2 + cap / 2, 1.6)
    fundo_icone = c["brasa2"] if destaque else c["aco2"]
    cor_icone = "#ffffff" if destaque else c["dado"]
    defs_icone, desenho = icone(nome_icone, caixa / 2, H / 2, cor_icone)
    if destaque:   # seta de link externo, no laranja
        ponta = (f'<path d="M{n(W - 21)} {n(H / 2 + 5)}l9-9M{n(W - 18)} {n(H / 2 - 4)}h6v6" fill="none" '
                 f'stroke="{c["brasa"]}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
    else:          # luz de status piscando
        ponta = f'<circle class="led" cx="{n(W - 15)}" cy="{H / 2}" r="3.2" fill="{c["dado"]}"/>'
    defs = (defs_icone + "".join(g.defs)
            + f'<clipPath id="corpo"><rect width="{n(W)}" height="{H}" rx="7"/></clipPath>'
            + '<linearGradient id="brilho" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
              '<stop offset=".5" stop-color="#fff" stop-opacity=".22"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>'
              '</linearGradient>')
    css = ("@keyframes led{0%,100%{opacity:1}50%{opacity:.25}}.led{animation:led 2.4s ease-in-out infinite}"
           f"@keyframes passa{{0%{{transform:translateX(-120px)}}35%,100%{{transform:translateX({int(W + 60)}px)}}}}"
           ".passa{animation:passa 6s ease-in-out infinite}")
    corpo = (f'<g clip-path="url(#corpo)">'
             f'<rect width="{n(W)}" height="{H}" fill="{c["aco1"]}"/>'
             f'<rect width="{n(W)}" height="1.5" fill="{c["aco4"]}"/>'
             f'<rect y="{H - 2}" width="{n(W)}" height="2" fill="{c["aco0"]}"/>'
             f'<rect width="{caixa}" height="{H}" fill="{fundo_icone}"/>'
             f'{desenho}<g fill="{c["texto"]}">{texto}</g>{ponta}'
             f'<g class="passa"><rect x="0" y="0" width="60" height="{H}" fill="url(#brilho)" transform="skewX(-18)"/></g>'
             f'</g><rect x=".5" y=".5" width="{n(W - 1)}" height="{H - 1}" rx="6.5" fill="none" stroke="{c["aco3"]}"/>')
    return documento(W, H, rotulo.title(), corpo, defs, css)


# ------------------------------------------------------------------------------------------------ títulos

def titulo(rotulo):
    """Placa da seção no centro, com uma esteira dos dois lados: entram registros brutos e saem tratados."""
    c = COR
    g = Glifos("t")
    W, H = 880, 64
    cap = 20
    tam = TK900.tamanho_para_cap(cap)
    _, larg = TK900.posicoes(rotulo, tam, 3)
    pad = 48
    lp = larg + 2 * pad
    x0, y0, alt = (W - lp) / 2, 18, 36
    texto, _ = g.escrever(TK900, tam, rotulo, W / 2, y0 + alt / 2 + cap / 2, 3, "middle")
    d1, l1 = listras(x0 + 5, y0 + 5, 20, alt - 10, "l1")
    d2, l2 = listras(x0 + lp - 25, y0 + 5, 20, alt - 10, "l2")
    placa = (f'<path d="{poli([(x0, y0), (x0 + lp, y0), (x0 + lp + 6, y0 - 6), (x0 + 6, y0 - 6)])}" fill="{c["aco3"]}"/>'
             f'<path d="{poli([(x0 + lp, y0), (x0 + lp + 6, y0 - 6), (x0 + lp + 6, y0 + alt - 6), (x0 + lp, y0 + alt)])}" fill="{c["aco0"]}"/>'
             f'<rect x="{n(x0)}" y="{y0}" width="{n(lp)}" height="{alt}" fill="{c["aco1"]}"/>'
             f'<rect x="{n(x0)}" y="{y0}" width="{n(lp)}" height="1.5" fill="{c["aco4"]}"/>' + l1 + l2
             + "".join(f'<circle cx="{n(px)}" cy="{n(py)}" r="1.6" fill="{c["aco5"]}"/>'
                       for px in (x0 + 33, x0 + lp - 33) for py in (y0 + 7, y0 + alt - 7))
             + f'<g fill="{c["texto"]}">{texto}</g>')
    trilho_y = y0 + alt - 4
    bruto = bloco(c["bruto"], c["bruto3"], c["bruto2"], "", w=14, h=11, d=4)
    tratado = bloco(c["dado"], c["dado_claro"], c["dado2"], "", w=14, h=11, d=4)
    esq_fim, dir_ini = x0 - 14, x0 + lp + 20
    defs = (d1 + d2 + "".join(g.defs)
            + f'<g id="bb">{bruto}</g><g id="bt">{tratado}</g>'
            + f'<clipPath id="ce"><rect x="16" y="0" width="{n(esq_fim - 16)}" height="{H}"/></clipPath>'
            + f'<clipPath id="cd"><rect x="{n(dir_ini)}" y="0" width="{n(W - 16 - dir_ini)}" height="{H}"/></clipPath>'
            + '<linearGradient id="some" x1="0" x2="1"><stop offset="0" stop-color="#000"/>'
              '<stop offset=".12" stop-color="#fff"/><stop offset=".88" stop-color="#fff"/>'
              '<stop offset="1" stop-color="#000"/></linearGradient>'
            + f'<mask id="pontas"><rect width="{W}" height="{H}" fill="url(#some)"/></mask>')

    def trilho(xa, xb, classe, ref, clip):
        rolos = "".join(f'<circle cx="{x}" cy="{n(trilho_y + 5)}" r="2" fill="{c["aco0"]}" stroke="{c["aco4"]}" stroke-width=".8"/>'
                        for x in range(int(xa) + 8, int(xb), 22))
        caixas = "".join(f'<use href="#{ref}" x="{x}" y="{n(trilho_y)}"/>' for x in range(int(xa) - 44, int(xb) + 44, 44))
        return (f'<rect x="{n(xa)}" y="{n(trilho_y)}" width="{n(xb - xa)}" height="10" fill="{c["aco2"]}"/>'
                f'<rect x="{n(xa)}" y="{n(trilho_y)}" width="{n(xb - xa)}" height="1.2" fill="{c["aco4"]}"/>' + rolos
                + f'<g clip-path="url(#{clip})"><g class="{classe}">{caixas}</g></g>')

    css = ("@keyframes anda{to{transform:translateX(44px)}}.anda{animation:anda 2.2s linear infinite}")
    corpo = (f'<g mask="url(#pontas)">' + trilho(16, esq_fim, "anda", "bb", "ce")
             + trilho(dir_ini, W - 16, "anda", "bt", "cd") + '</g>' + placa)
    return documento(W, H, rotulo.capitalize(), corpo, defs, css)


# ------------------------------------------------------------------------------------------------ cartões

def cartao(repo, nome, numero, nome_icone, linhas, tags):
    c = COR
    g = Glifos("c")
    W, H = 420, 196
    rot_cap, tit_cap = 8.5, 16.5
    rotulo, _ = g.escrever(TK700, TK700.tamanho_para_cap(rot_cap), f"{numero} · REPOSITÓRIO", 24, 32, 2.2)
    tam_tit = TK900.tamanho_para_cap(tit_cap)
    _, larg_tit = TK900.posicoes(nome, tam_tit, 0.6)
    if larg_tit > 300:
        tam_tit *= 300 / larg_tit
    tit, _ = g.escrever(TK900, tam_tit, nome, 24, 60, 0.6)
    tam_txt = 12.4
    maior = max(PX500.posicoes(l, tam_txt)[1] for l in linhas)
    if maior > 372:
        tam_txt *= 372 / maior
    desc = "".join(g.escrever(PX500, tam_txt, l, 24, 92 + i * 18)[0] for i, l in enumerate(linhas))
    # etiquetas em caixas, como os blocos da esteira
    tam_tag = TK700.tamanho_para_cap(7.6)
    caixas, x = [], 24
    for k, t in enumerate(tags):
        lt = TK700.posicoes(t, tam_tag, 1)[1]
        w = lt + 18
        cores = (c["dado2"], c["dado"], c["dado3"]) if k == 0 else (c["aco2"], c["aco3"], c["aco1"])
        rot, _ = g.escrever(TK700, tam_tag, t, x + w / 2, 160.3, 1, "middle")   # meio da face (156,5) + meia altura
        caixas.append(f'<g transform="translate({n(x + w / 2)} 166)">{bloco(*cores, "", w=w, h=19, d=5)}</g>'
                      f'<g fill="{c["texto"]}">{rot}</g>')
        x += w + 13
    # canto do ícone: caixa, ícone do projeto, engrenagem girando e luz de status
    defs_icone, desenho = icone(nome_icone, 373, 46, c["dado_claro"], 1.1)
    dG, _, _ = engrenagem(10, 1.9, 2.4, 4)
    ext = (f'<rect x="347" y="20" width="52" height="52" rx="9" fill="{c["aco0"]}" stroke="{c["aco2"]}"/>' + desenho
           + f'<g transform="translate(398 22)"><g class="gira"><path d="{dG}" fill="{c["brasa"]}" fill-rule="evenodd"/></g></g>'
           + f'<circle class="led" cx="352" cy="25" r="2.4" fill="{c["dado"]}"/>')
    # esteira no rodapé
    mini_b = bloco(c["bruto"], c["bruto3"], c["bruto2"], "", w=10, h=7, d=3)
    mini_t = bloco(c["dado"], c["dado_claro"], c["dado2"], "", w=10, h=7, d=3)
    caixinhas = "".join(f'<use href="#{"mt" if k % 2 else "mb"}" x="{x}" y="186"/>' for k, x in enumerate(range(-30, W + 40, 34)))
    defs = (defs_icone + "".join(g.defs)
            + f'<linearGradient id="painel" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c["aco1"]}"/>'
              f'<stop offset="1" stop-color="{c["parede2"]}"/></linearGradient>'
            + f'<pattern id="pontos" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="9" cy="9" r=".9" fill="#2b3b5e"/></pattern>'
            + f'<linearGradient id="linha" x1="0" x2="1"><stop offset="0" stop-color="{c["brasa"]}"/>'
              f'<stop offset="1" stop-color="{c["brasa"]}" stop-opacity="0"/></linearGradient>'
            + f'<clipPath id="moldura"><rect width="{W}" height="{H}" rx="14"/></clipPath>'
            + f'<g id="mb">{mini_b}</g><g id="mt">{mini_t}</g>')
    css = ("@keyframes gira{to{transform:rotate(360deg)}}.gira{animation:gira 6s linear infinite}"
           "@keyframes led{0%,100%{opacity:1}50%{opacity:.2}}.led{animation:led 2s ease-in-out infinite}"
           "@keyframes anda{to{transform:translateX(68px)}}.anda{animation:anda 3s linear infinite}")
    corpo = (f'<g clip-path="url(#moldura)">'
             f'<rect width="{W}" height="{H}" fill="url(#painel)"/><rect width="{W}" height="{H}" fill="url(#pontos)" opacity=".5"/>'
             f'<rect x="0" y="22" width="3" height="52" fill="{c["brasa"]}"/>'
             f'<g fill="{c["brasa"]}">{rotulo}</g><g fill="#ffffff">{tit}</g>'
             f'<rect x="24" y="68" width="60" height="2.5" fill="url(#linha)"/>'
             f'<g fill="#c3cce0">{desc}</g>' + "".join(caixas) + ext
             + f'<rect x="0" y="186" width="{W}" height="10" fill="{c["aco1"]}"/>'
               f'<rect x="0" y="186" width="{W}" height="1" fill="{c["aco3"]}"/>'
             + f'<g class="anda">{caixinhas}</g></g>'
             + f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="13.5" fill="none" stroke="{c["aco2"]}"/>')
    return documento(W, H, f"{nome} ({repo})", corpo, defs, css)


# ------------------------------------------------------------------------------------------------ stack

def stack():
    """Três prateleiras de armazém; cada tecnologia é uma caixa. Um leitor de luz varre cada prateleira."""
    c = COR
    g = Glifos("k")
    W, H = 880, 318
    x_rack, x_fim = 196, 856
    tam_cat = TK900.tamanho_para_cap(11.5)
    tam_item = TK700.tamanho_para_cap(9.2)
    partes, defs_extra, css_scan = [], [], []
    for i, (cat, cor, itens) in enumerate(STACK):
        base = 104 + i * 96
        # placa da categoria à esquerda
        larg_cat = TK900.posicoes(cat, tam_cat, 1.8)[1]
        escala = min(1.0, 150 / larg_cat)
        txt, _ = g.escrever(TK900, tam_cat * escala, cat, 30, base - 26, 1.8 * escala)
        partes.append(f'<rect x="22" y="{base - 52}" width="4" height="40" fill="{cor}"/>'
                      f'<g fill="{c["texto"]}">{txt}</g>')
        # caixas na prateleira
        larguras = [TK700.posicoes(t, tam_item, 1.2)[1] + 26 for t in itens]
        folga = (x_fim - x_rack - 24 - sum(larguras)) / (len(itens) - 1 + 2)
        x = x_rack + 12 + folga
        for k, (t, w) in enumerate(zip(itens, larguras)):
            frente, topo, lado = c["aco2"], c["aco3"], c["aco1"]
            rot, _ = g.escrever(TK700, tam_item, t, x + w / 2, base - 10.6, 1.2, "middle")
            partes.append(f'<g transform="translate({n(x + w / 2)} {base})">'
                          f'{bloco(frente, topo, lado, "", w=w, h=34, d=8)}'
                          f'<rect x="{n(-w / 2)}" y="-34" width="{n(w)}" height="4" fill="{cor}"/></g>'
                          f'<g fill="{c["texto"]}">{rot}</g>'
                          f'<circle class="led" style="animation-delay:-{(k * 0.37 + i * 0.5) % 2.4:.2f}s" '
                          f'cx="{n(x + w - 7)}" cy="{base - 7}" r="1.9" fill="{cor}"/>')
            x += w + folga
        # prateleira com faixa de sinalização
        dl, ll = listras(x_rack, base + 1, x_fim - x_rack, 7, f"pl{i}")
        defs_extra.append(dl)
        partes.append(f'<rect x="{x_rack}" y="{base}" width="{x_fim - x_rack}" height="9" fill="{c["aco3"]}"/>' + ll)
        # leitor varrendo a prateleira
        partes.append(f'<g clip-path="url(#vao{i})"><g class="scan" style="animation-delay:-{i * 2.1:.1f}s">'
                      f'<rect x="{x_rack - 70}" y="{base - 60}" width="60" height="60" fill="url(#luz)"/></g></g>')
        defs_extra.append(f'<clipPath id="vao{i}"><rect x="{x_rack}" y="{base - 60}" width="{x_fim - x_rack}" height="60"/></clipPath>')
    colunas = "".join(f'<rect x="{x}" y="34" width="9" height="{H - 50}" fill="{c["aco1"]}"/>'
                      f'<rect x="{x}" y="34" width="2" height="{H - 50}" fill="{c["aco4"]}"/>' for x in (x_rack - 9, x_fim))
    defs = ("".join(g.defs) + "".join(defs_extra)
            + f'<linearGradient id="painel" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c["aco1"]}"/>'
              f'<stop offset="1" stop-color="{c["parede2"]}"/></linearGradient>'
            + f'<pattern id="pontos" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="10" cy="10" r=".9" fill="#2b3b5e"/></pattern>'
            + f'<linearGradient id="luz" x1="0" x2="1"><stop offset="0" stop-color="{c["dado"]}" stop-opacity="0"/>'
              f'<stop offset=".5" stop-color="{c["dado_claro"]}" stop-opacity=".28"/><stop offset="1" stop-color="{c["dado"]}" stop-opacity="0"/></linearGradient>'
            + f'<clipPath id="moldura"><rect width="{W}" height="{H}" rx="14"/></clipPath>')
    css = ("@keyframes led{0%,100%{opacity:1}50%{opacity:.15}}.led{animation:led 2.4s ease-in-out infinite}"
           f"@keyframes scan{{0%{{transform:translateX(0)}}60%,100%{{transform:translateX({x_fim - x_rack + 80}px)}}}}"
           ".scan{animation:scan 6.3s ease-in-out infinite}")
    corpo = (f'<g clip-path="url(#moldura)"><rect width="{W}" height="{H}" fill="url(#painel)"/>'
             f'<rect width="{W}" height="{H}" fill="url(#pontos)" opacity=".5"/>{colunas}{"".join(partes)}</g>'
             f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="13.5" fill="none" stroke="{c["aco2"]}"/>')
    titulo_txt = "Stack: " + "; ".join(f"{cat.lower()}: {', '.join(itens)}" for cat, _, itens in STACK)
    return documento(W, H, titulo_txt, corpo, defs, css)


def gravar(caminho, conteudo):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo, encoding="utf-8")
    return len(conteudo.encode()) / 1024


def main():
    total = 0
    for arq, rotulo, icn, destaque in SELOS:
        total += gravar(ASSETS / "selos" / f"{arq}.svg", selo(rotulo, icn, destaque))
    for arq, rotulo in TITULOS:
        total += gravar(ASSETS / "titulos" / f"{arq}.svg", titulo(rotulo))
    for repo, nome, numero, icn, linhas, tags in PROJETOS:
        total += gravar(ASSETS / "cards" / f"{repo}.svg", cartao(repo, nome, numero, icn, linhas, tags))
    total += gravar(ASSETS / "stack.svg", stack())
    print(f"{len(SELOS)} selos, {len(TITULOS)} títulos, {len(PROJETOS)} cartões e a stack: {total:.0f} KB no total")


if __name__ == "__main__":
    main()
