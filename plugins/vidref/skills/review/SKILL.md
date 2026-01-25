---
name: review
description: Review extracted video reference material with slides and transcript. Use when user wants to understand or discuss a video that was extracted with vidref.
---

# Review Video Reference

Load and review extracted video reference material including slides and transcript.

## Usage

When asked to review a video reference:

1. **Read the reference.md** to get the structure, chapters, and transcript:
   ```
   Read output/reference.md
   ```

2. **Read slides for visual context** - The slides are PNG images that Claude can view:
   ```
   Read output/slides/00_00_00.png   # First slide
   Read output/slides/00_05_00.png   # 5 minutes in
   ```

3. **For comprehensive review**, read multiple key slides:
   - Read slides at chapter boundaries
   - Read slides where transcript mentions diagrams, code, or visual elements

## Batch Reading Slides

To efficiently review the video, read slides in parallel at key timestamps:

```
# Read 6 slides spanning the video
Read output/slides/00_00_00.png
Read output/slides/00_10_00.png
Read output/slides/00_20_00.png
Read output/slides/00_30_00.png
Read output/slides/00_40_00.png
Read output/slides/00_49_00.png
```

## Tips

- Start by reading reference.md to understand the video structure
- Read slides where the transcript mentions visual content ("as you can see", "this diagram", "on screen")
- For technical videos, slides often contain code, architecture diagrams, or key points
- The transcript has repetition from auto-captions - focus on the visual slides for clarity
