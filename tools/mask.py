import onnxruntime as ort, numpy as np, cv2, subprocess, time, os
W, H = 720, 1280
so = ort.SessionOptions(); so.intra_op_num_threads = os.cpu_count()
sess = ort.InferenceSession(os.environ.get('U2NET','u2net_human_seg.onnx'), so, providers=['CPUExecutionProvider'])
inp = sess.get_inputs()[0].name
mean = np.array([0.485, 0.456, 0.406], np.float32); std = np.array([0.229, 0.224, 0.225], np.float32)
dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', 'cut.mov', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'gray', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                        '-c:v', 'libx264', '-crf', '8', '-preset', 'fast', '-pix_fmt', 'yuv420p', 'mask.mp4'], stdin=subprocess.PIPE)
prev = None; i = 0; t0 = time.time()
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    x = cv2.resize(fr, (320, 320), interpolation=cv2.INTER_AREA)[:, :, ::-1].astype(np.float32) / 255
    x = ((x / max(x.max(), 1e-6) - mean) / std).transpose(2, 0, 1)[None]
    o = sess.run(None, {inp: x})[0][0, 0]; o = (o - o.min()) / (o.max() - o.min() + 1e-6)
    m = cv2.resize(o, (W, H), interpolation=cv2.INTER_CUBIC)
    m = prev * 0.4 + m * 0.6 if prev is not None else m; prev = m
    enc.stdin.write((np.clip(m, 0, 1) * 255).astype(np.uint8).tobytes()); i += 1
    if i % 100 == 0: print(i, round(time.time() - t0, 1), flush=True)
enc.stdin.close(); enc.wait(); print('done', i, round(time.time() - t0, 1))
