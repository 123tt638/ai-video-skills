"""Presenter layers for the page: graded + skin-smoothed cutout frames (WebP with alpha) and one dark room plate."""
import cv2, numpy as np, os, sys
from PIL import Image
OUT = os.environ.get('PERSON_OUT','film/person'); os.makedirs(OUT, exist_ok=True)
A0, A1, STEP = int(sys.argv[1]), int(sys.argv[2]), 1
cap = cv2.VideoCapture(os.environ.get('GRADED','work/graded.mp4')); mcap = cv2.VideoCapture(os.environ.get('MASK','work/mask.mp4'))
cap.set(cv2.CAP_PROP_POS_FRAMES, A0); mcap.set(cv2.CAP_PROP_POS_FRAMES, A0)
acc = None; wsum = None; i = A0
while True:
    if i >= A1: break
    ok, fr = cap.read(); ok2, mk = mcap.read()
    if not ok or not ok2: break
    m = cv2.cvtColor(mk, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    # --- skin beautify: edge-preserving smoothing on skin-coloured pixels inside the person
    ycc = cv2.cvtColor(fr, cv2.COLOR_BGR2YCrCb)
    skin = cv2.inRange(ycc, (40, 135, 85), (255, 175, 130)).astype(np.float32) / 255
    skin = cv2.GaussianBlur(skin * (m > 0.5), (0, 0), 4)[..., None]
    smooth = cv2.bilateralFilter(fr, 9, 38, 9)
    f = fr.astype(np.float32)
    f = f * (1 - skin * 0.7) + smooth.astype(np.float32) * skin * 0.7
    # brighten + warm skin a touch, keep highlights
    f = f + skin * np.array([4, 8, 12], np.float32)
    f = 255 * (f / 255) ** 0.94
    a = np.clip((m - 0.12) / 0.76, 0, 1)
    a = cv2.GaussianBlur(a, (0, 0), 1.2)
    rgba = np.dstack([np.clip(f[..., ::-1], 0, 255).astype(np.uint8), (a * 255).astype(np.uint8)])
    Image.fromarray(rgba, 'RGBA').save(f'{OUT}/{i:05d}.webp', quality=90, method=4)
    # accumulate room pixels where nobody stands (for a clean plate)
    w = np.clip(1 - m * 1.5, 0, 1)[..., None]
    acc = fr.astype(np.float64) * w if acc is None else acc + fr * w
    wsum = w.astype(np.float64) if wsum is None else wsum + w
    i += 1
    if i % 200 == 0: print(i, flush=True)
plate = (acc / np.maximum(wsum, 1e-3)).astype(np.float32)
hole = (wsum[..., 0] < 3).astype(np.uint8) * 255
plate = cv2.inpaint(np.clip(plate, 0, 255).astype(np.uint8), hole, 12, cv2.INPAINT_TELEA)
cv2.imwrite(f'{OUT}/../room_plate_{A0}.jpg', plate, [cv2.IMWRITE_JPEG_QUALITY, 92])
print('frames', i)
