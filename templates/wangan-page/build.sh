#!/bin/sh
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
LIB=${LIB:-$(cd "$HERE/../.." && pwd)}
export LIB
[ -n "$PLAYWRIGHT_CHROME" ] && export PLAYWRIGHT_CHROME   # 网络拦截浏览器下载时，指向本机 headless_shell
cd "$LIB"
mkdir -p "$HERE/out"
node core/render/events.mjs "$HERE"
node core/render/video.mjs "$HERE" --fps 30 --workers 2 --out "$HERE/out/video.mp4"
"$LIB/.venv/bin/python" "$HERE/mix.py"
sh core/render/mux.sh "$HERE/out/video.mp4" "$HERE/out/mix.wav" "$HERE/out/film.mp4" 30 1
echo BUILD-DONE
