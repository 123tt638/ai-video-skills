"""剪气口和卡壳：按保留区间拼接口播，并把逐字时间映射到剪后时间轴。

用法：python cut_talk.py talk.mp4 keep.json tokens.json out_dir
keep.json = [[开始秒, 结束秒], ...]，按 tokens.json 里的逐字时间手工/半自动挑选：
  - 句间停顿缩到 0.1–0.3 s；删掉「嗯/啊」等语气词；卡壳重复只保留最后一次。
输出：out_dir/cut.mov（30fps，PCM 音频）、out_dir/tokens_cut.json
"""
import json, subprocess, sys, os
src, keepf, tokf, out = sys.argv[1:5]
os.makedirs(out, exist_ok=True)
K = json.load(open(keepf))
vf, af = [], []
for i, (a, b) in enumerate(K):
    vf.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}]")
    af.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={b - a - 0.015:.3f}:d=0.015[a{i}]")
n = len(K)
fc = ';'.join(vf + af) + ';' + ''.join(f'[v{i}][a{i}]' for i in range(n)) + f'concat=n={n}:v=1:a=1[v][a]'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-filter_complex', fc, '-map', '[v]', '-map', '[a]',
                '-c:v', 'libx264', '-crf', '12', '-preset', 'fast', '-r', '30', '-c:a', 'pcm_s16le', '-ar', '48000', f'{out}/cut.mov'], check=True)


def m(t):
    acc = 0
    for a, b in K:
        if t < a: return None
        if t <= b: return round(acc + t - a, 3)
        acc += b - a
    return None


toks = json.load(open(tokf))['tokens']
res = [[tok, m(t)] for tok, t in toks if m(t) is not None]
json.dump(res, open(f'{out}/tokens_cut.json', 'w'), ensure_ascii=False)
print('剪后时长', round(sum(b - a for a, b in K), 2), 's；保留字数', len(res))
