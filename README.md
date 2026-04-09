# WD14 Tagger

Generate Danbooru-style tags for images and create XMP sidecar files for Immich.

## Installation

```bash
uv sync
```

Requires:
- Python 3.11+
- CUDA-capable GPU (recommended for speed)
- ExifTool (for XMP conversion)

### Install ExifTool

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get install exiftool
```

**macOS:**
```bash
brew install exiftool
```

**Windows:**
Download from https://exiftool.org/

## Usage

### Generate Tags

Tag your images using the WD14 Tagger:

```bash
uv run main.py tag <directory> [options]
```

**Options:**
- `--batch-size N` - Batch size (default: 6)
- `--gen-thresh N` - General tag threshold (default: 0.35)
- `--char-thresh N` - Character tag threshold (default: 0.85)
- `--model MODEL` - Model repo (default: SmilingWolf/wd-swinv2-tagger-v3)
- `--recursive` - Process subdirectories

**Examples:**
```bash
uv run main.py tag ./photos
uv run main.py tag ./photos --batch-size 8 --recursive
```

### Convert to XMP Sidecars

Convert the generated `.txt` files to XMP sidecar files:

```bash
cd <directory>
for f in *.txt; do
    base="${f%.txt}"
    exts="jpg jpeg png webp"
    for ext in $exts; do
        if [ -f "${base}.${ext}" ]; then
            tags=$(cat "$f")
            exiftool -tagsfromfile "${base}.${ext}" -xmp:subject="$tags" -o "${base}.xmp" "${base}.${ext}"
            break
        fi
    done
done
```

### Cleanup Generated Files

Remove tag files to clean up your directory:

```bash
uv run main.py clean <directory> [options]
```

**Options:**
- `--clean` - Delete `.txt` tag files (default)
- `--clean-all` - Delete both `.txt` and `.xmp` sidecar files
- `--prune` - Delete orphaned `.txt`/`.xmp` files (no matching image)
- `--recursive` - Clean subdirectories
- `--dry-run` - Preview what would be deleted (default)
- `--force` - Skip confirmation prompt

**Examples:**
```bash
# Preview what would be deleted
uv run main.py clean ./photos --dry-run

# Delete .txt files (with confirmation)
uv run main.py clean ./photos

# Delete both .txt and .xmp (skip confirmation)
uv run main.py clean ./photos --clean-all --force

# Delete orphaned files
uv run main.py clean ./photos --prune --force
```

## Threshold Guide

| Threshold | Effect |
|-----------|--------|
| 0.35 / 0.85 | Standard Danbooru defaults (recommended) |
| 0.50 / 0.90 | High precision, fewer tags |
| 0.25 / 0.70 | More tags, lower precision |

- **General tags** (blue hair, sword): Default 0.35
- **Character tags** (Lumine, March 7th): Default 0.85

## Available Models

| Model | VRAM | Accuracy | Speed |
|-------|------|----------|-------|
| wd-vit-tagger-v3 | ~4GB | Good | Fast |
| wd-swinv2-tagger-v3 | ~6GB | Best | Moderate |
| wd-v1-4-convnext-tagger-v3 | ~5GB | Good | Moderate |

For RTX 4060 (8GB): Use `wd-swinv2-tagger-v3` with batch size 6-8.

## Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Tag Images                                         │
│ uv run main.py tag ./photos                                 │
│                                                             │
│ Input:  photos/*.jpg, *.png, *.webp                        │
│ Output: photos/*.txt (non-destructive)                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Create XMP Sidecars                                │
│ (See conversion command above)                             │
│                                                             │
│ Input:  photos/*.txt                                        │
│ Output: photos/*.xmp (new files, originals untouched)      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Cleanup (Optional)                                 │
│ uv run main.py clean ./photos --clean-all --force          │
│                                                             │
│ Removes .txt and .xmp files, preserves original images    │
└─────────────────────────────────────────────────────────────┘
```

## Safety

- **Tagging**: Only reads images, generates new `.txt` files
- **XMP Conversion**: Creates new `.xmp` files, original images never modified
- **Cleanup**: Only deletes `.txt`/`.xmp` files that have matching images (use `--prune` for orphans)
- **Dry-run default**: Preview mode shows what would be deleted before confirming

## Testing

```bash
uv run pytest tests/
```