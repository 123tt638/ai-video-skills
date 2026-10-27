"""逐字时间轴：SenseVoice（sherpa-onnx）+ Silero VAD，输出每个字/词的开始时间。

用法：python asr_tokens.py talk.mp4 out/tokens.json [--model DIR] [--vad vad.onnx]
模型下载（GitHub Releases，可在受限网络里使用）：
  https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2
  https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx
依赖：pip install sherpa-onnx soundfile numpy
"""
import argparse, json, subprocess, tempfile, os
import numpy as np, soundfile as sf, sherpa_onnx as so

ap = argparse.ArgumentParser()
ap.add_argument('video'); ap.add_argument('out')
ap.add_argument('--model', default='sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17')
ap.add_argument('--vad', default='silero_vad.onnx'); ap.add_argument('--lang', default='zh')
a = ap.parse_args()
wav = tempfile.mktemp(suffix='.wav')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', a.video, '-ac', '1', '-ar', '16000', wav], check=True)
x, sr = sf.read(wav, dtype='float32'); os.remove(wav)
rec = so.OfflineRecognizer.from_sense_voice(model=f'{a.model}/model.int8.onnx', tokens=f'{a.model}/tokens.txt',
                                            language=a.lang, use_itn=False, num_threads=4)
cfg = so.VadModelConfig(); cfg.silero_vad.model = a.vad; cfg.silero_vad.threshold = 0.4
cfg.silero_vad.min_silence_duration = 0.25; cfg.silero_vad.max_speech_duration = 10; cfg.sample_rate = 16000
vad = so.VoiceActivityDetector(cfg, buffer_size_in_seconds=600)
x = np.concatenate([x, np.zeros(16000, np.float32)])
tokens = []
for i in range(0, len(x), 512):
    vad.accept_waveform(x[i:i + 512])
    while not vad.empty():
        s = vad.front; st = s.start / 16000; seg = np.array(s.samples)
        r = rec.create_stream(); r.accept_waveform(16000, seg); rec.decode_stream(r)
        for tok, t in zip(r.result.tokens, r.result.timestamps):
            if tok.strip(): tokens.append([tok.strip(), round(st + t, 3)])
        vad.pop()
json.dump(dict(tokens=tokens), open(a.out, 'w'), ensure_ascii=False)
print(''.join(t for t, _ in tokens))
print(len(tokens), 'tokens →', a.out)
