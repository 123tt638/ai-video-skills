---
name: "wangan-talking-head-edit"
description: "把竖屏真人口播+广告/案例素材剪成横屏网感快节奏口播（字幕新闻+综艺回合卡风格），含剪气口、抠像调色、分镜版、剪辑轨道图、成片展示。"
---

# 横屏网感口播剪辑（字幕新闻 × 综艺回合卡）

用户交来：一条口播视频（常为竖屏 720×1280）+ 一条要拆解的广告/案例成片。产出：1920×1080 横屏网感口播，口播结束后完整展示成片。全程中文和用户沟通（用户叫我「可乐」）。

## 用户已确认过的审美基线（不要再问）
- 风格 = lemo-opuscar 的「字幕新闻 Caption News」骨架 + 「综艺节奏扁平 Game Show Flat」回合卡/判定词混用。
- 节奏快：开场 1.6 s 成片钩子；每个步骤一张糖果色条纹回合卡（ROUND 1…/FINAL，0.8 s）；关键词出现时贴纸落下、判定词（快切!/停半拍!/更直观!）砸出；镜头切换带 0.05 s 白闪。
- 口播画面：原房间做背景但压暗+虚化，人物抠像放前景、暖色轮廓光、肤色磨皮提亮偏暖；句与句之间换景别（close/mid/right）遮跳切。
- 字幕：左下 x120、y≈948，Noto Sans CJK SC 900 / 88px，按块（2–3 块）依次砸入，每句只一个关键词垫蜜黄 #FFC21A 底。
- 配色：墨黑 #0E0E0C、象牙 #F7F5EF、蜜黄 #FFC21A、番茄红 #FF4A3D + 综艺糖果色。
- 拆解段落：广告微距全屏快切+REC 取景框；分镜版（9 宫格分镜表，荧光笔扫出被提到的镜头再逐镜推近）；剪辑轨道版图（V1 画面/T1 字幕/A1 音效/A2 音乐 + 播放头 + 判定词）；全屏段落右下角圆形口播小窗。
- 结尾：「BONUS 成片展示」回合卡 → 21:9 成片完整播放（自带原声）。
- 左上角标默认「AI 广告课」，用户给账号名就替换。

## 流程

### 0. 先确认/准备
- 运行第三方仓库脚本前必须得到用户明确许可（用户的长期规矩）；先读文档和脚本。
- lemo-opuscar：`git clone --depth 1 https://github.com/lemomo-ai/lemo-opuscar.git`，读 AGENTS.md、styles/caption-news/STYLE.md、styles/game-show/STYLE.md、core/README.md。依赖：`uv venv --python 3.12 .venv && uv pip install -r requirements.txt -r requirements-music.txt`；playwright 浏览器下载会被网络拦，设 `PLAYWRIGHT_CHROME=/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell`。
- 项目放 `films/<name>/`，先写 TREATMENT.md（三种结构 + 选择）。

### 1. 口播转写与精剪
- ASR：sherpa-onnx SenseVoice（zh），`use_itn=False` 取 `result.tokens` + `result.timestamps` 得逐字时间；VAD 只做粗分段。
- 列出要删的：开头/句间长停顿（缩到≈0.1–0.3 s）、语气词「嗯」、卡壳重复（如「需要在 / 你你」只留后一次）。按 token 时间写 keep 区间列表，ffmpeg trim/atrim + 12–15 ms 音频淡入淡出 concat 成 cut.mov（30 fps）。
- 用 ASR 复听 cut 音频确认没切坏；再把 token 时间映射到剪后时间轴（tokens_cut.json）。
- 字幕显示文字要清理错字，但不擅改观点；拿不准的词（同音误识）交付时请用户确认。

### 2. 调色 + 抠像 + 美颜
- 调色：`eq=contrast=1.07:saturation=1.08:gamma=0.98,colorbalance(暖高光),curves 轻 S,unsharp` → graded.mp4。
- 人像遮罩：rembg 的 u2net_human_seg.onnx（GitHub release 可下：danielgatis/rembg/releases/download/v0.0.0/u2net_human_seg.onnx），onnxruntime 320×320 推理，帧间 0.4/0.6 平滑 → mask.mp4（约 0.8 s/帧，后台跑）。
- 人物帧：YCrCb 肤色区域 bilateralFilter 70% 混合磨皮、肤色微暖提亮、gamma 0.94；alpha = clip((m-0.12)/0.76) 轻羽化 → `person/%05d.webp`（带透明，q90）。只有 2 核时按帧区间分两个进程并行。
- 房间底板：累加无人像素平均 + inpaint → room_plate.jpg（页面里再 blur 18px、亮度 0.42、暖色径向光、暗角）。

### 3. 素材
- 成片逐帧 `ad/%04d.jpg`（30 fps）；21:9→16:9 用中心 1120×630 裁切。
- 分镜表（2× 分辨率 PNG）：按成片切点取 9 镜代表帧 + 编号/景别运镜/时间段/描述；剪辑轨道缩略图 thumb_0..8。

### 4. 时间轴（唯一来源 timeline.json）
- OFF=1.6（钩子长度）、TALK、AD；M = 关键词在剪后口播中的时间（wt(子串)）；caps = [{t0,t1,chunks,starts,kw}]，块起点按原文比例取逐字时间；字幕至少 1.8 s 或撑到下一句。

### 5. 页面（films/<name>/index.html，Canvas 2D，`window.render = async t => …`，video.mjs 会 await）
- 场景判定按 M：钩子 / 口播镜头 / 回合卡 / micro 全屏快切 / 分镜表 board / 剪辑轨道 timeline / 品牌落版 brand / 结尾贴纸 / 成片展示。
- 必备函数：caption()（块砸入 scale 1.3→1 back-ease，关键词黄底左→右擦入）、sticker()（扁平+墨线+硬投影）、roundCard()（斜条纹滚动+卡片落下+爆线）、judge()（斜角大描边字+爆线）、drawPerson()（暖色 shadowBlur 轮廓光）、drawPip()、bug()/tag()/credit()。
- window.EV 由画面事件生成（hit/riser/jingle/pop/judge/cut/slam/whoosh/shutter），供混音对齐。
- 先 `node core/render/still.mjs <film> t1 t2 … --out 目录` 抽帧 + core/render/sheet.py 拼图检查，再全片渲染。

### 6. 声音（mix.py，用 core/audio/sfx.py）
- 120 BPM 明亮流行循环（I–V–vi–IV）：饱和底鼓、军鼓、踩镲、带谐波的贝斯、方波铜管 stab、拨弦；钩子只用重鼓+镲。
- 事件音效：slam=click+thump，pop=pop+音阶拨弦，judge=铜管和弦+镲+铃，jingle=whoosh+crash+上行 stab，cut=whoosh+thump。
- 人声链：highpass80, afftdn, -2dB@220, +3dB@3.5k, 压缩 3:1, loudnorm -16。音乐比人声低约 12 dB 并按人声包络闪避到约 50%；成片段用广告原声。
- `sh core/render/mux.sh video.mp4 mix.wav out.mp4 30 1` → -14 LUFS / TP -1.2。

### 7. 交付
- build.sh：events.mjs → video.mjs（--fps 30 --workers 2，约 9 分钟/100 s）→ mix.py → mux。
- 自检：每 4 s 抽帧拼图、blackdetect、响度；说明哪些没法替用户听。
- 复制到 /mnt/user-data/outputs/ 用 SendUserFile 发出；中文简短说明结构、检查范围、需确认的字幕。

## 坑
- 自动安全检查偶发「no verdict」时直接重试同一命令；不要用 rm 通配符清目录，改用新的输出目录。
- 页面里图片缓存失败会缓存 null：底板等文件要在渲染前就位。
- 回合卡、全屏段落的时间要和关键词对齐，否则字幕与画面打架；带人物的段落里内容放左侧、人物在右（right 布局）。
