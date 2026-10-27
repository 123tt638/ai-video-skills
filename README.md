# AI 视频 Skills（可乐 × Claude）

给 Claude / Claude Code 用的口播剪辑与 AI 广告导演 skills，以及它们需要的脚本和页面模板。

## Skills

| Skill | 用途 |
|---|---|
| `wangan-talking-head-edit` | 竖屏口播 + 广告素材 → 横屏网感快节奏口播（字幕新闻 × 综艺回合卡），含剪气口卡壳、抠像美颜压暗背景、分镜版、剪辑轨道图、成片展示。已出过成片 |
| `telestrator-breakdown-talk` | 体育战术板风拆解：播放 → 倒带 → 定格 → 画圈画箭头 |
| `dark-keynote-talk` | 暗色科技发布会风：黑舞台、单一亮色、界面元素卡拍、巨大数字 |
| `appetite-cut-talk` | 原创「食欲胶片」：食品快消广告拆解，菜单卡、蒸汽火星、滋滋声 |
| `director-slate-talk` | 原创「导演场记本」：场记板转场、镜头卡、线稿显影成片 |
| `shelf-pop-talk` | 原创「货架爆品」：货架、促销价签、扫码揭示、小票总结 |
| `ai-ad-director` | 为 Seedance 等 AI 视频模型写广告 / MV 分镜与提示词并审片 |

除 `wangan-talking-head-edit` 外，其余风格 skill 还没有实际出片，首次使用会先出 3 张风格帧确认。

**安装**：把 `skills/<名字>/` 文件夹放进 `~/.claude/skills/`（Claude Code），或在 claude.ai 的 Skills 设置里上传对应 `SKILL.md`。

## 工具（tools/）

| 文件 | 作用 |
|---|---|
| `asr_tokens.py` | SenseVoice + VAD 逐字时间轴 |
| `cut_talk.py` | 按保留区间剪掉气口和卡壳，并把逐字时间映射到剪后时间轴 |
| `mask.py` | u2net 人像遮罩视频（帧间平滑） |
| `prep_par.py` | 磨皮美颜 + 透明人物帧（WebP）+ 干净房间底板；可按帧区间多进程 |
| `common.py` / `make_timeline.py` | 关键词时间、分块字幕 → `timeline.json`（画面与混音共用的唯一时间轴） |
| `captions.example.json` | `make_timeline.py` 的输入示例：关键词标记 `marks` + 分块字幕 `caps` |

## 模板（templates/wangan-page/）

lemo-opuscar 页面约定（`window.render(t)`、`window.EV`）下的网感口播成片模板：`index.html`（一条已出片作品的完整画面代码，作参考：改 `ACCOUNT` / `BRAND`，并按自己的 `captions.json` 改 `M` 里的关键词名和各场景内容）、`mix.py`（120 BPM 原创配乐 + 程序音效 + 人声处理 + 闪避）、`build.sh`（渲染 → 混音 → −14 LUFS 母带，输出 `out/film.mp4`）、`TREATMENT.md`（结构模板）。放到 lemo-opuscar 的 `films/<名字>/` 下使用。

## 依赖与来源

- 渲染框架：[lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar)（MIT，需自行 clone，本仓库不包含其代码）。
- 语音识别：[sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) SenseVoice 模型（见 `asr_tokens.py` 注释中的下载地址）。
- 人像分割：rembg 发布的 `u2net_human_seg.onnx`（https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_human_seg.onnx）。
- Python：numpy、scipy、soundfile、opencv-python、pillow、onnxruntime、sherpa-onnx；系统：ffmpeg、Node 20+。

本仓库不含任何个人口播、广告素材或成片。

## 许可

MIT。各风格 skill 里提到的第三方风格参考仅作「语法」学习，不复制任何品牌、节目或作品的标识与素材。
