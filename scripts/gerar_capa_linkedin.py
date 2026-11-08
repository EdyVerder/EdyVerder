"""Capa do LinkedIn (1584 x 396) no tema "fábrica de dados", com outra cena: uma refinaria de dados.
Tanques de origem (ERP, API, CSV) mandam registros brutos por canos com válvulas e manômetros até a coluna de
ETL; dela sai o dado tratado para o tanque do DW e daí para o painel. O canto de baixo à esquerda fica livre
porque a foto do perfil cobre essa área.

Uso: python -m pip install fonttools && python scripts/gerar_capa_linkedin.py   (gera assets/linkedin/capa-linkedin.svg)
"""
import math
from pathlib import Path

from gerar_banner_fabrica import COR, bloco, engrenagem, n, poli
from gerar_pecas import PX500, TK700, TK900, Glifos, listras

W, H, PISO = 1584, 396, 350
SAIDA = Path(__file__).resolve().parents[1] / "assets" / "linkedin" / "capa-linkedin.svg"
c = COR
g = Glifos("q")
defs = []


def texto(fonte, cap, conteudo, x, base, cor, espaco=0.0, ancora="start"):
    usos, larg = g.escrever(fonte, fonte.tamanho_para_cap(cap), conteudo, x, base, espaco, ancora)
    return f'<g fill="{cor}">{usos}</g>', larg


def placa(cx, cy, rotulo, cor_txt="#ffffff", cap=11, pad=11):
    t, larg = texto(TK900, cap, rotulo, cx, cy + cap / 2, cor_txt, 1.6, "middle")
    w, h = larg + 2 * pad, cap + 2 * pad - 4
    return (f'<rect x="{n(cx - w / 2)}" y="{n(cy - h / 2)}" width="{n(w)}" height="{n(h)}" rx="3" fill="{c["aco0"]}" '
            f'stroke="{c["aco3"]}"/>' + t)


def cilindro(x, topo, w, h, ry=None, faixas=()):
    """Tanque em pé: corpo com sombreado de cilindro, tampa elíptica e anéis. Luz quente vem da esquerda
    (onde está o texto) e luz fria da direita (o brilho do DW), por isso as duas bordas acesas."""
    ry = ry or w * 0.16
    cx = x + w / 2
    corpo = (f'M{n(x)} {n(topo)}V{n(topo + h)}A{n(w / 2)} {n(ry)} 0 0 0 {n(x + w)} {n(topo + h)}V{n(topo)}Z')
    aneis = "".join(f'<path d="M{n(x)} {n(topo + f)}A{n(w / 2)} {n(ry)} 0 0 0 {n(x + w)} {n(topo + f)}" '
                    f'fill="none" stroke="{c["aco0"]}" stroke-width="3" opacity=".7"/>'
                    f'<path d="M{n(x)} {n(topo + f + 2.5)}A{n(w / 2)} {n(ry)} 0 0 0 {n(x + w)} {n(topo + f + 2.5)}" '
                    f'fill="none" stroke="{c["aco5"]}" stroke-width="1" opacity=".35"/>' for f in faixas)

    def fundo_y(xx):   # altura da borda de baixo (arco) na posição xx
        t = (xx - cx) / (w / 2)
        return topo + h + ry * math.sqrt(max(0.0, 1 - t * t))

    x1, x2 = x + w * 0.19, x + w * 0.27
    reflexo = (f'<path d="M{n(x1)} {n(topo)}L{n(x2)} {n(topo)}L{n(x2)} {n(fundo_y(x2))}L{n(x1)} {n(fundo_y(x1))}Z" '
               f'fill="#ffffff" opacity=".075"/>')
    bordas = (f'<path d="M{n(x + 1.3)} {n(topo + 3)}V{n(topo + h - 2)}" stroke="{c["brasa_clara"]}" stroke-opacity=".3" stroke-width="1.6"/>'
              f'<path d="M{n(x + w - 1.3)} {n(topo + 3)}V{n(topo + h - 2)}" stroke="{c["dado"]}" stroke-opacity=".3" stroke-width="1.6"/>')
    aro = (f'<path d="M{n(x + 1)} {n(topo)}A{n(w / 2 - 1)} {n(ry - 1)} 0 0 0 {n(x + w - 1)} {n(topo)}" fill="none" '
           f'stroke="{c["aco5"]}" stroke-width="1.5" opacity=".9"/>')
    return (f'<path d="{corpo}" fill="url(#cil)"/>{aneis}{reflexo}{bordas}'
            f'<ellipse cx="{n(cx)}" cy="{n(topo)}" rx="{n(w / 2)}" ry="{n(ry)}" fill="{c["aco4"]}"/>'
            f'<ellipse cx="{n(cx)}" cy="{n(topo)}" rx="{n(w / 2 - 5)}" ry="{n(ry - 3)}" fill="{c["aco3"]}"/>' + aro)


def sombra(cx, largura):
    """Sombra de contato no piso, para o tanque não parecer flutuar."""
    return (f'<ellipse cx="{n(cx)}" cy="{PISO + 1}" rx="{n(largura * 0.62)}" ry="6" fill="#000" opacity=".55" '
            f'filter="url(#sombra)"/>')


def pulso(x, y, comprimento, tratado, vertical=False):
    """Pulso de luz correndo no cano: rastro que acende até a cabeça. Laranja antes do ETL (dado bruto),
    verde-água depois (dado tratado)."""
    rastro = "rastroDv" if vertical else ("rastroD" if tratado else "rastroB")
    cabeca = c["dado_claro"] if tratado else c["brasa_clara"]
    if vertical:
        corpo = f'<rect x="{n(x - 2.2)}" y="{n(y - comprimento)}" width="4.4" height="{n(comprimento)}" rx="2.2" fill="url(#{rastro})"/>'
    else:
        corpo = f'<rect x="{n(x - comprimento)}" y="{n(y - 2.2)}" width="{n(comprimento)}" height="4.4" rx="2.2" fill="url(#{rastro})"/>'
    return f'<g filter="url(#brilho)">{corpo}<circle cx="{n(x)}" cy="{n(y)}" r="3.4" fill="{cabeca}"/></g>'


def tubo(pontos, w=12):
    d = "M" + "L".join(f"{n(x)} {n(y)}" for x, y in pontos)
    return (f'<path d="{d}" fill="none" stroke="{c["aco0"]}" stroke-width="{w + 5}" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{c["aco3"]}" stroke-width="{w}" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{c["aco5"]}" stroke-width="{n(w * 0.28)}" stroke-linejoin="round" '
            f'opacity=".55" transform="translate(0 {n(-w * 0.22)})"/>')


def flange(x, y, vertical=False):
    return (f'<rect x="{n(x - 3)}" y="{n(y - 11)}" width="6" height="22" rx="1.5" fill="{c["aco4"]}"/>' if not vertical
            else f'<rect x="{n(x - 11)}" y="{n(y - 3)}" width="22" height="6" rx="1.5" fill="{c["aco4"]}"/>')


def valvula(x, y):
    raios = "".join(f'<path d="M{n(x)} {n(y - 22)}l{n(8 * math.cos(a))} {n(8 * math.sin(a))}" stroke="{c["brasa"]}" stroke-width="2"/>'
                    for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2))
    return (f'<rect x="{n(x - 2.5)}" y="{n(y - 16)}" width="5" height="12" fill="{c["aco4"]}"/>'
            f'<circle cx="{n(x)}" cy="{n(y - 22)}" r="8" fill="none" stroke="{c["brasa"]}" stroke-width="3"/>'
            + raios + f'<circle cx="{n(x)}" cy="{n(y - 22)}" r="2.2" fill="{c["brasa2"]}"/>')


def manometro(x, y, angulo):
    marcas = "".join(f'<path d="M{n(x + 7.5 * math.cos(a))} {n(y + 7.5 * math.sin(a))}L{n(x + 10 * math.cos(a))} '
                     f'{n(y + 10 * math.sin(a))}" stroke="{c["aco1"]}" stroke-width="1.2"/>'
                     for a in [math.radians(150 + k * 30) for k in range(9)])
    a = math.radians(angulo)
    return (f'<rect x="{n(x - 2)}" y="{n(y + 10)}" width="4" height="9" fill="{c["aco4"]}"/>'
            f'<circle cx="{n(x)}" cy="{n(y)}" r="12.5" fill="{c["aco1"]}"/><circle cx="{n(x)}" cy="{n(y)}" r="10.5" fill="#e9eff9"/>'
            + marcas + f'<path d="M{n(x)} {n(y)}L{n(x + 8 * math.cos(a))} {n(y + 8 * math.sin(a))}" stroke="{c["brasa2"]}" '
                       f'stroke-width="2" stroke-linecap="round"/><circle cx="{n(x)}" cy="{n(y)}" r="1.8" fill="{c["aco1"]}"/>')


def janela(x, y, tratado):
    """Visor no cano mostrando um registro passando."""
    cores = (c["dado"], c["dado_claro"], c["dado2"]) if tratado else (c["bruto"], c["bruto3"], c["bruto2"])
    return (f'<rect x="{n(x - 15)}" y="{n(y - 11)}" width="30" height="22" rx="4" fill="{c["aco0"]}" stroke="{c["aco4"]}"/>'
            f'<rect x="{n(x - 12)}" y="{n(y - 8)}" width="24" height="16" rx="2" fill="#0b2a2a" opacity=".85"/>'
            f'<g transform="translate({n(x - 1)} {n(y + 6)})">{bloco(*cores, "", w=10, h=8, d=3)}</g>')


def main():
    defs.append(
        f'<linearGradient id="parede" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c["parede1"]}"/>'
        f'<stop offset="1" stop-color="{c["parede2"]}"/></linearGradient>'
        f'<linearGradient id="cil" x1="0" x2="1"><stop offset="0" stop-color="{c["aco2"]}"/><stop offset=".3" stop-color="{c["aco4"]}"/>'
        f'<stop offset=".65" stop-color="{c["aco2"]}"/><stop offset="1" stop-color="{c["aco0"]}"/></linearGradient>'
        f'<linearGradient id="nivel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c["dado_claro"]}"/>'
        f'<stop offset="1" stop-color="{c["dado2"]}"/></linearGradient>'
        f'<radialGradient id="luzEsq" cx="230" cy="110" r="360" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{c["brasa"]}" stop-opacity=".13"/>'
        f'<stop offset="1" stop-color="{c["brasa"]}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="luzDw" cx="1150" cy="230" r="300" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{c["dado"]}" stop-opacity=".16"/>'
        f'<stop offset="1" stop-color="{c["dado"]}" stop-opacity="0"/></radialGradient>'
        f'<pattern id="pontos" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="12" cy="12" r="1" fill="#2b3b5e"/></pattern>'
        # brilho (luz que vaza dos visores, do painel e dos pulsos), halo largo e sombra de contato
        f'<filter id="brilho" filterUnits="userSpaceOnUse" x="-200" y="-200" width="{W + 400}" height="{H + 400}">'
        f'<feGaussianBlur stdDeviation="3.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/>'
        f'<feMergeNode in="SourceGraphic"/></feMerge></filter>'
        f'<filter id="halo" filterUnits="userSpaceOnUse" x="-200" y="-200" width="{W + 400}" height="{H + 400}">'
        f'<feGaussianBlur stdDeviation="18"/></filter>'
        f'<filter id="sombra" filterUnits="userSpaceOnUse" x="-200" y="-200" width="{W + 400}" height="{H + 400}">'
        f'<feGaussianBlur stdDeviation="3.5"/></filter>'
        f'<linearGradient id="rastroB" x1="0" x2="1"><stop offset="0" stop-color="{c["brasa"]}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{c["brasa_clara"]}"/></linearGradient>'
        f'<linearGradient id="rastroD" x1="0" x2="1"><stop offset="0" stop-color="{c["dado"]}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{c["dado_claro"]}"/></linearGradient>'
        f'<linearGradient id="rastroDv" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c["dado"]}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{c["dado_claro"]}"/></linearGradient>'
        # reflexo da fábrica no piso, sumindo para baixo
        f'<linearGradient id="reflexoG" x1="0" y1="{PISO}" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="#fff" stop-opacity=".3"/><stop offset=".85" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        # a planta termina no piso (o fundo dos tanques não invade o chão; espelhado, vira o recorte do reflexo)
        f'<clipPath id="acimaPiso"><rect x="0" y="-100" width="{W}" height="{PISO + 100}"/></clipPath>'
        f'<mask id="reflexo" maskUnits="userSpaceOnUse" x="0" y="{PISO}" width="{W}" height="{H - PISO}">'
        f'<rect x="0" y="{PISO}" width="{W}" height="{H - PISO}" fill="url(#reflexoG)"/></mask>')
    fundo = (f'<rect width="{W}" height="{H}" fill="url(#parede)"/><rect width="{W}" height="{PISO}" fill="url(#pontos)" opacity=".45"/>'
             f'<rect width="{W}" height="{H}" fill="url(#luzEsq)"/><rect width="{W}" height="{H}" fill="url(#luzDw)"/>'
             f'<rect y="{PISO}" width="{W}" height="{H - PISO}" fill="{c["piso"]}"/><rect y="{PISO}" width="{W}" height="1.5" fill="#26365a"/>'
             f'<rect y="{PISO + 30}" width="{W}" height="2" fill="{c["brasa"]}" opacity=".22"/>')

    # chamada à esquerda (a foto do perfil cobre o canto de baixo, então tudo fica no alto). No computador o
    # LinkedIn mostra a capa com cerca de metade da largura, por isso letras maiores que na versão anterior.
    sob, _ = texto(TK700, 12.5, "ENGENHARIA DE DADOS · AUTOMAÇÃO · ETL", 50, 56, c["brasa"], 2.2)
    l1, _ = texto(TK900, 33, "DO DADO BRUTO", 48, 109, "#ffffff", 2)
    l2, _ = texto(TK900, 33, "À DECISÃO", 48, 158, c["dado"], 2)
    # endereço do GitHub como na primeira capa: bolinha verde acesa, "github.com/" em branco e o nome em verde-água
    u1, larg1 = texto(TK900, 17, "github.com/", 80, 201, "#e9eff9", 1.2)
    u2, _ = texto(TK900, 17, "EdyVerder", 80 + larg1 + 1, 201, c["dado"], 1.2)
    url = (f'<circle cx="59" cy="192.5" r="12" fill="{c["dado"]}" opacity=".16"/>'
           f'<circle cx="59" cy="192.5" r="7" fill="{c["dado"]}" opacity=".35"/>'
           f'<circle cx="59" cy="192.5" r="5" fill="{c["dado"]}" filter="url(#brilho)"/>' + u1 + u2)
    chamada = sob + f'<g transform="translate(2.2 2.2)" opacity=".55">{l1.replace(chr(34) + "#ffffff" + chr(34), chr(34) + c["brasa4"] + chr(34))}</g>' + l1 + l2 + url

    # tanques de origem
    origens = []
    for i, (rot, x) in enumerate((("ERP", 500), ("API", 580), ("CSV", 660))):
        topo = 210 + (i % 2) * 18
        origens.append(f'<rect x="{x + 8}" y="{PISO - 18}" width="6" height="18" fill="{c["aco1"]}"/>'
                       f'<rect x="{x + 46}" y="{PISO - 18}" width="6" height="18" fill="{c["aco1"]}"/>'
                       + cilindro(x, topo, 60, PISO - 18 - topo - 9, faixas=(30, 60)) + placa(x + 30, topo + 48, rot, cap=10))
    # canos das origens até a coluna de ETL
    canos = (tubo([(530, 210), (530, 182), (842, 182)])
             + tubo([(610, 228), (610, 182)])
             + tubo([(690, 210), (690, 182)])
             + tubo([(718, 300), (760, 300), (760, 262), (842, 262)]))
    juntas = flange(650, 182) + flange(745, 182) + flange(760, 285, True)
    # coluna de ETL
    cx0, cw, ctopo = 838, 92, 64
    coluna = (cilindro(cx0, ctopo, cw, PISO - ctopo - 10, ry=12, faixas=(48, 96, 144, 192, 240))
              + f'<rect x="{cx0 - 6}" y="{PISO - 12}" width="{cw + 12}" height="12" fill="{c["aco2"]}"/>')
    escada = (f'<path d="M{cx0 + cw + 8} {ctopo + 20}V{PISO - 12}M{cx0 + cw + 20} {ctopo + 20}V{PISO - 12}" stroke="{c["aco4"]}" stroke-width="2.5"/>'
              + "".join(f'<path d="M{cx0 + cw + 8} {y}h12" stroke="{c["aco4"]}" stroke-width="2"/>' for y in range(ctopo + 30, PISO - 12, 14)))
    dl, faixa = listras(cx0, ctopo + 18, cw, 12, "lc")
    defs.append(dl)
    visores = "".join(f'<rect x="{cx0 + 30}" y="{y}" width="32" height="14" rx="3" fill="#0b2a2a" stroke="{c["aco0"]}"/>'
                      f'<rect x="{cx0 + 33}" y="{y + 3}" width="26" height="8" rx="2" fill="{c["dado"]}" opacity="{op}" '
                      f'filter="url(#brilho)"/>'
                      for y, op in ((132, .35), (180, .6), (228, .85), (276, 1)))
    chamine = (f'<rect x="{cx0 + 38}" y="{ctopo - 26}" width="16" height="22" fill="{c["aco2"]}"/>'
               f'<rect x="{cx0 + 35}" y="{ctopo - 30}" width="22" height="6" rx="1.5" fill="{c["aco4"]}"/>'
               + "".join(f'<circle cx="{cx0 + 46 + dx}" cy="{ctopo - 42 - k * 12}" r="{6 + k * 2}" fill="{c["dado_claro"]}" opacity="{.16 - k * .04}"/>'
                         for k, dx in enumerate((0, 6, -4))))
    rotulo_etl = placa(cx0 + cw / 2, ctopo + 64, "ETL", cap=12)
    # engrenagens da automação, ao pé da coluna
    dA, rpA, _ = engrenagem(14, 3.2, 5)
    dB, rpB, _ = engrenagem(9, 3.2, 3.5, 4)
    engr = (f'<g transform="translate(788 316)"><path d="{dA}" fill="{c["brasa"]}" fill-rule="evenodd"/></g>'
            f'<g transform="translate({n(788 + rpA + rpB)} {316 - 8}) rotate(18)"><path d="{dB}" fill="{c["aco5"]}" fill-rule="evenodd"/></g>')
    # da coluna ao DW e do DW ao painel
    canos2 = (tubo([(cx0 + cw / 2, ctopo - 4), (cx0 + cw / 2, 40), (1050, 40), (1050, 146)])
              + tubo([(1176, 300), (1250, 300), (1250, 236), (1300, 236)]))
    juntas2 = flange(960, 40) + flange(1050, 120, True) + flange(1214, 300)
    # tanque do DW
    dx0, dw_, dtopo = 980, 190, 158
    dw = (cilindro(dx0, dtopo, dw_, PISO - dtopo - 10, ry=22, faixas=(58, 118))
          + f'<rect x="{dx0 - 8}" y="{PISO - 12}" width="{dw_ + 16}" height="12" fill="{c["aco2"]}"/>'
          + f'<rect x="{dx0 + 22}" y="{dtopo + 40}" width="20" height="132" rx="4" fill="#0b2a2a" stroke="{c["aco0"]}" stroke-width="2"/>'
          + f'<rect x="{dx0 + 25}" y="{dtopo + 74}" width="14" height="95" rx="2" fill="url(#nivel)" filter="url(#brilho)"/>'
          + placa(dx0 + dw_ / 2 + 14, dtopo + 92, "DW", cor_txt=c["dado_claro"], cap=22, pad=14))
    # painel de BI
    px0, py0, pw, ph = 1300, 112, 236, 168
    barras = "".join(f'<rect x="{px0 + 22 + k * 24}" y="{py0 + ph - 24 - hgt}" width="14" height="{hgt}" rx="2" '
                     f'fill="{c["dado"] if k % 3 else c["brasa"]}"/>' for k, hgt in enumerate((38, 62, 50, 84, 70, 98)))
    linha = "M" + "L".join(f"{n(px0 + 166 + k * 10)} {n(py0 + 70 - 26 * math.sin(k / 1.6) - k * 3)}" for k in range(6))
    painel = (f'<rect x="{px0 - 4}" y="{py0 - 4}" width="{pw + 8}" height="{ph + 8}" rx="14" fill="{c["dado"]}" opacity=".16" '
              f'filter="url(#halo)"/>'
              f'<rect x="{px0 + pw / 2 - 6}" y="{py0 + ph}" width="12" height="{PISO - py0 - ph - 6}" fill="{c["aco2"]}"/>'
              f'<rect x="{px0 + pw / 2 - 34}" y="{PISO - 8}" width="68" height="8" rx="2" fill="{c["aco3"]}"/>'
              f'<rect x="{px0 - 8}" y="{py0 - 8}" width="{pw + 16}" height="{ph + 16}" rx="12" fill="{c["aco1"]}" stroke="{c["aco4"]}" stroke-width="1.5"/>'
              f'<rect x="{px0}" y="{py0}" width="{pw}" height="{ph}" rx="6" fill="#070b14"/>'
              f'<rect x="{px0}" y="{py0}" width="{pw}" height="{ph}" rx="6" fill="url(#luzTela)"/>'
              f'<rect x="{px0 + 14}" y="{py0 + 14}" width="64" height="7" rx="3.5" fill="#2e4068"/>'
              f'<circle cx="{px0 + pw - 18}" cy="{py0 + 18}" r="4" fill="{c["dado"]}" filter="url(#brilho)"/>'
              + f'<g filter="url(#brilho)" opacity=".95">{barras}</g>'
              + f'<path d="{linha}" fill="none" stroke="{c["brasa"]}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" '
                f'filter="url(#brilho)"/>'
              + f'<rect x="{px0 + 160}" y="{py0 + 100}" width="62" height="7" rx="3.5" fill="#2e4068"/>'
              + f'<rect x="{px0 + 160}" y="{py0 + 114}" width="44" height="7" rx="3.5" fill="#2e4068"/>'
              + f'<rect x="{px0 + 160}" y="{py0 + 128}" width="52" height="7" rx="3.5" fill="#2e4068"/>')
    acessorios = (valvula(700, 182) + valvula(1050, 40 + 0) + valvula(1250, 300) + manometro(612, 166, 300)
                  + manometro(800, 248, 330) + manometro(1050, 96, 290)
                  + janela(565, 182, False) + janela(740, 300, False) + janela(905, 40, True) + janela(1010, 40, True)
                  + janela(1277, 236, True))
    # pulsos de luz nos canos: laranja (bruto) até o ETL, verde-água (tratado) depois dele
    pulsos = (pulso(640, 182, 44, False) + pulso(828, 182, 50, False) + pulso(834, 262, 40, False)
              + pulso(992, 40, 46, True) + pulso(1050, 142, 26, True, vertical=True) + pulso(1240, 300, 40, True))
    defs.append(f'<linearGradient id="luzTela" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c["dado"]}" stop-opacity=".07"/>'
                f'<stop offset="1" stop-color="{c["dado"]}" stop-opacity="0"/></linearGradient>')
    dlp, lp = listras(470, PISO - 4, 1090, 4, "lp")
    defs.append(dlp)
    sombras = (sombra(530, 60) + sombra(610, 60) + sombra(690, 60) + sombra(cx0 + cw / 2, cw + 12)
               + sombra(dx0 + dw_ / 2, dw_ + 16) + sombra(px0 + pw / 2, 68))
    planta = ("".join(origens) + canos + juntas + engr + coluna + escada + faixa + visores + chamine
              + rotulo_etl + canos2 + juntas2 + dw + painel + acessorios + pulsos)
    # reflexo: a mesma planta espelhada no piso, bem apagada
    reflexo = (f'<g mask="url(#reflexo)"><use href="#planta" transform="matrix(1 0 0 -1 0 {2 * PISO})"/></g>')
    corpo = fundo + chamada + sombras + f'<g id="planta" clip-path="url(#acimaPiso)">{planta}</g>' + reflexo + lp
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
           f'aria-labelledby="t"><title id="t">Refinaria de dados: do dado bruto à decisão</title>'
           f'<defs>{"".join(defs)}{"".join(g.defs)}</defs>{corpo}</svg>\n')
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(svg, encoding="utf-8")
    print(f"{SAIDA.name}: {len(svg.encode()) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
