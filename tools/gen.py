"""Genera gli asset della watchface "Red Signal" (450x450, Watch Face Format).
background.png   -> decorazioni statiche (bande a strisce, etichette, onde, mirini, binari delle barre)
d0..d9.png       -> cifre squadrate a contorno per l'ora
stripe_mask.png  -> maschera che trasforma la barra batteria in una barra a strisce
preview.png      -> anteprima con valori di esempio (stessa geometria di watchface.xml)
Uso: python3 tools/gen.py <cartella_output> tools/roboto_cond_semibold.ttf
"""
import math, sys, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
FONT = sys.argv[2] if len(sys.argv) > 2 else "roboto_cond_semibold.ttf"
os.makedirs(OUT, exist_ok=True)

S = 4
W = 450
BG = (30, 30, 30)
RD = (240, 40, 24)
RDD = (95, 24, 18)
GR = (40, 215, 40)
GRD = (22, 90, 22)

# ------------------------------------------------------------------ geometria (= watchface.xml)
DIG_W, DIG_H = 72, 104
DIG_Y = 132
DIG_X = [52, 132, 246, 326]          # HH : MM
COLON_X = 214                        # centro dei due punti
BAT_X, BAT_Y, BAT_W, BAT_H = 112, 262, 200, 14
STEP_BAR = (140, 382, 170, 5)


def P(v):
    return int(round(v * S))


def font(sz):
    return ImageFont.truetype(FONT, P(sz))


class Layer:
    def __init__(self, w=W, h=W):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (P(w), P(h)), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def line(self, pts, col, th=2):
        self.d.line([(P(x), P(y)) for x, y in pts], fill=col, width=max(1, P(th)))

    def rect(self, x0, y0, x1, y1, col=None, outline=None, th=2):
        self.d.rectangle([P(x0), P(y0), P(x1), P(y1)], fill=col,
                         outline=outline, width=P(th) if outline else 0)

    def poly(self, pts, col):
        self.d.polygon([(P(x), P(y)) for x, y in pts], fill=col)

    def text(self, x, y, s, sz, col, anchor="mm"):
        self.d.text((P(x), P(y)), s, font=font(sz), fill=col, anchor=anchor)

    def render(self, glow=0, strength=1.6):
        im = self.im
        if glow:
            g = im.filter(ImageFilter.GaussianBlur(P(glow) / 2))
            g.putalpha(g.getchannel("A").point(lambda v: min(255, int(v * strength * 0.5))))
            im = Image.alpha_composite(g, im)
        return im.resize((self.w, self.h), Image.LANCZOS)


def stripes(L, x0, y0, w, h, col, step=10, slant=None):
    """Strisce diagonali tipo nastro di pericolo, ritagliate nel rettangolo."""
    slant = h if slant is None else slant
    tmp = Layer(w, h)
    x = -slant
    while x < w + slant:
        tmp.poly([(x, h), (x + step / 2, h), (x + step / 2 + slant, 0), (x + slant, 0)], col)
        x += step
    L.im.alpha_composite(tmp.im, (P(x0), P(y0)))


def crosshair(L, x, y, s, col, th=2):
    L.line([(x - s, y), (x + s, y)], col, th)
    L.line([(x, y - s), (x, y + s)], col, th)


# ------------------------------------------------------------------ cifre a blocchi con contorno
SEG = {  # a=alto b=alto-dx c=basso-dx d=basso e=basso-sx f=alto-sx g=centro
    "0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc",
    "5": "afgcd", "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcdfg",
}


def digit_mask(ch, w=DIG_W, h=DIG_H, t=17, ch_cut=12, pad=4):
    """Maschera piena della cifra (segmenti uniti, angoli esterni smussati)."""
    m = Image.new("L", (P(w), P(h)), 0)
    d = ImageDraw.Draw(m)
    x0, y0, x1, y1 = pad, pad, w - pad, h - pad
    ym = (y0 + y1) / 2
    R = lambda a, b, c, e: d.rectangle([P(a), P(b), P(c), P(e)], fill=255)
    s = SEG[ch]
    if ch == "1":
        cx = (x0 + x1) / 2 + 6
        R(cx - t / 2, y0, cx + t / 2, y1)
        d.polygon([(P(cx - t / 2), P(y0)), (P(cx - t / 2 - 14), P(y0 + 14)),
                   (P(cx - t / 2 - 14), P(y0 + 14 + t * 0.8)), (P(cx - t / 2), P(y0 + t * 0.8))], fill=255)
    else:
        if "a" in s: R(x0, y0, x1, y0 + t)
        if "d" in s: R(x0, y1 - t, x1, y1)
        if "g" in s: R(x0, ym - t / 2, x1, ym + t / 2)
        if "f" in s: R(x0, y0, x0 + t, ym + t / 2)
        if "e" in s: R(x0, ym - t / 2, x0 + t, y1)
        if "b" in s: R(x1 - t, y0, x1, ym + t / 2)
        if "c" in s: R(x1 - t, ym - t / 2, x1, y1)
        if ch == "7":  # gamba diagonale
            d.polygon([(P(x1 - t), P(y0 + t)), (P(x1), P(y0 + t)), (P(x0 + 18 + t), P(y1)), (P(x0 + 18), P(y1))], fill=255)
            d.rectangle([P(x1 - t), P(ym), P(x1), P(y1)], fill=0)
    # smusso degli angoli esterni del riquadro
    c = ch_cut
    for (ax, ay, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.polygon([(P(ax - sx), P(ay - sy)), (P(ax + sx * c), P(ay - sy)), (P(ax - sx), P(ay + sy * c))], fill=0)
    return m


def outline_from_mask(m, th=2.6):
    k = int(P(th)) * 2 + 1
    er = m.filter(ImageFilter.MinFilter(k if k % 2 else k + 1))
    return ImageChops.subtract(m, er)


def tint(mask, col, alpha=255):
    im = Image.new("RGBA", mask.size, col + (0,))
    im.putalpha(mask.point(lambda v: v * alpha // 255))
    return im


def digit_image(ch):
    m = digit_mask(ch)
    fill = tint(m, RD, 38)
    edge = tint(outline_from_mask(m), RD)
    glow = edge.filter(ImageFilter.GaussianBlur(P(2.5)))
    glow.putalpha(glow.getchannel("A").point(lambda v: v // 2))
    im = Image.alpha_composite(Image.alpha_composite(fill, glow), edge)
    return im.resize((DIG_W, DIG_H), Image.LANCZOS)


def ghost_image():
    m = digit_mask("8")
    return tint(outline_from_mask(m, 1.6), RD, 34).resize((DIG_W, DIG_H), Image.LANCZOS)


# ------------------------------------------------------------------ sfondo
WAVE_Y, WAVE_H = 292, 158          # striscia delle onde (coordinate quadrante)
PER_A, PER_B = 180, 300            # periodo in px dei due strati (60 s divisibile per i tempi di ciclo)


def wave_strip(per, front=True):
    """Striscia di onde ripetibile: larga 450 + un periodo, così scorrendo di un periodo torna uguale."""
    w = 450 + per
    L = Layer(w, WAVE_H)
    y0, amp = 360 - WAVE_Y, 50
    f = lambda x, ph: math.sin(2 * math.pi * x / per + ph)
    n = 16 if front else 12
    for k in range(n):
        ph = k * 0.12
        a = amp * (1 - k * 0.014)
        pts = [(x, y0 + (a if front else a * 0.8) * (f(x, ph) if front else -f(x, ph + 0.9)) + k * 0.6)
               for x in range(0, w + 1, 2)]
        if front:
            L.line(pts, RD + (75 if k % 3 else 135,), 1.2)
        else:
            L.line(pts, RD + (50,), 1.0)
    if front:  # piccoli anelli lungo l'onda (passo = periodo/6, quindi ripetibili)
        step = per / 6
        x = step / 2
        while x < w:
            y = y0 + amp * f(x, 0.5)
            L.d.ellipse([P(x - 5), P(y - 7), P(x + 5), P(y + 7)], outline=RD + (115,), width=P(1.2))
            x += step
    return L.render()


def background(preview_ghost=True):
    base = Image.new("RGBA", (W, W), (0, 0, 0, 255))
    circ = Image.new("L", (W * S, W * S), 0)
    ImageDraw.Draw(circ).ellipse([0, 0, W * S - 1, W * S - 1], fill=255)
    circ = circ.resize((W, W), Image.LANCZOS)
    face = Image.new("RGBA", (W, W), BG + (255,))
    base.paste(face, (0, 0), circ)

    L = Layer()
    # banda superiore a strisce + cornice
    stripes(L, 112, 42, 226, 16, RD + (255,), step=12)
    L.poly([(205, 58), (225, 44), (245, 58)], BG + (255,))
    L.poly([(212, 58), (225, 49), (238, 58)], RD + (255,))
    # righe "terminale"
    L.text(116, 76, "LINK:", 15, RD, "lm")
    L.text(160, 76, "+++++", 15, GR, "lm")
    L.text(226, 76, "SYS:", 15, RD, "lm")
    L.text(262, 76, "1011 0010 01", 15, GR, "lm")
    # etichetta data
    L.rect(98, 92, 150, 116, None, RD, 2)
    L.text(124, 104.5, "DATE", 15, GR)

    # cifre fantasma + due punti
    if preview_ghost:
        g = ghost_image()
        for x in DIG_X:
            L.im.alpha_composite(g.resize((P(DIG_W), P(DIG_H)), Image.LANCZOS), (P(x), P(DIG_Y)))
    for cy in (DIG_Y + 32, DIG_Y + 70):
        L.rect(COLON_X - 6, cy - 6, COLON_X + 6, cy + 6, RD + (70,), RD, 2)

    # riga rossa + barra batteria (binario spento a strisce)
    L.line([(48, 252), (402, 252)], RD, 2.5)
    L.text(68, BAT_Y + BAT_H / 2 + 0.5, "BATT", 15, RD, "lm")
    stripes(L, BAT_X, BAT_Y, BAT_W, BAT_H, RDD + (255,), step=10)
    L.line([(48, 288), (402, 288)], RD, 2.5)

    base.alpha_composite(L.render(glow=4))
    base.putalpha(circ)
    return base


def circle_mask():
    c = Image.new("L", (W * S, W * S), 0)
    ImageDraw.Draw(c).ellipse([0, 0, W * S - 1, W * S - 1], fill=255)
    return c.resize((W, W), Image.LANCZOS)


def foreground():
    """Elementi sopra le onde: mirini, scanner, etichetta e binario dei passi, tacche esterne."""
    L = Layer()
    for x in (95, 170, 245, 320):
        crosshair(L, x, 318, 7, GR + (150,), 1.6)
    for x in (130, 205, 280, 355):
        crosshair(L, x, 405, 7, GR + (150,), 1.6)
    for y in range(296, 432, 5):
        L.rect(118, y, 123, y + 2.5, GR + (120,))
    # etichetta passi
    L.rect(180, 298, 270, 322, BG + (235,), RD, 2.2)
    L.text(225, 310.5, "STEPS", 16, GR)
    # binario barra passi
    x, y, w, h = STEP_BAR
    L.rect(x, y, x + w, y + h, GRD + (255,))
    L.text(x - 8, y + 2.5, "0", 11, GR + (170,), "rm")
    L.text(x + w + 8, y + 2.5, "10K", 11, GR + (170,), "lm")

    # anello esterno con tacche
    for i in range(60):
        a = math.radians(i * 6)
        r0 = 216 if i % 5 else 209
        L.line([(225 + r0 * math.sin(a), 225 - r0 * math.cos(a)),
                (225 + 221 * math.sin(a), 225 - 221 * math.cos(a))],
               (RD if i % 5 == 0 else RDD) + (255,), 2 if i % 5 == 0 else 1.2)

    im = L.render(glow=4)
    im.putalpha(ImageChops.multiply(im.getchannel("A"), circle_mask()))
    return im


def stripe_mask():
    """Bande color sfondo con spazi trasparenti: sopra la barra rossa piena la fa apparire a strisce."""
    L = Layer(BAT_W, BAT_H)
    L.rect(0, 0, BAT_W, BAT_H, BG + (255,))
    tmp = Layer(BAT_W, BAT_H)
    stripes(tmp, 0, 0, BAT_W, BAT_H, (255, 255, 255, 255), step=10)
    hole = tmp.im.getchannel("A")
    a = L.im.getchannel("A")
    L.im.putalpha(ImageChops.subtract(a, hole))
    return L.render()


# ------------------------------------------------------------------ anteprima
def preview(bg, fg, wa, wb, digits, mask, t=0.0, hh=10, mm=8, ss=42, bat=78, steps=6542, date="GIO 26 NOV"):
    im = bg.copy()
    waves = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    waves.alpha_composite(wb, (int(-PER_B + (t % 10) * PER_B / 10), WAVE_Y))
    waves.alpha_composite(wa, (int(-(t % 6) * PER_A / 6), WAVE_Y))
    waves.putalpha(ImageChops.multiply(waves.getchannel("A"), circle_mask()))
    im.alpha_composite(waves)
    im.alpha_composite(fg)
    for x, ch in zip(DIG_X, f"{hh:02d}{mm:02d}"):
        im.alpha_composite(digits[ch], (x, DIG_Y))
    L = Layer()
    L.text(162, 104.5, date, 22, GR, "lm")
    L.text(400, 104.5, f"{ss:02d}", 22, GR, "rm")
    L.text(372, 104.5, "SEC", 13, RD, "rm")
    L.rect(BAT_X, BAT_Y, BAT_X + BAT_W * bat / 100, BAT_Y + BAT_H, RD + (255,))
    im.alpha_composite(L.render())
    im.alpha_composite(mask, (BAT_X, BAT_Y))
    L = Layer()
    L.text(366, BAT_Y + BAT_H / 2, f"{bat}%", 22, RD)
    L.text(225, 350, f"{steps}", 40, GR)
    x, y, w, h = STEP_BAR
    L.rect(x, y, x + w * min(1, steps / 10000), y + h, GR + (255,))
    im.alpha_composite(L.render())
    return im


if __name__ == "__main__":
    digits = {c: digit_image(c) for c in "0123456789"}
    for c, d in digits.items():
        d.save(f"{OUT}/d{c}.png")
    bg = background()
    bg.save(f"{OUT}/background.png")
    m = stripe_mask()
    m.save(f"{OUT}/stripe_mask.png")
    fg = foreground()
    fg.save(f"{OUT}/foreground.png")
    wa, wb = wave_strip(PER_A, True), wave_strip(PER_B, False)
    wa.save(f"{OUT}/wave_a.png")
    wb.save(f"{OUT}/wave_b.png")
    pv = preview(bg, fg, wa, wb, digits, m)
    pv.save(f"{OUT}/preview.png")
    if len(sys.argv) > 3:  # GIF dimostrativa dell'animazione
        fr = [preview(bg, fg, wa, wb, digits, m, t=i / 10, ss=42 + i // 10).convert("RGB") for i in range(60)]
        fr[0].save(sys.argv[3], save_all=True, append_images=fr[1:], duration=100, loop=0)
    print("ok")
