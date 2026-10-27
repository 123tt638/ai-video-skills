"""Shared timing, fonts and easing for the landscape talking-head edit.

环境变量：TOKENS（tokens_cut.json）、TALK_FRAMES（剪后口播帧数）、AD_LEN（成片秒数）、ANTON（Anton 字体路径）。
"""
import os, json, math
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

FPS = 30
W, H = 1920, 1080
OFF = 1.6                      # cold-open hook before the talk starts
TALK_FRAMES = int(os.environ.get('TALK_FRAMES', 2056))
TALK_LEN = TALK_FRAMES / FPS
SHOW_T0 = OFF + TALK_LEN + 0.0  # showcase title card start
SHOW_CARD = 2.0
AD_LEN = float(os.environ.get('AD_LEN', 30.08))
END = SHOW_T0 + SHOW_CARD + AD_LEN + 0.6

# palette: near-black studio, warm white, cheese yellow, tomato red
INK = (14, 15, 18)
PAPER = (246, 242, 234)
YEL = (255, 202, 40)
RED = (255, 72, 54)
MUTE = (150, 154, 162)
CARD = (26, 28, 33)

SANS = '/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc'
ANTON = os.environ.get('ANTON','Anton-Regular.ttf')


@lru_cache(None)
def font(weight, size):
    if weight == 'anton':
        return ImageFont.truetype(ANTON, size)
    return ImageFont.truetype(SANS % weight, size, index=2)


# ---- word timing (cut timeline, talk-relative seconds) ----
_T = json.load(open(os.environ.get('TOKENS','work/tokens_cut.json')))
_chars, _times = [], []
for tok, t in _T:
    for c in tok:
        _chars.append(c); _times.append(t)
RAW = ''.join(_chars)


def wt(s, after=0.0):
    """Talk-relative start time of the first occurrence of raw substring s after `after` seconds."""
    i = 0
    while True:
        i = RAW.find(s, i)
        if i < 0:
            raise KeyError(s)
        if _times[i] >= after - 1e-6:
            return _times[i]
        i += 1


def wend(s, after=0.0):
    i = RAW.find(s)
    while i >= 0 and _times[i] < after - 1e-6:
        i = RAW.find(s, i + 1)
    j = i + len(s) - 1
    return _times[j] + 0.22


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out(x):
    x = clamp(x); return 1 - (1 - x) ** 3


def ease_io(x):
    x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def back(x, k=1.70158):
    x = clamp(x); return 1 + (k + 1) * (x - 1) ** 3 + k * (x - 1) ** 2


def prog(t, a, d):
    return clamp((t - a) / d) if d > 0 else (1.0 if t >= a else 0.0)


@lru_cache(None)
def text_img(txt, weight, size, color, stroke=0, stroke_color=(0, 0, 0), track=0):
    f = font(weight, size)
    d = ImageDraw.Draw(Image.new('L', (1, 1)))
    if track:
        w = sum(d.textlength(c, font=f) + track for c in txt) - track
    else:
        w = d.textlength(txt, font=f)
    asc, desc = f.getmetrics()
    pad = stroke + 4
    im = Image.new('RGBA', (int(w) + pad * 2, asc + desc + pad * 2), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    if track:
        x = pad
        for c in txt:
            dr.text((x, pad), c, font=f, fill=color + (255,), stroke_width=stroke, stroke_fill=stroke_color + (255,))
            x += d.textlength(c, font=f) + track
    else:
        dr.text((pad, pad), txt, font=f, fill=color + (255,), stroke_width=stroke, stroke_fill=stroke_color + (255,))
    return im


def paste(dst, im, x, y, alpha=1.0, scale=1.0, anchor='lt'):
    """Alpha-composite RGBA `im` onto RGBA PIL `dst` with opacity and scale; anchor lt/mm/mt/lm."""
    if alpha <= 0.003:
        return
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if alpha < 0.999:
        a = im.getchannel('A').point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    if anchor == 'mm':
        x, y = x - im.width / 2, y - im.height / 2
    elif anchor == 'mt':
        x = x - im.width / 2
    elif anchor == 'lm':
        y = y - im.height / 2
    elif anchor == 'rm':
        x, y = x - im.width, y - im.height / 2
    dst.alpha_composite(im, (int(round(x)), int(round(y))))


@lru_cache(None)
def shadow_box(w, h, r, fill, border=None, shadow=24, salpha=150):
    pad = shadow * 2
    im = Image.new('RGBA', (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    sh = Image.new('L', im.size, 0); ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 10, pad + w, pad + h + 10], r, fill=salpha)
    sh = sh.filter(ImageFilter.GaussianBlur(shadow))
    im = Image.new('RGBA', im.size, (0, 0, 0, 255)); im.putalpha(sh)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([pad, pad, pad + w, pad + h], r, fill=fill, outline=border, width=2 if border else 0)
    return im, pad
