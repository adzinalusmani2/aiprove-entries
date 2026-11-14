#!/bin/bash
# Assemble video.mp4: one static frame per segment, shown for exactly its
# (slightly sped-up) narration duration. Raw narration totals 69.02s;
# atempo=1.15 brings it to ~60.0s, matching the sixty-second brief.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p clips
# sped durations (orig / 1.15), rounded to 2dp
DURS=(9.95 10.69 10.56 8.97 7.66 12.19)
for i in 1 2 3 4 5 6; do
  d="${DURS[$((i-1))]}"
  ffmpeg -y -v error -loop 1 -framerate 30 -i "frames/frame${i}.png" \
    -i "audio/seg${i}.mp3" \
    -filter_complex "[1:a]atempo=1.15[aout]" \
    -map 0:v -map "[aout]" -t "$d" \
    -c:v libx264 -pix_fmt yuv420p -r 30 -c:a aac -b:a 128k \
    -video_track_timescale 30 "clips/clip${i}.mp4"
  echo "clip${i}: ${d}s"
done
printf "file 'clip1.mp4'\nfile 'clip2.mp4'\nfile 'clip3.mp4'\nfile 'clip4.mp4'\nfile 'clip5.mp4'\nfile 'clip6.mp4'\n" > clips/list.txt
ffmpeg -y -v error -f concat -safe 0 -i clips/list.txt -c copy video.mp4
echo "--- video.mp4 ---"
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height -show_entries format=duration,size -of default=noprint_wrappers=1 video.mp4
ls -la video.mp4
