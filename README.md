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

### Tag Images

Tag your images and automatically generate XMP sidecars:

```bash
uv run main.py tag <directory> [options]
```

**Options:**
- `--batch-size N` - Batch size (default: 6)
- `--gen-thresh N` - General tag threshold (default: 0.35)
- `--char-thresh N` - Character tag threshold (default: 0.85)
- `--model MODEL` - Model repo (default: SmilingWolf/wd-swinv2-tagger-v3)
- `--recursive` - Process subdirectories
- `--txt` - Keep .txt files after XMP conversion

**Examples:**
```bash
# Tag images (auto-generates XMP, deletes .txt files)
uv run main.py tag ./photos

# Keep .txt files alongside XMP sidecars
uv run main.py tag ./photos --txt

# Process subdirectories
uv run main.py tag ./photos --recursive
```

### Convert to XMP (Standalone)

Convert existing .txt files to XMP sidecars:

```bash
uv run main.py xmp <directory> [options]
```

**Options:**
- `--recursive` - Process subdirectories
- `--overwrite` - Overwrite existing XMP files

**Examples:**
```bash
# Convert existing .txt files to XMP
uv run main.py xmp ./photos

# Overwrite existing XMP files
uv run main.py xmp ./photos --overwrite
```

### Cleanup Generated Files

Remove tag files to clean up your directory:

```bash
uv run main.py clean <directory> [options]
```

**Options:**
- `--clean` - Delete .txt tag files (default)
- `--clean-all` - Delete both .txt and .xmp sidecar files
- `--prune` - Delete orphaned .txt/.xmp files (no matching image)
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

## Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ TAG IMAGES                                                  │
│ uv run main.py tag ./photos                                 │
│                                                             │
│ Input:  photos/*.jpg, *.png, *.webp                        │
│ Output: photos/*.xmp (auto-generated, .txt deleted)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ CLEANUP (Optional)                                         │
│ uv run main.py clean ./photos --clean-all --force          │
│                                                             │
│ Removes .txt and .xmp files, preserves original images    │
└─────────────────────────────────────────────────────────────┘
```

If exiftool is not installed, the tagger will:
- Generate .txt files normally
- Print a warning about XMP sidecars not being generated
- Keep the .txt files so you can convert them later

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

## Safety

- **Tagging**: Only reads images, generates .xmp files automatically
- **XMP Conversion**: Creates new .xmp files, original images never modified
- **Cleanup**: Only deletes .txt/.xmp files that have matching images (use --prune for orphans)
- **Dry-run default**: Preview mode shows what would be deleted before confirming

## Testing

```bash
uv run pytest tests/
```
