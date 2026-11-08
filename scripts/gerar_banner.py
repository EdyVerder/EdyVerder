"""Tema "pipeline vivo" do perfil: gera assets/banner.svg (1200 x 400).

O nome VERDER fica no centro, grande, e em volta dele roda um pipeline de dados como num canvas do
Apache Hop: fontes (banco, API, planilha) -> engrenagens -> data warehouse -> orquestrador ->
consumidores (painel, e-mail, robô). Pacotes correm pelas arestas e cada nó pulsa quando um chega.

Tudo é SVG puro: as letras viram <path> com o fontTools (não depende de fonte instalada), os pacotes
andam com SMIL (animateMotion) e o resto com CSS, que para com prefers-reduced-motion.
Uso: python -m pip install fonttools && python scripts/gerar_banner.py
"""
import functools
import math
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

AQUI = Path(__file__).resolve().parent
FONTES = AQUI / "fontes"   # Martian Mono e IBM Plex Sans, licença OFL (cada pasta tem o seu OFL.txt)
MARTIAN = FONTES / "martianmono" / "MartianMono[wdth,wght].ttf"
PLEX = FONTES / "ibmplexsans" / "IBMPlexSans[wdth,wght].ttf"


# ----------------------------------------------------------------------------- texto em curvas
def num(v):
    """Número curto para o SVG: uma casa decimal, sem zero sobrando."""
    s = f"{v:.1f}"
    if s.endswith(".0"):
        s = s[:-2]
    return "0" if s == "-0" else s


class Fonte:
    """Instância estática de uma fonte (variável ou não) que desenha texto como <path>."""

    def __init__(self, arquivo, **eixos):
        ttf = TTFont(arquivo)
        if "fvar" in ttf:
            local = {a.axisTag: float(eixos.get(a.axisTag, a.defaultValue)) for a in ttf["fvar"].axes}
            ttf = instancer.instantiateVariableFont(ttf, local)
        self.ttf = ttf
        self.upm = ttf["head"].unitsPerEm
        self.cmap = ttf.getBestCmap()
        self.glifos = ttf.getGlyphSet()
        self.avancos = ttf["hmtx"].metrics
        self._lookups = self._ler_kern_gpos()
        self._kern_antigo = {}
        if not self._lookups and "kern" in ttf:
            for tabela in ttf["kern"].kernTables:
                self._kern_antigo.update(getattr(tabela, "kernTable", {}))
        self.maiuscula = self.caixa_glifo(self.cmap[ord("H")])[3]

    def _ler_kern_gpos(self):
        if "GPOS" not in self.ttf:
            return []
        gpos = self.ttf["GPOS"].table
        indices = set()
        for registro in gpos.FeatureList.FeatureRecord if gpos.FeatureList else []:
            if registro.FeatureTag == "kern":
                indices.update(registro.Feature.LookupListIndex)
        lookups = []
        for i in sorted(indices):
            lookup = gpos.LookupList.Lookup[i]
            subtabelas = []
            for st in lookup.SubTable:
                if lookup.LookupType == 9:
                    if st.ExtensionLookupType != 2:
                        continue
                    st = st.ExtSubTable
                elif lookup.LookupType != 2:
                    continue
                subtabelas.append((st, set(st.Coverage.glyphs)))
            lookups.append(subtabelas)
        return lookups

    @functools.lru_cache(maxsize=None)
    def kern(self, a, b):
        """Ajuste de par (unidades da fonte) entre os glifos a e b."""
        if not self._lookups:
            return self._kern_antigo.get((a, b), 0)
        total = 0
        for subtabelas in self._lookups:
            for st, cobertura in subtabelas:
                if a not in cobertura:
                    continue
                if st.Format == 1:
                    conjunto = st.PairSet[st.Coverage.glyphs.index(a)]
                    valor = next((r.Value1 for r in conjunto.PairValueRecord if r.SecondGlyph == b), False)
                    if valor is False:
                        continue
                else:
                    c1 = st.ClassDef1.classDefs.get(a, 0)
                    c2 = st.ClassDef2.classDefs.get(b, 0)
                    valor = st.Class1Record[c1].Class2Record[c2].Value1
                total += (getattr(valor, "XAdvance", 0) or 0) if valor else 0
                break
        return total

    def caixa_glifo(self, nome):
        caneta = BoundsPen(self.glifos)
        self.glifos[nome].draw(caneta)
        return caneta.bounds or (0, 0, 0, 0)

    def nomes(self, texto):
        faltando = [c for c in texto if ord(c) not in self.cmap]
        if faltando:
            raise ValueError(f"glifo ausente: {faltando!r}")
        return [self.cmap[ord(c)] for c in texto]

    def tamanho_para_maiuscula(self, altura):
        """Tamanho de fonte que deixa a letra maiúscula com essa altura."""
        return altura * self.upm / self.maiuscula

    def medir(self, texto, tamanho, espaco=0.0):
        """Largura do texto (unidades do SVG), com kerning e espaçamento entre letras."""
        nomes = self.nomes(texto)
        esc = tamanho / self.upm
        largura = 0.0
        for i, n in enumerate(nomes):
            largura += self.avancos[n][0] * esc
            if i + 1 < len(nomes):
                largura += self.kern(n, nomes[i + 1]) * esc + espaco
        return largura

    def caminho(self, texto, x, y, tamanho, espaco=0.0, ancora="start"):
        """Devolve (d, largura): o texto inteiro num único atributo d, linha de base em y."""
        nomes = self.nomes(texto)
        esc = tamanho / self.upm
        largura = self.medir(texto, tamanho, espaco)
        if ancora == "middle":
            x -= largura / 2
        elif ancora == "end":
            x -= largura
        partes = []
        for i, n in enumerate(nomes):
            caneta = SVGPathPen(self.glifos, ntos=num)
            self.glifos[n].draw(TransformPen(caneta, (esc, 0, 0, -esc, x, y)))
            partes.append(caneta.getCommands())
            x += self.avancos[n][0] * esc
            if i + 1 < len(nomes):
                x += self.kern(n, nomes[i + 1]) * esc + espaco
        return "".join(partes), largura


@functools.lru_cache(maxsize=None)
def fonte(arquivo, **eixos):
    return Fonte(arquivo, **eixos)


def titulo_fonte():
    return fonte(MARTIAN, wght=800, wdth=112.5)


def mono_fonte():
    return fonte(MARTIAN, wght=600, wdth=100)


def corpo_fonte():
    return fonte(PLEX, wght=430, wdth=100)


# ----------------------------------------------------------------------------- paleta
FUNDO_A, FUNDO_B = "#0b1328", "#05080f"     # tinta: azul-noite para quase preto
BORDA = "#1c2a49"
PONTO_GRADE = "#25365a"
TILE_A, TILE_B, TILE_BORDA = "#121d38", "#0a1226", "#2b3d66"
TEXTO, TEXTO_SUAVE, TEXTO_APAGADO = "#f4f7ff", "#c5d0ea", "#8896b9"
CIANO, CIANO_CLARO = "#4cc9f0", "#c4f1ff"   # dado bruto (extração)
BRASA, BRASA_CLARA = "#ff8a5b", "#ffd2bf"   # dado transformado (a cor do Ignis)


# ----------------------------------------------------------------------------- geometria
W, H = 1200, 400
TAU = 1.5          # a cada TAU segundos chega um pacote em cada nó
VELOCIDADE = 92.0  # unidades do viewBox por segundo
PROCESSO = 0.3     # o nó "trabalha" esse tempo antes de soltar o pacote seguinte

NOS = {
    "erp": dict(x=80, y=120, tipo="banco"),
    "api": dict(x=80, y=220, tipo="api"),
    "csv": dict(x=80, y=320, tipo="planilha"),
    "etl": dict(x=300, y=320, tipo="engrenagens"),
    "dw": dict(x=600, y=320, tipo="dw", meio=32),
    "orq": dict(x=900, y=320, tipo="relogio"),
    "painel": dict(x=1120, y=120, tipo="painel"),
    "email": dict(x=1120, y=220, tipo="email"),
    "robo": dict(x=1120, y=320, tipo="robo"),
}
ARESTAS = [("erp", "etl"), ("api", "etl"), ("csv", "etl"), ("etl", "dw"), ("dw", "orq"),
           ("orq", "painel"), ("orq", "email"), ("orq", "robo")]
FONTES_DADO = {"erp", "api", "csv"}


def meio(no):
    return NOS[no].get("meio", 27)


def bezier(p, t):
    u = 1 - t
    return (u ** 3 * p[0][0] + 3 * u * u * t * p[1][0] + 3 * u * t * t * p[2][0] + t ** 3 * p[3][0],
            u ** 3 * p[0][1] + 3 * u * u * t * p[1][1] + 3 * u * t * t * p[2][1] + t ** 3 * p[3][1])


def comprimento(p, n=240):
    pts = [bezier(p, i / n) for i in range(n + 1)]
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def aresta(origem, destino):
    """Curva cúbica com tangentes horizontais, da porta de saída à porta de entrada."""
    a, b = NOS[origem], NOS[destino]
    x0, y0 = a["x"] + meio(origem), a["y"]
    x3, y3 = b["x"] - meio(destino), b["y"]
    k = (x3 - x0) / 2
    p = ((x0, y0), (x0 + k, y0), (x3 - k, y3), (x3, y3))
    d = f"M{num(x0)} {num(y0)}C{num(x0 + k)} {num(y0)} {num(x3 - k)} {num(y3)} {num(x3)} {num(y3)}"
    return p, d


def agenda():
    """Fase de chegada (s, dentro de TAU) em cada nó e a fase de saída de cada aresta.

    As três fontes soltam o pacote em momentos diferentes para que os três cheguem juntos às engrenagens;
    daí em diante cada nó solta o próximo pacote PROCESSO segundos depois de receber.
    """
    chegada, saida = {"etl": 0.0}, {}
    for o, d in ARESTAS:
        p, _ = aresta(o, d)
        dur = comprimento(p) / VELOCIDADE
        if o in FONTES_DADO:
            saida[(o, d)] = (chegada["etl"] - dur) % TAU
        else:
            saida[(o, d)] = (chegada[o] + PROCESSO) % TAU
            chegada[d] = (saida[(o, d)] + dur) % TAU
    return chegada, saida


# ----------------------------------------------------------------------------- ícones (traço 2.2)
def icone_banco(x, y, cor):
    rx, ry, h = 11, 4, 20
    t = y - h / 2
    return (f'<g fill="none" stroke="{cor}" stroke-width="2.2" stroke-linecap="round">'
            f'<ellipse cx="{x}" cy="{num(t)}" rx="{rx}" ry="{ry}"/>'
            f'<path d="M{x - rx} {num(t)}V{num(t + h)}A{rx} {ry} 0 0 0 {x + rx} {num(t + h)}V{num(t)}'
            f'M{x - rx} {num(t + h / 2)}A{rx} {ry} 0 0 0 {x + rx} {num(t + h / 2)}"/></g>')


def icone_api(x, y, cor):
    def chave(s):
        return (f"M{x + s * 5} {y - 11}C{x + s * 9} {y - 11} {x + s * 9} {y - 9} {x + s * 9} {y - 5}V{y - 3}"
                f"C{x + s * 9} {y - 1} {x + s * 10} {y} {x + s * 12} {y}C{x + s * 10} {y} {x + s * 9} {y + 1} "
                f"{x + s * 9} {y + 3}V{y + 5}C{x + s * 9} {y + 9} {x + s * 9} {y + 11} {x + s * 5} {y + 11}")
    return (f'<path d="{chave(-1)}{chave(1)}" fill="none" stroke="{cor}" stroke-width="2.2" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="{x}" cy="{y}" r="2" fill="{cor}"/>')


def icone_planilha(x, y, cor):
    return (f'<g fill="none" stroke="{cor}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="M{x - 9} {y - 12}H{x + 3}L{x + 10} {y - 5}V{y + 12}H{x - 9}Z"/>'
            f'<path d="M{x + 3} {y - 12}V{y - 5}H{x + 10}"/>'
            f'<path d="M{x - 5} {y}H{x + 6}M{x - 5} {y + 4.5}H{x + 6}M{x - 5} {y + 9}H{x + 1}"/></g>')


def engrenagem(cx, cy, dentes, r_ext, r_raiz, r_furo, fase):
    passo = 2 * math.pi / dentes
    pts = []
    for i in range(dentes):
        a = fase + i * passo
        for ang, r in ((a - passo * .29, r_raiz), (a - passo * .15, r_ext), (a + passo * .15, r_ext),
                       (a + passo * .29, r_raiz)):
            pts.append(f"{num(cx + r * math.cos(ang))} {num(cy + r * math.sin(ang))}")
    furo = (f"M{num(cx + r_furo)} {num(cy)}A{r_furo} {r_furo} 0 1 0 {num(cx - r_furo)} {num(cy)}"
            f"A{r_furo} {r_furo} 0 1 0 {num(cx + r_furo)} {num(cy)}Z")
    return "M" + "L".join(pts) + "Z" + furo


def icone_engrenagens(x, y, cor):
    """Par de engrenagens engatadas girando em sentidos opostos (a menor gira mais rápido)."""
    gx, gy, nd_g = x - 6, y + 5, 8
    ang = -math.pi / 4
    dist = (13 + 9.4) / 2 + (8.2 + 5.8) / 2
    px, py = gx + dist * math.cos(ang), gy + dist * math.sin(ang)
    nd_p = 6
    grande = engrenagem(gx, gy, nd_g, 13, 9.4, 4, ang)
    pequena = engrenagem(px, py, nd_p, 8.2, 5.8, 2.4, ang + math.pi + math.pi / nd_p)
    per_g = 8.0
    per_p = per_g * nd_p / nd_g
    return (f'<path class="gira" d="{grande}" fill="{cor}" fill-rule="evenodd" '
            f'style="transform-origin:{num(gx)}px {num(gy)}px;animation-duration:{per_g}s"/>'
            f'<path class="gira volta" d="{pequena}" fill="{cor}" fill-opacity=".8" fill-rule="evenodd" '
            f'style="transform-origin:{num(px)}px {num(py)}px;animation-duration:{num(per_p)}s"/>')


def disco_dw(x, y, i):
    """Face frontal do disco i (0 = topo) do data warehouse."""
    rx, ry, h, vao = 14, 4.2, 6.5, 4
    t = y - 15 + i * (h + vao)
    return f"M{x - rx} {num(t)}V{num(t + h)}A{rx} {ry} 0 0 0 {x + rx} {num(t + h)}V{num(t)}A{rx} {ry} 0 0 1 {x - rx} {num(t)}Z", t


def icone_dw(x, y):
    partes = []
    for i in range(3):
        d, t = disco_dw(x, y, i)
        partes.append(f'<path d="{d}" fill="url(#fluxoIcone)" fill-opacity=".14"/>'
                      f'<ellipse cx="{x}" cy="{num(t)}" rx="14" ry="4.2"/>')
    return (f'<g fill="none" stroke="url(#fluxoIcone)" stroke-width="2.2" stroke-linejoin="round">'
            + "".join(partes) + "</g>")


def icone_relogio(x, y, cor):
    marcas = "".join(f"M{num(x + 8.2 * math.cos(a))} {num(y + 8.2 * math.sin(a))}"
                     f"L{num(x + 10.4 * math.cos(a))} {num(y + 10.4 * math.sin(a))}"
                     for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2))
    return (f'<g fill="none" stroke="{cor}" stroke-width="2.2" stroke-linecap="round">'
            f'<circle cx="{x}" cy="{y}" r="13"/><path d="{marcas}" stroke-width="1.6"/>'
            f'<path class="gira" d="M{x} {y}V{y - 8}" style="transform-origin:{x}px {y}px;animation-duration:6s"/>'
            f'<path class="gira" d="M{x} {y}H{x + 5}" stroke-width="1.8" '
            f'style="transform-origin:{x}px {y}px;animation-duration:36s"/></g>'
            f'<circle cx="{x}" cy="{y}" r="2" fill="{cor}"/>')


def icone_painel(x, y, cor):
    barras = []
    for i, (alt, dur) in enumerate(((7, 2.1), (12, 2.7), (9, 1.8), (15, 3.1))):
        bx = x - 9.5 + i * 5.6
        barras.append(f'<rect class="barra" x="{num(bx)}" y="{y + 8 - alt}" width="3.6" height="{alt}" rx="1" '
                      f'fill="{cor}" style="animation-duration:{dur}s;animation-delay:-{i * .7:.1f}s"/>')
    return (f'<rect x="{x - 14}" y="{y - 12}" width="28" height="24" rx="4" fill="none" stroke="{cor}" '
            f'stroke-width="2.2"/>' + "".join(barras))


def icone_email(x, y, cor):
    return (f'<g fill="none" stroke="{cor}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
            f'<rect x="{x - 13}" y="{y - 9}" width="26" height="18" rx="3"/>'
            f'<path d="M{x - 11} {y - 6}L{x} {y + 2}L{x + 11} {y - 6}"/></g>')


def icone_robo(x, y, cor):
    return (f'<g fill="none" stroke="{cor}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
            f'<rect x="{x - 11}" y="{y - 6}" width="22" height="17" rx="5"/>'
            f'<path d="M{x} {y - 6}V{y - 10}M{x - 14} {y}V{y + 5}M{x + 14} {y}V{y + 5}M{x - 3} {y + 6}H{x + 3}"/></g>'
            f'<circle cx="{x}" cy="{y - 12}" r="2.2" fill="{cor}"/>'
            f'<g class="pisca"><circle cx="{x - 4.5}" cy="{y + 1}" r="2.3" fill="{cor}"/>'
            f'<circle cx="{x + 4.5}" cy="{y + 1}" r="2.3" fill="{cor}"/></g>')


ICONES = {"banco": icone_banco, "api": icone_api, "planilha": icone_planilha, "engrenagens": icone_engrenagens,
          "relogio": icone_relogio, "painel": icone_painel, "email": icone_email, "robo": icone_robo}


# ----------------------------------------------------------------------------- animação sincronizada
def negativo(fase, ciclo):
    """begin negativo: a animação já está rodando no instante 0, na fase pedida."""
    return f"{num((fase % ciclo) - ciclo)}s" if fase % ciclo else "0s"


def capsula(sufixo):
    """Pacote de dados: núcleo branco, cauda colorida e halo (gradiente, sem filtro de blur)."""
    return (f'<ellipse rx="20" ry="8" fill="url(#halo{sufixo})"/>'
            f'<rect x="-34" y="-1.7" width="30" height="3.4" rx="1.7" fill="url(#cauda{sufixo})"/>'
            f'<rect x="-6" y="-2.7" width="12" height="5.4" rx="2.7" fill="#fff"/>')


def pacotes_parados():
    """Com prefers-reduced-motion os pacotes param no meio de cada aresta (o desenho continua completo)."""
    partes = []
    for o, d in ARESTAS:
        p, _ = aresta(o, d)
        x, y = bezier(p, .5)
        x2, y2 = bezier(p, .51)
        ang = math.degrees(math.atan2(y2 - y, x2 - x))
        partes.append(f'<g transform="translate({num(x)} {num(y)}) rotate({num(ang)})">'
                      f'{capsula("C" if o in FONTES_DADO else "B")}</g>')
    return "".join(partes)


def pacote(d_path, p, saida, sufixo):
    """Pacotes de uma aresta: um a cada TAU, viajando à VELOCIDADE e sumindo ao entrar no nó."""
    dur = comprimento(p) / VELOCIDADE
    n = max(1, math.ceil(dur / TAU - 1e-6))
    ciclo = n * TAU
    f = dur / ciclo
    if f > .999:
        kp, kt = "0;1", "0;1"
        ov, ot = "0;1;1;0", f"0;{.06 / f:.3f};{1 - .06 / f:.3f};1"
    else:
        kp, kt = "0;1;1", f"0;{f:.4f};1"
        ov, ot = "0;1;1;0;0", f"0;{.06 * f:.4f};{.94 * f:.4f};{f:.4f};1"
    grupos = []
    for k in range(n):
        ini = negativo(saida + k * TAU, ciclo)
        comum = f'dur="{num(ciclo)}s" begin="{ini}" repeatCount="indefinite"'
        grupos.append(
            f'<g opacity="0">{capsula(sufixo)}'
            f'<animateMotion {comum} rotate="auto" calcMode="linear" keyPoints="{kp}" keyTimes="{kt}" path="{d_path}"/>'
            f'<animate attributeName="opacity" {comum} values="{ov}" keyTimes="{ot}"/></g>')
    return "".join(grupos)


def borda_acesa(x, y, meia, fase, cor):
    """A borda do nó fica na cor do dado por um instante quando o pacote chega."""
    ini = negativo(fase, TAU)
    return (f'<rect x="{x - meia}" y="{y - meia}" width="{2 * meia}" height="{2 * meia}" rx="{num(meia * .52)}" '
            f'fill="none" stroke="{cor}" stroke-width="1.6" opacity="0"><animate attributeName="opacity" '
            f'dur="{TAU}s" begin="{ini}" repeatCount="indefinite" values="1;.15;0" keyTimes="0;.55;1"/></rect>')


def pulso(x, y, meia, fase, cor, forte=True):
    """Anel que acende e se expande quando um pacote chega (ou sai, nas fontes)."""
    ini = negativo(fase, TAU)
    comum = f'dur="{TAU}s" begin="{ini}" repeatCount="indefinite"'
    alvo = 16 if forte else 9
    return (f'<rect x="{x - meia}" y="{y - meia}" width="{2 * meia}" height="{2 * meia}" rx="{num(meia * .52)}" '
            f'fill="none" stroke="{cor}" opacity="0">'
            f'<animate attributeName="opacity" {comum} values="{".85" if forte else ".5"};0;0" keyTimes="0;.6;1"/>'
            f'<animate attributeName="stroke-width" {comum} values="2;{alvo};{alvo}" keyTimes="0;.6;1"/></rect>')


# ----------------------------------------------------------------------------- banner
def defs_comuns():
    return f'''
    <linearGradient id="fundo" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{FUNDO_A}"/><stop offset="1" stop-color="{FUNDO_B}"/>
    </linearGradient>
    <linearGradient id="tile" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{TILE_A}"/><stop offset="1" stop-color="{TILE_B}"/>
    </linearGradient>
    <radialGradient id="haloC"><stop offset="0" stop-color="{CIANO}" stop-opacity=".75"/>
      <stop offset=".45" stop-color="{CIANO}" stop-opacity=".22"/><stop offset="1" stop-color="{CIANO}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="haloB"><stop offset="0" stop-color="{BRASA}" stop-opacity=".8"/>
      <stop offset=".45" stop-color="{BRASA}" stop-opacity=".24"/><stop offset="1" stop-color="{BRASA}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="caudaC" x1="0" x2="1"><stop offset="0" stop-color="{CIANO}" stop-opacity="0"/>
      <stop offset="1" stop-color="{CIANO_CLARO}"/></linearGradient>
    <linearGradient id="caudaB" x1="0" x2="1"><stop offset="0" stop-color="{BRASA}" stop-opacity="0"/>
      <stop offset="1" stop-color="{BRASA_CLARA}"/></linearGradient>'''


def tile(no):
    n = NOS[no]
    x, y, m = n["x"], n["y"], meio(no)
    return (f'<rect x="{x - m}" y="{y - m}" width="{2 * m}" height="{2 * m}" rx="{num(m * .52)}" '
            f'fill="url(#tile)" stroke="{TILE_BORDA}" stroke-width="1.4"/>'
            f'<path d="M{x - m + 10} {y - m + .9}H{x + m - 10}" stroke="#ffffff" stroke-opacity=".09" stroke-width="1.2"/>')


def cor_no(no):
    if no in FONTES_DADO:
        return CIANO
    return BRASA


def portas(no, entra, sai):
    n = NOS[no]
    m, partes = meio(no), []
    cor = cor_no(no)
    if entra:
        partes.append(f'<circle cx="{n["x"] - m}" cy="{n["y"]}" r="3.6" fill="{FUNDO_B}" stroke="{cor}" stroke-width="1.6"/>')
    if sai:
        partes.append(f'<circle cx="{n["x"] + m}" cy="{n["y"]}" r="3.6" fill="{cor}"/>')
    return "".join(partes)


def subtitulo(y, altura_maiuscula):
    """ENGENHARIA DE DADOS · AUTOMAÇÃO · ETL, com os pontos desenhados como portas de pipeline."""
    f = mono_fonte()
    tam = f.tamanho_para_maiuscula(altura_maiuscula)
    esp = tam * .16
    blocos = ["ENGENHARIA DE DADOS", "AUTOMAÇÃO", "ETL"]
    sep = 54  # largura de cada separador
    larguras = [f.medir(b, tam, esp) for b in blocos]
    total = sum(larguras) + sep * (len(blocos) - 1)
    x = (W - total) / 2
    caminhos, seps = [], []
    for i, (b, lw) in enumerate(zip(blocos, larguras)):
        d, _ = f.caminho(b, x, y, tam, esp)
        caminhos.append(d)
        x += lw
        if i + 1 < len(blocos):
            cx, cy = x + sep / 2, y - altura_maiuscula / 2
            cor = CIANO if i == 0 else BRASA
            seps.append(f'<rect x="{num(cx - 4)}" y="{num(cy - 4)}" width="8" height="8" rx="1.5" fill="{cor}" '
                        f'transform="rotate(45 {num(cx)} {num(cy)})"/>')
            x += sep
    return (f'<path d="{"".join(caminhos)}" fill="{TEXTO_SUAVE}"/>' + "".join(seps)), total


def banner():
    f = titulo_fonte()
    cap = 112
    tam = f.tamanho_para_maiuscula(cap)
    base = 178
    d_nome, larg_nome = f.caminho("VERDER", W / 2, base, tam, espaco=tam * .05, ancora="middle")
    sub, larg_sub = subtitulo(230, 18.5)

    chegada, saida = agenda()
    arestas_svg, pacotes_svg = [], []
    for o, d in ARESTAS:
        p, dd = aresta(o, d)
        arestas_svg.append(dd)
        pacotes_svg.append(pacote(dd, p, saida[(o, d)], "C" if o in FONTES_DADO else "B"))
    todas = "".join(arestas_svg)

    pulsos, tiles, icones, extras = [], [], [], []
    for no, n in NOS.items():
        x, y, m = n["x"], n["y"], meio(no)
        cor = cor_no(no)
        if no in FONTES_DADO:
            pulsos.append(pulso(x, y, m, saida[(no, "etl")], CIANO, forte=False))
        else:
            pulsos.append(pulso(x, y, m, chegada[no], cor))
            extras.append(borda_acesa(x, y, m, chegada[no], cor))
        tiles.append(tile(no))
        if n["tipo"] == "dw":
            icones.append(icone_dw(x, y))
        else:
            icones.append(ICONES[n["tipo"]](x, y, cor))
        icones.append(portas(no, entra=no not in FONTES_DADO, sai=no not in ("painel", "email", "robo")))

    # luzes do DW: os discos acendem de baixo para cima quando a carga chega
    for i in range(3):
        d, _ = disco_dw(NOS["dw"]["x"], NOS["dw"]["y"], 2 - i)
        ini = negativo(chegada["dw"] + i * .14, TAU)
        extras.append(f'<path d="{d}" fill="url(#fluxoIcone)" opacity="0"><animate attributeName="opacity" '
                      f'dur="{TAU}s" begin="{ini}" repeatCount="indefinite" values="0;.85;.12;0" '
                      f'keyTimes="0;.12;.6;1"/></path>')
    # e-mail: selo de mensagem nova; robô: antena acende
    ex, ey = NOS["email"]["x"], NOS["email"]["y"]
    extras.append(f'<circle cx="{ex + 13}" cy="{ey - 9}" r="4.4" fill="{BRASA}" stroke="{TILE_B}" stroke-width="2" '
                  f'opacity="0"><animate attributeName="opacity" dur="{TAU}s" begin="{negativo(chegada["email"], TAU)}" '
                  f'repeatCount="indefinite" values="1;1;0;0" keyTimes="0;.55;.75;1"/></circle>')
    rx_, ry_ = NOS["robo"]["x"], NOS["robo"]["y"]
    extras.append(f'<circle cx="{rx_}" cy="{ry_ - 12}" r="6" fill="url(#haloB)" opacity="0">'
                  f'<animate attributeName="opacity" dur="{TAU}s" begin="{negativo(chegada["robo"], TAU)}" '
                  f'repeatCount="indefinite" values="1;0;0" keyTimes="0;.6;1"/></circle>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="titulo descricao">
  <title id="titulo">VERDER · engenharia de dados, automação e ETL</title>
  <desc id="descricao">O nome VERDER em letras grossas sobre um pipeline de dados em movimento: banco, API e planilha alimentam um par de engrenagens, que carrega o data warehouse; dele um orquestrador entrega pacotes a um painel, a um e-mail e a um robô. Cada nó pulsa quando um pacote chega.</desc>
  <defs>{defs_comuns()}
    <linearGradient id="nomeCor" x1="0" y1="{base - cap}" x2="0" y2="{base}" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#c3cfec"/>
    </linearGradient>
    <linearGradient id="fluxo" x1="100" y1="0" x2="1100" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{CIANO}"/><stop offset=".22" stop-color="{CIANO}"/>
      <stop offset=".5" stop-color="#b9b3ff"/><stop offset=".78" stop-color="{BRASA}"/><stop offset="1" stop-color="{BRASA}"/>
    </linearGradient>
    <linearGradient id="fluxoIcone" x1="584" y1="0" x2="616" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{CIANO}"/><stop offset="1" stop-color="{BRASA}"/>
    </linearGradient>
    <linearGradient id="brilho" x1="0" x2="1">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".9"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="luzC" cx="210" cy="190" r="330" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{CIANO}" stop-opacity=".16"/><stop offset="1" stop-color="{CIANO}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="luzB" cx="990" cy="190" r="330" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{BRASA}" stop-opacity=".14"/><stop offset="1" stop-color="{BRASA}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="luzNome" cx="600" cy="130" r="430" gradientTransform="translate(0 78) scale(1 .4)" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#3a4f8f" stop-opacity=".45"/><stop offset="1" stop-color="#3a4f8f" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grade" width="20" height="20" patternUnits="userSpaceOnUse">
      <circle cx="0" cy="0" r="1.1" fill="{PONTO_GRADE}"/><circle cx="20" cy="0" r="1.1" fill="{PONTO_GRADE}"/>
      <circle cx="0" cy="20" r="1.1" fill="{PONTO_GRADE}"/><circle cx="20" cy="20" r="1.1" fill="{PONTO_GRADE}"/>
    </pattern>
    <radialGradient id="mascaraGrade" cx="600" cy="200" r="640" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#fff" stop-opacity=".9"/><stop offset=".75" stop-color="#fff" stop-opacity=".55"/>
      <stop offset="1" stop-color="#fff" stop-opacity=".15"/>
    </radialGradient>
    <mask id="fadeGrade"><rect width="{W}" height="{H}" fill="url(#mascaraGrade)"/></mask>
    <path id="nome" d="{d_nome}"/>
    <clipPath id="recorteNome"><use href="#nome"/></clipPath>
    <clipPath id="quadro"><rect width="{W}" height="{H}" rx="18"/></clipPath>
  </defs>
  <style>
    .gira{{animation:gira 8s linear infinite}}
    .volta{{animation-name:volta}}
    @keyframes gira{{to{{transform:rotate(360deg)}}}}
    @keyframes volta{{to{{transform:rotate(-360deg)}}}}
    .fluxo{{stroke-dasharray:1.6 10.4;animation:flui 1.2s linear infinite}}
    @keyframes flui{{to{{stroke-dashoffset:-12}}}}
    .barra{{transform-box:fill-box;transform-origin:50% 100%;animation:barra 2s ease-in-out infinite alternate}}
    @keyframes barra{{from{{transform:scaleY(.4)}}to{{transform:scaleY(1)}}}}
    .pisca{{transform-box:fill-box;transform-origin:center;animation:pisca 4.6s infinite}}
    @keyframes pisca{{0%,90%,100%{{transform:scaleY(1)}}94%{{transform:scaleY(.12)}}}}
    .varre{{animation:varre 8s cubic-bezier(.5,0,.3,1) infinite}}
    @keyframes varre{{0%{{transform:translateX(0)}}24%,100%{{transform:translateX(1000px)}}}}
    .respira{{animation:respira 7s ease-in-out infinite alternate}}
    .respira.b{{animation-duration:9s;animation-direction:alternate-reverse}}
    @keyframes respira{{from{{opacity:.55}}to{{opacity:1}}}}
    .parado{{display:none}}
    @media (prefers-reduced-motion:reduce){{
      *{{animation:none!important}}
      .vivo{{display:none}}
      .parado{{display:inline}}
    }}
  </style>
  <g clip-path="url(#quadro)">
    <rect width="{W}" height="{H}" fill="url(#fundo)"/>
    <rect class="respira" width="{W}" height="{H}" fill="url(#luzC)"/>
    <rect class="respira b" width="{W}" height="{H}" fill="url(#luzB)"/>
    <rect width="{W}" height="{H}" fill="url(#luzNome)"/>
    <rect width="{W}" height="{H}" fill="url(#grade)" mask="url(#fadeGrade)"/>
    <g fill="none" stroke-linecap="round">
      <path d="{todas}" stroke="{FUNDO_B}" stroke-width="8"/>
      <path d="{todas}" stroke="url(#fluxo)" stroke-opacity=".38" stroke-width="2"/>
      <path class="fluxo" d="{todas}" stroke="url(#fluxo)" stroke-opacity=".9" stroke-width="2"/>
    </g>
    <g class="vivo">{"".join(pulsos)}</g>
    <g class="vivo">{"".join(pacotes_svg)}</g>
    <g class="parado">{pacotes_parados()}</g>
    {"".join(tiles)}
    {"".join(icones)}
    <g class="vivo">{"".join(extras)}</g>
    <use href="#nome" transform="translate(0 6)" fill="#02040a" opacity=".6"/>
    <use href="#nome" fill="url(#nomeCor)"/>
    <g clip-path="url(#recorteNome)"><g class="varre"><rect x="90" y="40" width="130" height="160" fill="url(#brilho)" opacity=".55" transform="skewX(-18)"/></g></g>
    {sub}
  </g>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="17.5" fill="none" stroke="{BORDA}"/>
</svg>
'''
    return svg, larg_nome, larg_sub


def main():
    svg, larg_nome, larg_sub = banner()
    destino = AQUI.parent / "assets" / "banner.svg"
    destino.write_text(svg, encoding="utf-8")
    print(f"{destino.name}: {len(svg.encode()) / 1024:.1f} KB | nome {larg_nome:.0f} | subtítulo {larg_sub:.0f}")


if __name__ == "__main__":
    main()
