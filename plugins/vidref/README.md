# vidref

Extract transcripts and screenshots from videos for Claude Skill reference material.

## Overview

`vidref` is a simple CLI wrapper around `yt-dlp` and `ffmpeg` that:

1. Downloads video transcripts (auto-generated or manual subtitles)
2. Extracts chapter metadata
3. Captures screenshots every 30 seconds throughout the video
4. Generates a combined markdown reference with slides organized by chapter

## Installation

Ensure you have the required dependencies installed:

```bash
# macOS
brew install yt-dlp ffmpeg jq

# Ubuntu/Debian
sudo apt install yt-dlp ffmpeg jq
```

## Usage

```bash
# Basic usage
vidref "https://www.youtube.com/watch?v=VIDEO_ID"

# Custom output directory
vidref "https://www.youtube.com/watch?v=VIDEO_ID" ./my-output
```

## Output

```
output/
├── transcript.vtt        # Timestamped transcript
├── chapters.json         # Chapter metadata
├── video.info.json       # Full video metadata from yt-dlp
├── video.mp4            # Downloaded video
├── slides/
│   ├── 00_00_00.png      # Screenshot every 30 seconds
│   ├── 00_00_30.png
│   ├── 00_01_00.png
│   └── ...
└── reference.md          # Combined markdown reference
```

## Skills

| Skill | Description |
|-------|-------------|
| `extract` | Guided workflow for extracting video references |
| `review` | Review extracted reference material with Claude |

## Dependencies

- `yt-dlp` - Video/metadata download (supports YouTube, Vimeo, and 1000+ sites)
- `ffmpeg` - Screenshot extraction
- `jq` - JSON processing
- `python3` - Markdown generation

## License

MIT
