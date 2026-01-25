---
name: extract
description: Extract transcripts and screenshots from videos for reference material. Use when user wants to create skill references from video tutorials or presentations.
---

# Video Reference Extraction

Extract transcripts and screenshots from videos for use as Claude Skill reference material.

## Usage

```bash
# Basic extraction
vidref "https://www.youtube.com/watch?v=VIDEO_ID"

# Custom output directory
vidref "https://www.youtube.com/watch?v=VIDEO_ID" ./my-output
```

## What This Does

1. Downloads video metadata and transcript using `yt-dlp`
2. Extracts chapter information (or creates segments for videos without chapters)
3. Downloads the video and extracts screenshots every 30 seconds
4. Generates a combined `reference.md` with slides and transcript segments

## Output Structure

```
output/
├── transcript.vtt        # Timestamped transcript (VTT format)
├── chapters.json         # Chapter metadata
├── video.info.json       # Full video metadata
├── video.mp4            # Downloaded video (can be deleted after)
├── slides/
│   ├── 00_00_00.png      # Screenshots every 30 seconds
│   ├── 00_00_30.png
│   └── ...
└── reference.md          # Combined markdown reference
```

## Workflow

When asked to extract reference material from a video:

1. **Run the extraction:**
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/vidref "VIDEO_URL" output_directory
   ```

2. **Review the output:**
   - Check `reference.md` for the combined output
   - Verify slides are captured at the right moments
   - Check transcript quality

3. **Clean up (optional):**
   - Delete `video.mp4` if not needed
   - Delete `video.info.json` if not needed

4. **Use in skills:**
   - Copy relevant content to skill references
   - Edit transcript for clarity if needed
   - Organize slides as needed

## Tips

- Videos with chapters produce better organized output
- Screenshots are taken every 30 seconds for comprehensive coverage
- Auto-generated transcripts may have errors - manual review recommended
- Supports any site that yt-dlp supports (YouTube, Vimeo, etc.)
