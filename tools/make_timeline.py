"""timeline.json：画面与混音共用的唯一时间轴（关键词时间 + 分块字幕）。

用法：TOKENS=work/tokens_cut.json TIMELINE=film/timeline.json python make_timeline.py captions.json
captions.json 结构见 captions.example.json：
  marks：{名字: 口播原文里的子串}  → M[名字] = 该子串第一个字在剪后口播中的时间（页面按 M 切场景）
  caps： [[口播原文（用于对时间）, [依次砸入的字幕块], 关键词], ...]  按口播顺序排列
"""
import os, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import wt, RAW, _times, OFF, TALK_LEN, AD_LEN

cfg = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'captions.json'))
M = {k: wt(v) for k, v in cfg['marks'].items()}

caps, pos = [], 0
for raw, chunks, kw in cfg['caps']:
    i = RAW.find(raw, pos); assert i >= 0, raw
    j = i + len(raw) - 1; pos = j + 1
    a, b = _times[i], _times[j] + 0.35
    # 每块的起点 = 原文按比例对应那个字的时间
    starts = [_times[i + int(len(raw) * k / len(chunks))] for k in range(len(chunks))]
    caps.append(dict(t0=a, t1=b, chunks=chunks, starts=starts, kw=kw))
for k in range(len(caps) - 1):           # 间隔很短就撑到下一句；每条至少 1.8 s
    if caps[k + 1]['t0'] - caps[k]['t1'] < 0.7: caps[k]['t1'] = caps[k + 1]['t0'] - 0.02
    caps[k]['t1'] = max(caps[k]['t1'], min(caps[k]['t0'] + 1.8, caps[k + 1]['t0'] - 0.02))
json.dump(dict(OFF=OFF, TALK=TALK_LEN, AD=AD_LEN, M=M, caps=caps), open(os.environ.get('TIMELINE', 'film/timeline.json'), 'w'),
          ensure_ascii=False, indent=0)
print('ok', len(caps))
