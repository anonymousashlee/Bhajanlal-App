#!/usr/bin/env bash
# Launch GTA: Vice City — serves the folder and opens the game in your browser.
cd "$(dirname "$0")"
PORT="${1:-8791}"
python3 -m http.server "$PORT" >/dev/null 2>&1 &
SRV=$!
sleep 1
URL="http://127.0.0.1:$PORT/gta-vice-city-full.html"
echo "GTA: Vice City -> $URL"
open "$URL" 2>/dev/null || echo "Open $URL in your browser"
echo "Press Ctrl+C to stop."
wait $SRV
