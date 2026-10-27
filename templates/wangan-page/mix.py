"""Score + foley + voice + ad audio → out/mix.wav. Everything placed from events.json / timeline.json."""
import json, os, subprocess, sys
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.environ.get('LIB', os.path.abspath(os.path.join(HERE, '../..')))
sys.path.insert(0, os.path.join(LIB, 'core/audio'))
import sfx as S
SR = S.SR
ev = json.load(open(os.path.join(HERE, 'events.json')))
tl = json.load(open(os.path.join(HERE, 'timeline.json')))
DUR = ev['dur']; OFF = tl['OFF']; TALK = tl['TALK']; SHOW0 = OFF + TALK + 0.2; AD0 = SHOW0 + 1.8
N = int((DUR + 1) * SR)
rng = np.random.default_rng(3)
t_ = S.t_; env = S.env_exp
hz = lambda m: 440 * 2 ** ((m - 69) / 12)


def add(buf, x, at, g=1.0):
    i = int(round(at * SR))
    if i < 0: x = x[-i:]; i = 0
    j = min(len(buf), i + len(x))
    if j > i: buf[i:j] += x[:j - i] * g


# ---------------- score: 120 BPM, bright major pop loop, one chord per bar (I–V–vi–IV in C)
bpm = 120; beat = 60 / bpm; bar = 4 * beat
mus = np.zeros(N)
chords = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]
def kick():
    d = .32; tt = t_(d); f = 50 + 120 * np.exp(-tt * 35)
    return np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * env(d, .11)
def snare():
    d = .22; return S.bp(S.noise(d), 900, 6000) * env(d, .05) * .7 + np.sin(2 * np.pi * 190 * t_(d)) * env(d, .03) * .4
def hat(o=False):
    d = .12 if o else .04; return S.hp(S.noise(d), 7000) * env(d, .03 if o else .008) * .35
def bass(m, d):
    tt = t_(d); x = np.sin(2 * np.pi * hz(m) * tt) + .45 * np.sin(4 * np.pi * hz(m) * tt) + .25 * np.sin(6 * np.pi * hz(m) * tt)
    return x * np.minimum(1, tt / .005) * env(d, .22) * .55
def stab(ch, d=.22):
    tt = t_(d); x = sum(np.sign(np.sin(2 * np.pi * hz(m + 12) * tt * (1 + dt))) for m in ch for dt in (-.004, .004))
    return S.lp(x / (2 * len(ch)), 2600) * np.minimum(1, tt / .004) * env(d, .09) * .5
def pluck(m, d=.3):
    tt = t_(d); return (np.sin(2 * np.pi * hz(m) * tt) + .3 * np.sin(2 * np.pi * hz(m) * 4 * tt)) * env(d, .07) * .35
def bell(m, d=.8):
    tt = t_(d); return (np.sin(2 * np.pi * hz(m) * tt) + .4 * np.sin(2 * np.pi * hz(m) * 2.76 * tt)) * env(d, .25) * .3

start = OFF - 2 * beat; end = SHOW0
nb = int((end - start) / beat)
for b in range(nb):
    t = start + b * beat; ch = chords[(b // 4) % 4]
    add(mus, kick(), t, .9 if b % 2 == 0 else .55)
    if b % 4 in (1, 3): add(mus, snare(), t, .6)
    add(mus, hat(), t + beat / 2, .7); add(mus, hat(b % 4 == 3), t, .4)
    add(mus, bass(ch[0] - 24, beat * .9), t, .9)
    if b % 2 == 1: add(mus, stab(ch), t + beat / 2, .55)
    for k in range(2): add(mus, pluck(ch[(b + k) % 3] + 24, .25), t + k * beat / 2, .5)
# hook: drums only, big hits
for e in ev['ev']:
    if e['type'] == 'hit': add(mus, kick(), e['t'], 1.2); add(mus, S.crash(.8), e['t'], .35 if e['t'] == 0 else .15)
# fade the music into the showcase
fade = np.ones(N); a, b = int((SHOW0 - 0.4) * SR), int((SHOW0 + 0.1) * SR); fade[a:b] = np.linspace(1, 0, b - a); fade[b:] = 0
mus *= fade
mus = S.hp(mus, 35)

# ---------------- foley from the picture's events
fx = np.zeros(N)
for e in ev['ev']:
    t, k = e['t'], e['type']
    if k == 'slam': add(fx, S.click(1.4, .5), t); add(fx, S.thump(.35, 90), t)
    elif k == 'pop': add(fx, S.pop(.7), t); add(fx, pluck(72 + [0, 4, 7, 12, 16][e.get('pitch', 0)], .25), t, .6)
    elif k == 'judge': add(fx, stab([72, 76, 79], .35), t, 1.0); add(fx, S.crash(.5), t, .25); add(fx, bell(84), t + .02, .6)
    elif k == 'jingle':
        add(fx, S.whoosh(.35, .8), t - .3); add(fx, S.crash(.9), t, .45)
        for i, m in enumerate([67, 72, 76, 79]): add(fx, stab([m], .16), t + i * .07, .8)
    elif k == 'cut': add(fx, S.whoosh(.25, .6), t - .18); add(fx, S.thump(.4, 70), t)
    elif k == 'whoosh': add(fx, S.whoosh(.3, .5), t - .15)
    elif k == 'shutter': add(fx, S.click(.8, .9), t); add(fx, S.click(1.1, .6), t + .06)
    elif k == 'riser':
        d = .32; tt = t_(d); add(fx, S.hp(S.noise(d), 2000) * (tt / d) ** 2 * .5, t)
# ding on the checks
for key in [k for k in ('chk', 'freeze') if k in tl['M']]: add(fx, S.ding(.6), OFF + tl['M'][key] + (0.5 if key == 'chk' else 0))

# ---------------- voice (the cut talk), cleaned and compressed
vw = os.path.join(HERE, 'out', 'voice.wav'); os.makedirs(os.path.dirname(vw), exist_ok=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.environ.get('TALK_CUT', os.path.join(HERE, 'cut.mov')), '-af',
                'highpass=f=80,afftdn=nr=10:nf=-40,equalizer=f=220:t=q:w=1:g=-2,equalizer=f=3500:t=q:w=1.2:g=3,'
                'acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=4,loudnorm=I=-16:TP=-2:LRA=7',
                '-ar', str(SR), '-ac', '1', vw], check=True)
v, _ = sf.read(vw); voice = np.zeros(N); add(voice, v, OFF)
lvl = np.sqrt(np.convolve(voice ** 2, np.ones(2400) / 2400, 'same'))
duck = np.convolve(np.clip(1 - 7 * lvl, .5, 1), np.ones(6000) / 6000, 'same')   # ~45 % under the voice

def rms(x): return np.sqrt(np.mean(x[np.abs(x) > 1e-4] ** 2)) if np.any(np.abs(x) > 1e-4) else 1
mus *= 10 ** (-12 / 20) * rms(voice) / rms(mus)
fx *= 10 ** (-9 / 20) * rms(voice) / rms(fx)

# ---------------- ad audio for the showcase
aw = os.path.join(HERE, 'out', 'ad.wav')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.environ.get('AD_VIDEO', os.path.join(HERE, 'ad.mp4')), '-vn', '-ar', str(SR), '-ac', '1', '-af', 'loudnorm=I=-16:TP=-1.5', aw], check=True)
ad, _ = sf.read(aw); g = np.ones(len(ad)); g[:int(.3 * SR)] = np.linspace(0, 1, int(.3 * SR)); g[-int(.6 * SR):] = np.linspace(1, 0, int(.6 * SR))
adb = np.zeros(N); add(adb, ad * g, AD0)

mix = voice + mus * duck + fx * (0.6 + 0.4 * duck) + adb
mix = S.limit(S.compress(mix, .5, 2.0), .9)[:int(DUR * SR)]
sf.write(os.path.join(HERE, 'out', 'mix.wav'), np.stack([mix, mix], 1).astype(np.float32), SR)
print('mix', len(mix) / SR)
