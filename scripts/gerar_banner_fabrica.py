"""Gera assets/banner.svg (1200 x 400) no tema "fábrica de dados".

Cena: o silo ERP despeja registros brutos na esteira, o braço robótico pega cada um, transforma
e devolve à esteira, que leva os blocos tratados para o armazém DW. Tudo é SVG puro: o texto vira
contorno (path) a partir da fonte Tektur, então nada depende de fonte instalada.

Uso: python -m pip install fonttools && python scripts/gerar_banner_fabrica.py
A animação roda sempre (sem a trava de movimento reduzido), a pedido do dono do perfil.
"""
import math
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

PASTA = Path(__file__).resolve().parent
TEKTUR = PASTA / "fontes" / "tektur" / "Tektur[wdth,wght].ttf"   # licença OFL (OFL.txt na mesma pasta)

W, H = 1200, 400
T = 3.0            # ciclo do robô e da esteira (s)
P = 84             # passo entre blocos na esteira
V = P / T          # velocidade da esteira (unidades por segundo)

COR = {
    "parede1": "#111b2f", "parede2": "#0b1221", "piso": "#0a101c",
    "aco0": "#121a2b", "aco1": "#18223a", "aco2": "#223050", "aco3": "#2e4068", "aco4": "#3f5682",
    "aco5": "#5873a3", "brasa": "#ff8a5b", "brasa2": "#e8693c", "brasa3": "#b8481f", "brasa4": "#7c2e12",
    "brasa_clara": "#ffc2a6", "dado": "#2dd4bf", "dado2": "#14a191", "dado3": "#0b6c62",
    "dado_claro": "#a2f7ea", "bruto": "#8089b8", "bruto2": "#5d6694", "bruto3": "#b3bae0",
    "texto": "#e9eff9", "listra": "#0d1424",
}


def n(v, casas=1):
    s = f"{v:.{casas}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ---------------------------------------------------------------- fonte -> contorno

def _lookups_kern(fonte):
    if "GPOS" not in fonte:
        return []
    gpos = fonte["GPOS"].table
    idx = set()
    for reg in gpos.FeatureList.FeatureRecord:
        if reg.FeatureTag == "kern":
            idx.update(reg.Feature.LookupListIndex)
    saida = []
    for i in sorted(idx):
        lk = gpos.LookupList.Lookup[i]
        subs = []
        for st in lk.SubTable:
            tipo = lk.LookupType
            if tipo == 9:
                tipo, st = st.ExtensionLookupType, st.ExtSubTable
            if tipo == 2:
                subs.append(st)
        saida.append(subs)
    return saida


def _xadv(valor):
    return (getattr(valor, "XAdvance", 0) or 0) if valor is not None else 0


class Fonte:
    """Instância fixa de uma fonte variável, com avanço e kerning (GPOS PairPos 1 e 2)."""

    def __init__(self, caminho, eixos, chave):
        f = TTFont(caminho)
        if "fvar" in f:
            valores = {a.axisTag: a.defaultValue for a in f["fvar"].axes}
            valores.update(eixos)
            f = instantiateVariableFont(f, valores)
        self.chave = chave
        self.upm = f["head"].unitsPerEm
        self.cmap = f.getBestCmap()
        self.gs = f.getGlyphSet()
        self.hmtx = f["hmtx"]
        self.cap = f["OS/2"].sCapHeight
        self.lookups = _lookups_kern(f)

    def glifo(self, c):
        return self.cmap[ord(c)]

    def kern(self, g1, g2):
        total = 0
        for subs in self.lookups:
            for st in subs:
                cob = st.Coverage.glyphs
                if g1 not in cob:
                    continue
                if st.Format == 1:
                    reg = next((r for r in st.PairSet[cob.index(g1)].PairValueRecord if r.SecondGlyph == g2), None)
                    if reg is None:
                        continue
                    total += _xadv(reg.Value1)
                    break
                if st.Format == 2:
                    c1 = st.ClassDef1.classDefs.get(g1, 0)
                    c2 = st.ClassDef2.classDefs.get(g2, 0)
                    total += _xadv(st.Class1Record[c1].Class2Record[c2].Value1)
                    break
        return total

    def tamanho_para_cap(self, cap):
        return cap * self.upm / self.cap

    def posicoes(self, texto, tam, espaco=0.0):
        """Lista (glifo, x) a partir de x=0 e a largura total."""
        s = tam / self.upm
        x, ant, saida = 0.0, None, []
        for c in texto:
            g = self.glifo(c)
            if ant is not None:
                x += self.kern(ant, g) * s + espaco
            saida.append((g, x))
            x += self.hmtx[g][0] * s
            ant = g
        return saida, x

    def contorno(self, g, tam, x=0.0, base=0.0):
        s = tam / self.upm
        pen = SVGPathPen(self.gs, ntos=n)
        self.gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x, base)))
        return pen.getCommands()

    def caminho(self, texto, tam, x, base, espaco=0.0, ancora="start"):
        pos, larg = self.posicoes(texto, tam, espaco)
        x0 = x - (larg / 2 if ancora == "middle" else larg if ancora == "end" else 0)
        return "".join(self.contorno(g, tam, x0 + gx, base) for g, gx in pos), larg


class Glifos:
    """Cada glifo vira um <path> em <defs>, reaproveitado com <use> (texto repetido custa pouco)."""

    def __init__(self, prefixo):
        self.prefixo = prefixo
        self.ids = {}
        self.defs = []

    def escrever(self, fonte, tam, texto, x, base, espaco=0.0, ancora="start"):
        pos, larg = fonte.posicoes(texto, tam, espaco)
        x0 = x - (larg / 2 if ancora == "middle" else larg if ancora == "end" else 0)
        usos = []
        for g, gx in pos:
            chave = (fonte.chave, round(tam, 2), g)
            if chave not in self.ids:
                d = fonte.contorno(g, tam)
                gid = f"{self.prefixo}{len(self.ids)}"
                self.ids[chave] = gid if d else None
                if d:
                    self.defs.append(f'<path id="{gid}" d="{d}"/>')
            gid = self.ids[chave]
            if gid:
                usos.append(f'<use href="#{gid}" x="{n(x0 + gx)}" y="{n(base)}"/>')
        return "".join(usos), larg


# ---------------------------------------------------------------- peças de desenho

def poli(pts):
    return "M" + "L".join(f"{n(x)} {n(y)}" for x, y in pts) + "Z"


def bloco(cor_frente, cor_topo, cor_lado, marcas, w=28, h=24, d=8):
    """Bloco 2.5D com a base da face frontal centrada em (0,0); profundidade sobe para a direita."""
    m = w / 2
    return (f'<path d="{poli([(-m, -h), (m, -h), (m + d, -h - d), (-m + d, -h - d)])}" fill="{cor_topo}"/>'
            f'<path d="{poli([(m, -h), (m + d, -h - d), (m + d, -d), (m, 0)])}" fill="{cor_lado}"/>'
            f'<rect x="{-m}" y="{-h}" width="{w}" height="{h}" fill="{cor_frente}"/>' + marcas)


def engrenagem(dentes, modulo, furo, raios=5):
    rp = modulo * dentes / 2
    rt, rr = rp + modulo, rp - 1.2 * modulo
    passo = 2 * math.pi / dentes
    pts = []
    for i in range(dentes):
        a = i * passo
        for frac, r in ((-0.27, rr), (-0.13, rt), (0.13, rt), (0.27, rr)):
            pts.append((r * math.cos(a + frac * passo), r * math.sin(a + frac * passo)))
    d = poli(pts)
    d += f"M{n(furo)} 0A{n(furo)} {n(furo)} 0 1 0 {n(-furo)} 0A{n(furo)} {n(furo)} 0 1 0 {n(furo)} 0Z"
    rj, rc = (rr - furo) * 0.32, furo + (rr - furo) * 0.5
    for k in range(raios):
        a = k * 2 * math.pi / raios + math.pi / raios
        cx, cy = rc * math.cos(a), rc * math.sin(a)
        d += (f"M{n(cx + rj)} {n(cy)}A{n(rj)} {n(rj)} 0 1 0 {n(cx - rj)} {n(cy)}"
              f"A{n(rj)} {n(rj)} 0 1 0 {n(cx + rj)} {n(cy)}Z")
    return d, rp, rt


# ---------------------------------------------------------------- robô: cinemática

OMBRO = (600, 250)      # pivô do ombro no mundo
L1, L2 = 56, 58         # braço e antebraço
ALCANCE = 84            # distância horizontal do ombro até o ponto de pega / entrega
Y_BAIXO, Y_ALTO = 16, -28   # punho relativo ao ombro: na esteira e erguido
PEGA = OMBRO[0] - ALCANCE   # x onde o bloco bruto é pego
ENTREGA = OMBRO[0] + ALCANCE  # x onde o bloco tratado é devolvido
U_SOLTA = 0.58          # fração do ciclo em que o bloco é solto na esteira


def suave(u):
    u = min(1.0, max(0.0, u))
    return u * u * u * (u * (6 * u - 15) + 10)


def estado_robo(u):
    """(guinada em graus, y do punho relativo ao ombro, abertura da garra 0..1) na fração u do ciclo."""
    fases = [
        (0.00, 0.06, ("pega",)), (0.06, 0.20, ("sobe", 180)), (0.20, 0.46, ("gira", 180, 0)),
        (0.46, U_SOLTA, ("desce", 0)), (U_SOLTA, 0.63, ("solta",)), (0.63, 0.73, ("sobe", 0)),
        (0.73, 0.92, ("gira", 0, 180)), (0.92, 1.0, ("desce", 180)),
    ]
    for a, b, f in fases:
        if a <= u <= b:
            k = suave((u - a) / (b - a))
            if f[0] == "pega":
                return 180, Y_BAIXO, 1 - k
            if f[0] == "sobe":
                return f[1], Y_BAIXO + (Y_ALTO - Y_BAIXO) * k, 0 if f[1] == 180 else 1
            if f[0] == "gira":
                return f[1] + (f[2] - f[1]) * k, Y_ALTO, 0 if f[1] == 180 else 1
            if f[0] == "desce":
                return f[1], Y_ALTO + (Y_BAIXO - Y_ALTO) * k, 0 if f[1] == 0 else 1
            if f[0] == "solta":
                return 0, Y_BAIXO, k
    return 180, Y_BAIXO, 1


def ik(x, y):
    """Ângulos (graus, sentido do SVG) do ombro e do cotovelo com o cotovelo para cima."""
    d = math.hypot(x, y)
    fi = math.atan2(y, x)
    alfa = math.acos((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))
    t1 = fi - alfa
    ex, ey = L1 * math.cos(t1), L1 * math.sin(t1)
    t2 = math.atan2(y - ey, x - ex) - t1
    return math.degrees(t1), math.degrees(t2)


def simplificar(amostras, tol):
    """Remove quadros-chave que a interpolação linear dos vizinhos já reproduz (erro < tol)."""
    manter = [0, len(amostras) - 1]

    def rec(i, j):
        if j <= i + 1:
            return
        ui, vi = amostras[i]
        uj, vj = amostras[j]
        pior, k_pior = 0.0, None
        for k in range(i + 1, j):
            uk, vk = amostras[k]
            f = (uk - ui) / (uj - ui)
            erro = max(abs(vk[c] - (vi[c] + (vj[c] - vi[c]) * f)) for c in range(len(vk)))
            if erro > pior:
                pior, k_pior = erro, k
        if pior > tol:
            manter.append(k_pior)
            rec(i, k_pior)
            rec(k_pior, j)

    rec(0, len(amostras) - 1)
    return [amostras[i] for i in sorted(set(manter))]


def quadros(nome, amostras, tol, fmt):
    pts = simplificar(amostras, tol)
    corpo = "".join(f"{n(u * 100, 2)}%{{transform:{fmt(v)}}}" for u, v in pts)
    return f"@keyframes {nome}{{{corpo}}}"


def animacao_robo():
    passos = 240
    guinada, ombro, cotovelo, garra, dedos = [], [], [], [], []
    for i in range(passos + 1):
        u = i / passos
        psi, y, abre = estado_robo(u)
        sx = math.cos(math.radians(psi))
        a1, a2 = ik(ALCANCE, y)
        guinada.append((u, (sx,)))
        ombro.append((u, (a1,)))
        cotovelo.append((u, (a2,)))
        garra.append((u, (OMBRO[0] + sx * ALCANCE, OMBRO[1] + y)))
        dedos.append((u, (abre * 5,)))
    css = [
        quadros("gu", guinada, 0.004, lambda v: f"scaleX({n(v[0], 3)})"),
        quadros("om", ombro, 0.15, lambda v: f"rotate({n(v[0], 2)}deg)"),
        quadros("co", cotovelo, 0.15, lambda v: f"rotate({n(v[0], 2)}deg)"),
        quadros("ga", garra, 0.15, lambda v: f"translate({n(v[0], 2)}px,{n(v[1], 2)}px)"),
        quadros("de", dedos, 0.05, lambda v: f"translateX({n(-v[0], 2)}px)"),
        quadros("dd", dedos, 0.05, lambda v: f"translateX({n(v[0], 2)}px)"),
    ]
    # pose parada (sem animação / movimento reduzido): erguido na metade do giro, bloco já tratado
    psi, y, _ = estado_robo(0.40)
    sx = math.cos(math.radians(psi))
    a1, a2 = ik(ALCANCE, y)
    pose = (f".gu{{transform:scaleX({n(sx, 3)})}}.om{{transform:rotate({n(a1, 2)}deg)}}"
            f".co{{transform:rotate({n(a2, 2)}deg)}}"
            f".ga{{transform:translate({n(OMBRO[0] + sx * ALCANCE, 2)}px,{n(OMBRO[1] + y, 2)}px)}}")
    return "".join(css), pose


# ---------------------------------------------------------------- banner

class Banner:
    def __init__(self):
        self.tk900 = Fonte(TEKTUR, {"wght": 900, "wdth": 100}, "a")
        self.tk700 = Fonte(TEKTUR, {"wght": 700, "wdth": 85}, "b")
        self.glifos = Glifos("g")
        self.defs = []

    # -- fundo ----------------------------------------------------------------
    def fundo(self):
        c = COR
        self.defs.append(
            f'<linearGradient id="parede" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c["parede1"]}"/>'
            f'<stop offset="1" stop-color="{c["parede2"]}"/></linearGradient>'
            f'<radialGradient id="luzPlaca" cx="600" cy="120" r="430" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="{c["brasa"]}" stop-opacity=".16"/>'
            f'<stop offset="1" stop-color="{c["brasa"]}" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="luzDw" cx="1100" cy="190" r="230" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="{c["dado"]}" stop-opacity=".13"/>'
            f'<stop offset="1" stop-color="{c["dado"]}" stop-opacity="0"/></radialGradient>'
            f'<pattern id="pontos" width="24" height="24" patternUnits="userSpaceOnUse">'
            f'<circle cx="12" cy="12" r="1" fill="#2b3b5e"/></pattern>'
            f'<clipPath id="quadro"><rect width="{W}" height="{H}" rx="18"/></clipPath>')
        return (f'<rect width="{W}" height="{H}" fill="url(#parede)"/>'
                f'<rect width="{W}" height="368" fill="url(#pontos)" opacity=".55"/>'
                f'<rect width="{W}" height="{H}" fill="url(#luzPlaca)"/>'
                f'<rect width="{W}" height="{H}" fill="url(#luzDw)"/>'
                f'<rect y="368" width="{W}" height="32" fill="{c["piso"]}"/>'
                f'<rect y="368" width="{W}" height="1.5" fill="#26365a"/>'
                f'<rect y="386" width="{W}" height="2" fill="{c["brasa"]}" opacity=".22"/>')

    # -- placa ROCHA + subtítulo --------------------------------------------
    def placa(self):
        c = COR
        cap = 104
        tam = self.tk900.tamanho_para_cap(cap)
        base = 136
        d, larg = self.tk900.caminho("ROCHA", tam, 600, base, espaco=4, ancora="middle")
        self.defs.append(f'<path id="vd" d="{d}"/>')
        self.defs.append(
            f'<linearGradient id="face" x1="0" y1="{base - cap}" x2="0" y2="{base}" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="#ffffff"/><stop offset=".6" stop-color="#fff1e8"/>'
            f'<stop offset="1" stop-color="#ffd2bd"/></linearGradient>'
            f'<linearGradient id="brilho" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
            f'<stop offset=".5" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>'
            f'</linearGradient>'
            f'<clipPath id="recorteVd"><use href="#vd"/></clipPath>'
            f'<filter id="desfoque" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="18"/></filter>')
        prof = []
        passos = 9
        for k in range(passos, 0, -1):
            t = k / passos
            cor = _mistura(c["brasa2"], c["brasa4"], t)
            prof.append(f'<use href="#vd" x="{n(k * 1.05)}" y="{n(-k * 1.05)}" fill="{cor}"/>')
        letras = (f'<use href="#vd" x="6" y="10" fill="#000" opacity=".45" filter="url(#desfoque)"/>'
                  + "".join(prof)
                  + f'<use href="#vd" fill="url(#face)"/>'
                  + f'<g clip-path="url(#recorteVd)"><rect class="bri" x="200" y="20" width="70" height="130" '
                    f'fill="url(#brilho)" transform="skewX(-18)" opacity=".75"/></g>')
        # placa do subtítulo
        sub_tam = self.tk700.tamanho_para_cap(24)
        partes = ["ENGENHARIA DE DADOS", "AUTOMAÇÃO", "ETL"]
        sep = 26
        larguras = [self.tk700.posicoes(p, sub_tam, 1.2)[1] for p in partes]
        total = sum(larguras) + sep * 2
        y0, alt = 148, 40
        pad = 34
        x0 = 600 - total / 2 - pad
        larg_placa = total + 2 * pad
        base_sub = y0 + alt / 2 + 12
        textos, x = [], 600 - total / 2
        losangos = []
        for i, (p, lw) in enumerate(zip(partes, larguras)):
            usos, _ = self.glifos.escrever(self.tk700, sub_tam, p, x, base_sub, 1.2)
            textos.append(usos)
            x += lw
            if i < len(partes) - 1:
                cx, cy = x + sep / 2, y0 + alt / 2
                losangos.append(f'<path d="M{n(cx)} {n(cy - 5)}l5 5-5 5-5-5z" fill="{c["brasa"]}"/>')
                x += sep
        listras = self._listras(x0 + 4, y0 + 4, 18, alt - 8) + self._listras(x0 + larg_placa - 22, y0 + 4, 18, alt - 8)
        parafusos = "".join(f'<circle cx="{n(px)}" cy="{n(py)}" r="1.8" fill="{c["aco5"]}"/>'
                            for px in (x0 + 28, x0 + larg_placa - 28) for py in (y0 + 8, y0 + alt - 8))
        placa = (f'<path d="{poli([(x0, y0), (x0 + larg_placa, y0), (x0 + larg_placa + 6, y0 - 6), (x0 + 6, y0 - 6)])}" '
                 f'fill="{c["aco3"]}"/>'
                 f'<path d="{poli([(x0 + larg_placa, y0), (x0 + larg_placa + 6, y0 - 6), (x0 + larg_placa + 6, y0 + alt - 6), (x0 + larg_placa, y0 + alt)])}" '
                 f'fill="{c["aco0"]}"/>'
                 f'<rect x="{n(x0)}" y="{y0}" width="{n(larg_placa)}" height="{alt}" fill="{c["aco1"]}"/>'
                 f'<rect x="{n(x0)}" y="{y0}" width="{n(larg_placa)}" height="1.5" fill="{c["aco4"]}"/>'
                 + listras + parafusos +
                 f'<g fill="{c["texto"]}">{"".join(textos)}</g>' + "".join(losangos))
        return f'<g id="placa">{placa}{letras}</g>', larg

    def _listras(self, x, y, w, h):
        pid = f"lst{len(self.defs)}"
        self.defs.append(f'<clipPath id="{pid}"><rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}"/></clipPath>')
        faixas = "".join(f'<path d="M{n(x + i * 10)} {n(y + h)}l{n(h)} {n(-h)}h5l{n(-h)} {n(h)}z"/>'
                         for i in range(-4, int(w / 10) + 2))
        return (f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" fill="{COR["listra"]}"/>'
                f'<g clip-path="url(#{pid})" fill="{COR["brasa"]}">{faixas}</g>')

    # -- silo ERP -------------------------------------------------------------
    def silo(self):
        c = COR
        cx, x0, x1 = 96, 34, 158
        topo, corpo_fim, saida = 98, 226, 258
        self.defs.append(
            f'<linearGradient id="cil" x1="0" x2="1"><stop offset="0" stop-color="{c["aco1"]}"/>'
            f'<stop offset=".35" stop-color="{c["aco4"]}"/><stop offset=".7" stop-color="{c["aco2"]}"/>'
            f'<stop offset="1" stop-color="{c["aco0"]}"/></linearGradient>')
        rx, ry = (x1 - x0) / 2, 12
        faixas = "".join(
            f'<path d="M{x0} {y}A{n(rx)} {ry} 0 0 0 {x1} {y}" fill="none" stroke="{c["aco0"]}" stroke-width="3"/>'
            f'<path d="M{x0} {y + 3}A{n(rx)} {ry} 0 0 0 {x1} {y + 3}" fill="none" stroke="{c["aco5"]}" stroke-width="1" opacity=".5"/>'
            for y in (142, 186))
        rot, _ = self.glifos.escrever(self.tk900, self.tk900.tamanho_para_cap(15), "ERP", cx, 172, 1.5, "middle")
        pernas = "".join(f'<rect x="{px}" y="{corpo_fim - 6}" width="6" height="{368 - corpo_fim + 6}" fill="{c["aco2"]}"/>'
                         for px in (40, 146))
        corpo = (
            f'<path d="M{x0} {topo}V{corpo_fim}L{cx - 20} {saida}H{cx + 20}L{x1} {corpo_fim}V{topo}Z" fill="url(#cil)"/>'
            f'<ellipse cx="{cx}" cy="{topo}" rx="{n(rx)}" ry="{ry}" fill="{c["aco4"]}"/>'
            f'<ellipse cx="{cx}" cy="{topo}" rx="{n(rx - 8)}" ry="{ry - 4}" fill="{c["aco3"]}"/>'
            f'<path d="M{x0} {corpo_fim}A{n(rx)} {ry} 0 0 0 {x1} {corpo_fim}" fill="none" stroke="{c["aco0"]}" stroke-width="2"/>'
            + faixas +
            f'<rect x="{cx - 28}" y="{159}" width="56" height="19" rx="3" fill="{c["aco0"]}"/>'
            f'<g fill="{c["bruto3"]}">{rot}</g>'
            f'<rect x="{cx - 22}" y="{saida}" width="44" height="10" rx="2" fill="{c["aco1"]}"/>'
        )
        return pernas, corpo

    def engrenagens(self):
        c = COR
        dA, rpA, rtA = engrenagem(16, 2.6, 4)
        dB, rpB, rtB = engrenagem(10, 2.6, 3, 4)
        cxA, cyA = 80, 60
        beta = math.radians(-35)
        dist = rpA + rpB
        cxB, cyB = cxA + dist * math.cos(beta), cyA + dist * math.sin(beta)
        fA = math.degrees(beta)
        fB = math.degrees(beta) + 180 - 180 / 10
        self.defs.append(f'<path id="gA" d="{dA}"/><path id="gB" d="{dB}"/>')
        caixa = (f'<rect x="56" y="76" width="80" height="14" rx="3" fill="{c["aco2"]}"/>'
                 f'<rect x="{n(cxB - 4)}" y="{n(cyB)}" width="8" height="{n(80 - cyB)}" fill="{c["aco1"]}"/>'
                 f'<rect x="{cxA - 4}" y="{cyA}" width="8" height="{80 - cyA}" fill="{c["aco1"]}"/>')

        def roda(href, cx, cy, fase, classe, cor, cor_fundo):
            return (f'<g transform="translate({n(cx + 3)} {n(cy - 3)}) rotate({n(fase, 2)})"><g class="{classe}">'
                    f'<use href="#{href}" fill="{cor_fundo}" fill-rule="evenodd"/></g></g>'
                    f'<g transform="translate({n(cx)} {n(cy)}) rotate({n(fase, 2)})"><g class="{classe}">'
                    f'<use href="#{href}" fill="{cor}" fill-rule="evenodd"/></g></g>'
                    f'<circle cx="{n(cx)}" cy="{n(cy)}" r="2.2" fill="{c["aco0"]}"/>')
        return (caixa + roda("gA", cxA, cyA, fA, "rA", c["brasa"], c["brasa4"])
                + roda("gB", cxB, cyB, fB, "rB", c["aco5"], c["aco1"]))

    # -- esteira --------------------------------------------------------------
    def esteira(self):
        c = COR
        xa, xb, yf, prof = 60, 1110, 306, 12
        topo = poli([(xa, yf), (xb, yf), (xb + prof, yf - prof), (xa + prof, yf - prof)])
        self.defs.append(f'<clipPath id="lona"><path d="{topo}"/></clipPath>')
        ripas = "".join(f"M{x} {yf}l{prof} {-prof}" for x in range(xa - 24, xb + 12, 12))
        superficie = (f'<path d="{topo}" fill="{c["aco1"]}"/>'
                      f'<g clip-path="url(#lona)"><path class="rp" d="{ripas}" stroke="{c["aco3"]}" stroke-width="2"/></g>'
                      f'<path d="M{xa + prof} {yf - prof}H{xb + prof}" stroke="{c["aco4"]}" stroke-width="1"/>')
        rolos = []
        for x in range(xa + 30, xb, 42):
            rolos.append(f'<g transform="translate({x} 316)"><g class="ro"><circle r="5" fill="{c["aco0"]}" stroke="{c["aco4"]}" '
                         f'stroke-width="1.2"/><path d="M0 0H4" stroke="{c["aco5"]}" stroke-width="1.6"/></g></g>')
        pernas = "".join(f'<rect x="{x}" y="326" width="7" height="42" fill="{c["aco1"]}"/>'
                         f'<rect x="{x - 3}" y="364" width="13" height="4" fill="{c["aco2"]}"/>'
                         for x in (196, 376, 556, 736, 916))
        frente = (pernas + f'<rect x="{xa}" y="{yf}" width="{xb - xa}" height="20" fill="{c["aco2"]}"/>'
                  f'<rect x="{xa}" y="{yf}" width="{xb - xa}" height="2" fill="{c["aco4"]}"/>'
                  f'<rect x="{xa}" y="{yf + 18}" width="{xb - xa}" height="2" fill="{c["aco0"]}"/>' + "".join(rolos))
        return superficie, frente

    def blocos(self):
        c = COR
        bruto = bloco(c["bruto"], c["bruto3"], c["bruto2"],
                      f'<path d="M-9-18h14M-9-12h8M-9-6h17" stroke="{c["bruto2"]}" stroke-width="2.4"/>')
        tratado = bloco(c["dado"], c["dado_claro"], c["dado2"],
                        f'<path d="M-14-24h28v6h-28z" fill="{c["dado2"]}"/>'
                        f'<path d="M-9-12h18M-9-6h18" stroke="{c["dado3"]}" stroke-width="2.4"/>')
        self.defs.append(f'<g id="bb">{bruto}</g><g id="bt">{tratado}</g>')
        self.defs.append(f'<clipPath id="ate_dw"><rect x="0" y="0" width="1160" height="400"/></clipPath>')
        brutos = "".join(f'<use href="#bb" x="{96 + k * P}" y="304"/>' for k in range(5))
        tratados = "".join(f'<use href="#bt" x="{ENTREGA + k * P}" y="304"/>' for k in range(6))
        queda = f'<g class="qd"><use href="#bb" x="96" y="268"/></g>'
        return (queda, f'<g class="eb">{brutos}</g>',
                f'<g clip-path="url(#ate_dw)"><g class="et">{tratados}</g></g>')

    # -- robô -----------------------------------------------------------------
    def robo(self):
        c = COR
        ox, oy = OMBRO
        self.defs.append(
            f'<linearGradient id="torre" x1="0" x2="1"><stop offset="0" stop-color="{c["brasa3"]}"/>'
            f'<stop offset=".4" stop-color="{c["brasa"]}"/><stop offset="1" stop-color="{c["brasa4"]}"/></linearGradient>'
            f'<linearGradient id="pedestal" x1="0" x2="1"><stop offset="0" stop-color="{c["aco1"]}"/>'
            f'<stop offset=".4" stop-color="{c["aco3"]}"/><stop offset="1" stop-color="{c["aco0"]}"/></linearGradient>')
        base = (f'<rect x="{ox - 26}" y="{oy + 12}" width="52" height="40" fill="url(#pedestal)"/>'
                + self._listras(ox - 26, oy + 18, 52, 8) +
                f'<ellipse cx="{ox}" cy="{oy + 12}" rx="26" ry="5" fill="{c["aco4"]}"/>'
                f'<path d="M{ox - 18} {oy - 2}V{oy + 12}A18 4 0 0 0 {ox + 18} {oy + 12}V{oy - 2}Z" fill="url(#torre)"/>'
                f'<ellipse cx="{ox}" cy="{oy - 2}" rx="18" ry="4" fill="{c["brasa_clara"]}"/>'
                f'<g transform="translate({ox} {oy + 6})"><g class="gu"><rect x="15" y="-3" width="3" height="9" fill="{c["aco0"]}"/></g></g>')
        braco = (f'<path d="M0-9L{L1} -7V7L0 9Z" fill="{c["brasa"]}"/>'
                 f'<path d="M0-9L{L1}-7V-2L0-3Z" fill="{c["brasa_clara"]}" opacity=".55"/>')
        antebraco = (f'<path d="M0-6.5L{L2} -4.5V4.5L0 6.5Z" fill="{c["brasa2"]}"/>'
                     f'<path d="M0-6.5L{L2}-4.5V-1L0-1.5Z" fill="{c["brasa_clara"]}" opacity=".45"/>')
        junta = lambda r, cor: (f'<circle r="{r}" fill="{c["aco1"]}" stroke="{c["aco4"]}" stroke-width="1.5"/>'
                                f'<circle r="{n(r * 0.45)}" fill="{cor}"/>')
        arm = (f'<g transform="translate({ox} {oy})"><g class="gu"><g class="om">{braco}'
               f'<g transform="translate({L1} 0)"><g class="co">{antebraco}'
               f'<g transform="translate({L2} 0)">{junta(5, c["brasa_clara"])}</g></g>{junta(8, c["brasa"])}</g>'
               f'</g>{junta(11, c["brasa"])}</g></g>')
        dedo = lambda x: f'<rect x="{x}" y="10" width="4" height="17" rx="1" fill="{c["aco4"]}"/>'
        garra = (f'<g class="ga"><rect x="-3" y="0" width="6" height="6" fill="{c["aco2"]}"/>'
                 f'<g class="cg"><use href="#bb" y="38"/><g class="cp"><use href="#bt" y="38"/></g></g>'
                 f'<g class="ae"><ellipse cx="4" cy="26" rx="26" ry="10" fill="none" stroke="{c["dado_claro"]}" stroke-width="2"/></g>'
                 f'<rect x="-19" y="5" width="38" height="6" rx="2" fill="{c["aco3"]}"/>'
                 f'<rect x="-19" y="5" width="38" height="2" rx="1" fill="{c["brasa"]}"/>'
                 f'<g class="de">{dedo(-18)}</g><g class="dd">{dedo(14)}</g></g>')
        return base, arm + garra

    # -- armazém DW -----------------------------------------------------------
    def armazem(self):
        c = COR
        x0, x1, topo, chao, prof = 1036, 1166, 128, 368, 14
        fachada = poli([(x0, topo), (x1, topo), (x1, chao), (x0, chao)])
        teto = poli([(x0, topo), (x1, topo), (x1 + prof, topo - prof), (x0 + prof, topo - prof)])
        lado = poli([(x1, topo), (x1 + prof, topo - prof), (x1 + prof, chao - prof), (x1, chao)])
        # vão de carga (a esteira entra por aqui)
        vx0, vx1, vy0, vy1 = x0, 1092, 262, 306
        self.defs.append(
            f'<linearGradient id="escuro" x1="{vx0}" x2="{vx1}" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="#05080f" stop-opacity="0"/><stop offset=".85" stop-color="#05080f"/></linearGradient>'
            f'<linearGradient id="fach" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c["aco3"]}"/>'
            f'<stop offset="1" stop-color="{c["aco1"]}"/></linearGradient>')
        interior = f'<rect x="{vx0}" y="{vy0}" width="{vx1 - vx0}" height="{vy1 - vy0 + 22}" fill="#070b14"/>'
        sombra_vao = f'<rect x="{vx0}" y="{vy0}" width="{vx1 - vx0}" height="{vy1 - vy0 + 22}" fill="url(#escuro)"/>'
        parede = (f'<path d="{fachada}M{vx0} {vy0}V{vy1 + 20}H{vx1}V{vy0}Z" fill="url(#fach)" fill-rule="evenodd"/>'
                  f'<path d="{teto}" fill="{c["aco4"]}"/><path d="{lado}" fill="{c["aco0"]}"/>'
                  f'<rect x="{x0}" y="{topo}" width="{x1 - x0}" height="3" fill="{c["aco5"]}"/>'
                  f'<rect x="{x0}" y="{chao - 10}" width="{x1 - x0}" height="10" fill="{c["aco0"]}"/>')
        moldura = (self._listras(vx0, vy0 - 8, vx1 - vx0, 7)
                   + f'<rect x="{vx1}" y="{vy0 - 8}" width="5" height="{vy1 - vy0 + 28}" fill="{c["aco1"]}"/>')
        tiras = "".join(f'<rect x="{x}" y="{vy0}" width="7" height="{vy1 - vy0 - 2}" fill="#9fb3d9" opacity=".16"/>'
                        for x in range(vx0 + 3, vx1 - 4, 9))
        cortina = f'<g class="ct">{tiras}</g>'
        # prateleiras iluminadas: cada célula acende em onda, como carga chegando
        celulas = []
        k = 0
        for lin in range(3):
            for col in range(4):
                cx, cy = 1050 + col * 27, 150 + lin * 30
                atraso = -(k * T * 4 / 12)
                celulas.append(f'<rect x="{cx}" y="{cy}" width="21" height="22" rx="2" fill="{c["aco0"]}"/>'
                               f'<rect class="jl" style="animation-delay:{n(atraso, 2)}s" x="{cx + 3}" y="{cy + 3}" '
                               f'width="15" height="16" rx="1" fill="{c["dado"]}"/>')
                k += 1
        tam = self.tk900.tamanho_para_cap(36)
        d, larg = self.tk900.caminho("DW", tam, 1108, 118, espaco=3, ancora="middle")
        self.defs.append(f'<path id="dw" d="{d}"/>')
        prof_dw = "".join(f'<use href="#dw" x="{n(k * 0.9)}" y="{n(-k * 0.9)}" fill="{_mistura(c["dado2"], c["dado3"], k / 6)}"/>'
                          for k in range(6, 0, -1))
        letreiro = (f'<ellipse cx="1108" cy="100" rx="70" ry="30" fill="{c["dado"]}" opacity=".22" filter="url(#desfoque)"/>'
                    f'<rect x="1072" y="114" width="4" height="8" fill="{c["aco1"]}"/><rect x="1140" y="114" width="4" height="8" fill="{c["aco1"]}"/>'
                    + prof_dw + f'<use href="#dw" fill="{c["dado_claro"]}"/>')
        farol = (f'<rect x="1160" y="104" width="8" height="6" fill="{c["aco1"]}"/>'
                 f'<circle class="fa" cx="1164" cy="101" r="8" fill="{c["brasa"]}" opacity=".35"/>'
                 f'<path d="M1160 104a4 5 0 0 1 8 0z" fill="{c["brasa"]}"/>')
        return interior, sombra_vao, parede + moldura + cortina + "".join(celulas) + letreiro + farol

    def montar(self):
        c = COR
        fundo = self.fundo()
        placa, _ = self.placa()
        pernas_silo, corpo_silo = self.silo()
        eng = self.engrenagens()
        superficie, frente = self.esteira()
        queda, brutos, tratados = self.blocos()
        base_robo, braco = self.robo()
        interior, sombra_vao, armazem = self.armazem()
        css_robo, pose = animacao_robo()
        t_rip = 12 / V
        estilo = (
            "@keyframes mv{to{transform:translateX(84px)}}"
            ".eb{animation:mv 3s linear infinite}"
            f".et{{animation:mv 3s linear {n(-(1 - U_SOLTA) * T, 3)}s infinite}}"
            "@keyframes rp{to{transform:translateX(12px)}}"
            f".rp{{animation:rp {n(t_rip, 4)}s linear infinite}}"
            "@keyframes gi{to{transform:rotate(360deg)}}@keyframes ga2{to{transform:rotate(-360deg)}}"
            f".ro{{animation:gi {n(2 * math.pi * 5 / V, 3)}s linear infinite}}"
            ".rA{animation:gi 8s linear infinite}.rB{animation:ga2 5s linear infinite}"
            + css_robo + pose +
            ".gu,.om,.co,.ga,.de,.dd{animation:3s linear infinite}"
            ".gu{animation-name:gu}.om{animation-name:om}.co{animation-name:co}.ga{animation-name:ga}"
            ".de{animation-name:de}.dd{animation-name:dd}"
            f"@keyframes cg{{0%,{n(U_SOLTA * 100 - 0.05, 2)}%{{opacity:1}}{n(U_SOLTA * 100, 2)}%,100%{{opacity:0}}}}"
            ".cg{animation:cg 3s linear infinite}"
            "@keyframes cp{0%,28%{opacity:0}38%,100%{opacity:1}}.cp{opacity:1;animation:cp 3s linear infinite}"
            "@keyframes ae{0%,27%{opacity:0;transform:scale(.6)}31%{opacity:.9}42%,100%{opacity:0;transform:scale(1.25)}}"
            ".ae{opacity:0;transform-box:fill-box;transform-origin:center;animation:ae 3s ease-out infinite}"
            "@keyframes qd{0%,74.9%{opacity:0;transform:translateY(0)}"
            "75%{opacity:1;transform:translateY(0);animation-timing-function:cubic-bezier(.5,0,1,.6)}"
            "100%{opacity:1;transform:translateY(36px)}}"
            ".qd{opacity:0;animation:qd 3s linear infinite}"
            "@keyframes jl{0%,100%{opacity:.18}12%{opacity:.95}40%{opacity:.35}}"
            ".jl{opacity:.35;animation:jl 12s ease-in-out infinite}"
            "@keyframes fa{0%,100%{opacity:.15}50%{opacity:.7}}.fa{animation:fa 2s ease-in-out infinite}"
            "@keyframes ct{0%,100%{transform:skewX(0)}12%{transform:skewX(-6deg)}30%{transform:skewX(2deg)}}"
            ".ct{transform-box:fill-box;transform-origin:top;animation:ct 3s ease-in-out infinite;"
            f"animation-delay:{n((U_SOLTA * T + (1017 - ENTREGA) / V) % T - T, 2)}s}}"
            "@keyframes bri{0%{transform:skewX(-18deg) translateX(-200px)}22%,100%{transform:skewX(-18deg) translateX(820px)}}"
            ".bri{animation:bri 7s ease-in-out 1s infinite}"
        )
        corpo = (fundo + eng + pernas_silo + interior + base_robo + superficie + queda + corpo_silo
                 + brutos + tratados + frente + sombra_vao + armazem + braco + placa)
        defs = "".join(self.defs) + "".join(self.glifos.defs)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
               f'aria-labelledby="t d"><title id="t">Rocha</title>'
               f'<desc id="d">Placa industrial com o nome ROCHA e o subtítulo Engenharia de dados, automação e ETL, '
               f'sobre uma fábrica de dados animada: um silo ERP despeja registros brutos numa esteira, um braço '
               f'robótico pega cada registro, transforma e devolve à esteira, que leva os blocos tratados para o '
               f'armazém DW; engrenagens giram e as prateleiras do armazém acendem conforme a carga chega.</desc>'
               f'<defs>{defs}</defs><style>{estilo}</style>'
               f'<g clip-path="url(#quadro)">{corpo}</g>'
               f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="#24324f"/></svg>')
        return svg


def _mistura(a, b, t):
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def main():
    svg = Banner().montar()
    saida = PASTA.parent / "assets" / "banner.svg"
    saida.write_text(svg, encoding="utf-8")
    print(f"{saida.name}: {len(svg.encode()) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
