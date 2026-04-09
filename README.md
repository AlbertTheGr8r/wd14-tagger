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

### Step 1: Generate Tags

Tag your images using the WD14 Tagger:

```bash
uv run main.py <directory> [options]
```

**Options:**
- `--batch-size N` - Batch size (default: 6)
- `--gen-thresh N` - General tag threshold (default: 0.35)
- `--char-thresh N` - Character tag threshold (default: 0.85)
- `--model MODEL` - Model repo (default: SmilingWolf/wd-swinv2-tagger-v3)
- `--recursive` - Process subdirectories

**Example:**
```bash
uv run main.py ./photos --batch-size 6 --recursive
```

### Step 2: Convert to XMP Sidecars

Convert the generated `.txt` files to XMP sidecar files:

```bash
python -m src.converter.xmp_writer <directory> [--overwrite]
```

Or using ExifTool directly:
```bash
cd <directory>
exiftool -ext txt -tagsfromfile %d%f.jpg "-xmp:subject<$(cat %d%f.txt)" -o %d%f.xmp .
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
│ uv run main.py ./photos                                    │
│                                                             │
│ Input:  photos/*.jpg, *.png, *.webp                       │
│ Output: photos/*.txt (non-destructive)                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Create XMP Sidecars                                │
│ python -m src.converter.xmp_writer ./photos                 │
│                                                             │
│ Input:  photos/*.txt                                        │
│ Output: photos/*.xmp (new files, originals untouched)      │
└─────────────────────────────────────────────────────────────┘
```

## Safety

- **Step 1**: Only reads images, generates new `.txt` files
- **Step 2**: Creates new `.xmp` files, original images never modified
- No overwrites unless explicitly specified with `--overwrite`

## Testing

```bash
uv run pytest tests/
```