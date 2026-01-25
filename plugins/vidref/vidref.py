#!/usr/bin/env python3
"""
yt2ref.py - Generate reference markdown from YouTube video artifacts

This script processes the output from yt-dlp (transcript, chapters, screenshots)
and generates a combined reference.md file suitable for Claude Skill references.
"""

import json
import re
import sys
from pathlib import Path
from datetime import timedelta


def parse_vtt_timestamp(ts: str) -> float:
    """Parse VTT timestamp (HH:MM:SS.mmm) to seconds."""
    parts = ts.replace(',', '.').split(':')
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return float(parts[0])


def format_timestamp(seconds: float) -> str:
    """Format seconds as H:MM:SS or MM:SS."""
    td = timedelta(seconds=int(seconds))
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def parse_vtt(vtt_path: Path) -> list[dict]:
    """Parse VTT file into list of {start, end, text} segments."""
    segments = []
    if not vtt_path.exists():
        return segments

    content = vtt_path.read_text(encoding='utf-8')

    # Remove WEBVTT header and metadata
    lines = content.split('\n')

    current_segment = None
    timestamp_pattern = re.compile(r'(\d{1,2}:)?(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d{1,2}:)?(\d{2}):(\d{2})[.,](\d{3})')

    for line in lines:
        line = line.strip()

        # Skip empty lines, WEBVTT header, and numeric cue identifiers
        if not line or line.startswith('WEBVTT') or line.isdigit():
            if current_segment and current_segment.get('text'):
                segments.append(current_segment)
                current_segment = None
            continue

        # Check for timestamp line
        match = timestamp_pattern.match(line)
        if match:
            if current_segment and current_segment.get('text'):
                segments.append(current_segment)

            # Parse start time
            start_h = int(match.group(1)[:-1]) if match.group(1) else 0
            start_m = int(match.group(2))
            start_s = int(match.group(3))
            start_ms = int(match.group(4))
            start = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000

            # Parse end time
            end_h = int(match.group(5)[:-1]) if match.group(5) else 0
            end_m = int(match.group(6))
            end_s = int(match.group(7))
            end_ms = int(match.group(8))
            end = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000

            current_segment = {'start': start, 'end': end, 'text': ''}
            continue

        # Skip lines that look like metadata (contain -->)
        if '-->' in line:
            continue

        # Text content - strip VTT tags like <c> </c>
        clean_text = re.sub(r'<[^>]+>', '', line)
        if current_segment is not None and clean_text:
            if current_segment['text']:
                current_segment['text'] += ' '
            current_segment['text'] += clean_text

    # Don't forget the last segment
    if current_segment and current_segment.get('text'):
        segments.append(current_segment)

    return segments


def get_transcript_for_range(segments: list[dict], start: float, end: float) -> str:
    """Extract transcript text for a time range."""
    texts = []
    seen = set()  # Deduplicate repeated lines (common in auto-subs)

    for seg in segments:
        # Check if segment overlaps with our range
        if seg['end'] >= start and seg['start'] < end:
            text = seg['text'].strip()
            # Simple deduplication
            if text and text not in seen:
                seen.add(text)
                texts.append(text)

    return ' '.join(texts)


def get_slides_sorted(slides_dir: Path) -> list[tuple[float, str]]:
    """Get all slides sorted by timestamp, returns list of (seconds, filename)."""
    slides = []
    pattern = re.compile(r'^(\d{2})_(\d{2})_(\d{2})\.png$')

    for slide in slides_dir.glob('*.png'):
        match = pattern.match(slide.name)
        if match:
            hours, minutes, seconds = int(match.group(1)), int(match.group(2)), int(match.group(3))
            total_seconds = hours * 3600 + minutes * 60 + seconds
            slides.append((total_seconds, slide.name))

    return sorted(slides, key=lambda x: x[0])


def get_chapter_for_timestamp(chapters: list[dict], timestamp: float, duration: float) -> dict | None:
    """Find which chapter a timestamp belongs to."""
    for i, chapter in enumerate(chapters):
        start = chapter['start_time']
        end = chapter.get('end_time', chapters[i + 1]['start_time'] if i + 1 < len(chapters) else duration)
        if start <= timestamp < end:
            return chapter
    return None


def generate_reference(output_dir: Path) -> str:
    """Generate reference markdown from processed video artifacts."""
    chapters_file = output_dir / 'chapters.json'
    transcript_file = output_dir / 'transcript.vtt'
    slides_dir = output_dir / 'slides'
    info_file = output_dir / 'video.info.json'

    # Load metadata
    with open(chapters_file) as f:
        chapters_data = json.load(f)

    title = chapters_data.get('title', 'Video Reference')
    duration = chapters_data.get('duration', 0)
    chapters = chapters_data.get('chapters', [])

    # Get video URL from info.json if available
    video_url = ""
    if info_file.exists():
        with open(info_file) as f:
            info = json.load(f)
            video_url = info.get('webpage_url', info.get('original_url', ''))

    # Parse transcript
    segments = parse_vtt(transcript_file)

    # Get all slides
    slides = get_slides_sorted(slides_dir)
    interval = 30  # Default interval between screenshots

    # Build markdown
    lines = [
        f"# {title}",
        "",
    ]

    if video_url:
        lines.extend([
            f"**Source:** {video_url}",
            "",
        ])

    lines.extend([
        f"**Duration:** {format_timestamp(duration)}",
        f"**Slides:** {len(slides)} screenshots (every {interval}s)",
        "",
        "---",
        "",
    ])

    # Track current chapter to show headers
    current_chapter_title = None

    # Process each slide with its transcript segment
    for i, (timestamp, slide_name) in enumerate(slides):
        # Determine end time for transcript
        if i + 1 < len(slides):
            end_time = slides[i + 1][0]
        else:
            end_time = duration

        # Check if we're entering a new chapter
        chapter = get_chapter_for_timestamp(chapters, timestamp, duration)
        if chapter:
            chapter_title = chapter.get('title', '')
            if chapter_title != current_chapter_title:
                current_chapter_title = chapter_title
                lines.append(f"## {chapter_title}")
                lines.append("")

        # Add slide
        lines.append(f"### {format_timestamp(timestamp)}")
        lines.append("")
        lines.append(f"![{format_timestamp(timestamp)}](slides/{slide_name})")
        lines.append("")

        # Add transcript for this segment
        transcript = get_transcript_for_range(segments, timestamp, end_time)
        if transcript:
            # Wrap transcript, breaking into paragraphs
            paragraphs = []
            words = transcript.split()
            current = []
            for word in words:
                current.append(word)
                if len(current) >= 50:  # ~50 words per paragraph
                    paragraphs.append(' '.join(current))
                    current = []
            if current:
                paragraphs.append(' '.join(current))

            for para in paragraphs:
                lines.append(f"> {para}")
                lines.append(">")
            lines.append("")

        lines.append("---")
        lines.append("")

    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: yt2ref.py <output-dir>")
        sys.exit(1)

    output_dir = Path(sys.argv[1])

    if not output_dir.exists():
        print(f"Error: Output directory {output_dir} does not exist")
        sys.exit(1)

    reference_md = generate_reference(output_dir)

    output_file = output_dir / 'reference.md'
    output_file.write_text(reference_md, encoding='utf-8')
    print(f"Reference saved to {output_file}")


if __name__ == '__main__':
    main()
