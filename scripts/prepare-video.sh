#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/prepare-video.sh [--force] INPUT.MOV [name]

Create docs/<name>.mp4 and docs/<name>-preview.gif from an iPhone video.
The name defaults to the input filename, converted to a URL-friendly form.
Use --force to replace files made by an earlier run.
EOF
}

force=0
if [[ ${1:-} == --force ]]; then
  force=1
  shift
fi

if [[ $# -lt 1 || $# -gt 2 || ${1:-} == --help ]]; then
  usage
  [[ ${1:-} == --help ]] && exit 0
  exit 2
fi

input=$1
if [[ ! -f $input ]]; then
  printf 'Video not found: %s\n' "$input" >&2
  exit 1
fi

for program in ffmpeg ffprobe; do
  if ! command -v "$program" >/dev/null 2>&1; then
    printf '%s is required. Install it with: brew install ffmpeg\n' "$program" >&2
    exit 1
  fi
done

if ! ffprobe -v error -select_streams v:0 -show_entries stream=index \
  -of csv=p=0 "$input" | grep -q .; then
  printf 'No video stream found in: %s\n' "$input" >&2
  exit 1
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_dir=$(cd -- "$script_dir/.." && pwd)
output_dir=${VIDEO_OUTPUT_DIR:-"$repo_dir/docs"}
mkdir -p -- "$output_dir"

filename=${input##*/}
stem=${filename%.*}
name=${2:-$stem}
slug=$(printf '%s' "$name" | LC_ALL=C tr '[:upper:]' '[:lower:]' \
  | LC_ALL=C sed -E 's/[^a-z0-9._-]+/-/g; s/^-+//; s/-+$//')
if [[ -z $slug || $slug == .* ]]; then
  printf 'Choose a name containing letters or numbers.\n' >&2
  exit 1
fi

mp4="$output_dir/$slug.mp4"
preview="$output_dir/$slug-preview.gif"
if (( ! force )) && [[ -e $mp4 || -e $preview ]]; then
  printf 'Output already exists for "%s". Use another name or --force.\n' "$slug" >&2
  exit 1
fi

ffmpeg -y -hide_banner -loglevel error -i "$input" \
  -map 0:v:0 -map '0:a:0?' -map_metadata -1 \
  -vf 'scale=1280:1280:force_original_aspect_ratio=decrease:force_divisible_by=2,format=yuv420p' \
  -c:v libx264 -preset medium -crf 24 \
  -c:a aac -b:a 128k -movflags +faststart "$mp4"

ffmpeg -y -hide_banner -loglevel error -i "$input" \
  -filter_complex '[0:v]fps=6,scale=400:400:force_original_aspect_ratio=decrease:force_divisible_by=2:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=64:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5' \
  -loop 0 "$preview"

printf 'Created:\n  %s\n  %s\n\n' "$mp4" "$preview"
if [[ $output_dir == "$repo_dir/docs" ]]; then
  printf 'Paste this into README.md:\n\n'
  printf '[![Animated preview of %s](docs/%s-preview.gif)](docs/%s.mp4)\n\n' "$slug" "$slug" "$slug"
  printf '[Watch with sound](docs/%s.mp4)\n' "$slug"
fi
