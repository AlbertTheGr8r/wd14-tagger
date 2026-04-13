import shutil
import subprocess
import sys
from pathlib import Path
from src.tagger.inference import WD14Tagger
from src.converter.xmp_writer import convert_to_xmp as xmp_convert
from tqdm import tqdm


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".JPG", ".JPEG", ".PNG", ".WEBP"}


def check_exiftool():
    return shutil.which("exiftool") is not None


def convert_to_xmp(target_path: Path, recursive: bool = False):
    return xmp_convert(str(target_path), overwrite=False, recursive=recursive)


def cleanup_txt_files(target_path: Path, recursive: bool = False):
    """Delete .txt tag files."""
    pattern = "**/*.txt" if recursive else "*.txt"
    txt_files = list(target_path.glob(pattern))
    deleted = 0
    for txt_file in txt_files:
        try:
            base_name = txt_file.stem
            has_image = any(
                txt_file.with_suffix(ext).exists()
                for ext in [
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".webp",
                    ".JPG",
                    ".JPEG",
                    ".PNG",
                    ".WEBP",
                ]
            )
            if has_image:
                txt_file.unlink()
                deleted += 1
        except OSError as e:
            print(f"Skipping {txt_file.name}: {e}")
    return deleted


def run_tagging(
    target_dir: str,
    batch_size: int = 6,
    general_threshold: float = 0.35,
    character_threshold: float = 0.85,
    model_repo: str = "SmilingWolf/wd-swinv2-tagger-v3",
    recursive: bool = False,
    keep_txt: bool = False,
):
    target_path = Path(target_dir)
    if not target_path.exists():
        print(f"Error: Directory '{target_dir}' does not exist")
        return

    extensions = [
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.webp",
        "*.JPG",
        "*.JPEG",
        "*.PNG",
        "*.WEBP",
    ]

    if recursive:
        image_paths = []
        for ext in extensions:
            image_paths.extend(target_path.rglob(ext))
    else:
        image_paths = []
        for ext in extensions:
            image_paths.extend(target_path.glob(ext))

    image_paths = sorted(image_paths)
    print(f"Found {len(image_paths)} images")

    tagger = WD14Tagger(
        model_repo=model_repo,
        general_threshold=general_threshold,
        character_threshold=character_threshold,
    )

    for i in tqdm(range(0, len(image_paths), batch_size), desc="Tagging"):
        batch = image_paths[i : i + batch_size]
        predictions = tagger.predict(batch)

        for path, tags in predictions.items():
            if tags:
                txt_path = path.with_suffix(".txt")
                try:
                    with open(txt_path, "w", encoding="utf-8") as f:
                        f.write(tags)
                except OSError as e:
                    print(f"Could not write tags for {path.name}: {e}")

    skipped = tagger.skipped_count
    if skipped > 0:
        print(
            f"Processing complete. Processed {len(image_paths) - skipped} images, skipped {skipped}."
        )
    else:
        print(f"Processing complete. Processed {len(image_paths)} images.")

    if check_exiftool():
        converted = convert_to_xmp(target_path, recursive)
        if converted > 0:
            print(f"Created {converted} XMP sidecar files.")
            if not keep_txt:
                deleted = cleanup_txt_files(target_path, recursive)
                print(f"Deleted {deleted} .txt files.")
        else:
            print("No .txt files found to convert.")
    else:
        print(
            "XMP sidecar files not generated. exiftool not found.\n"
            "Install exiftool to enable XMP sidecars:\n"
            "  - Linux: sudo apt-get install exiftool\n"
            "  - macOS: brew install exiftool\n"
            "  - Windows: https://exiftool.org/"
        )


def run_cleanup(
    target_dir: str,
    recursive: bool = False,
    clean_xmp: bool = False,
    prune: bool = False,
    dry_run: bool = True,
    force: bool = False,
):
    target_path = Path(target_dir)
    if not target_path.exists():
        print(f"Error: Directory '{target_dir}' does not exist")
        return

    pattern = "**/*" if recursive else "*"
    extensions_to_clean = [".txt"]
    if clean_xmp:
        extensions_to_clean.append(".xmp")

    to_delete = []

    for ext in extensions_to_clean:
        for file in target_path.glob(f"{pattern}{ext}"):
            base_name = file.stem
            base_exists = any(
                (file.with_suffix(img_ext)).exists() for img_ext in IMAGE_EXTENSIONS
            )

            if prune:
                if not base_exists:
                    to_delete.append(file)
            else:
                if base_exists:
                    to_delete.append(file)

    if not to_delete:
        print("Nothing to clean.")
        return

    file_count = len(to_delete)
    print(f"{'[DRY RUN] ' if dry_run else ''}Found {file_count} files to delete.")

    if dry_run:
        print("Files that would be deleted:")
        for f in to_delete[:20]:
            print(f"  {f}")
        if file_count > 20:
            print(f"  ... and {file_count - 20} more")
        return

    if not force:
        response = input(f"Proceed with deletion? [y/N] ")
        if response.lower() not in ("y", "yes"):
            print("Cancelled.")
            return

    for f in to_delete:
        try:
            f.unlink()
        except OSError as e:
            print(f"Could not delete {f.name}: {e}")

    print("Cleanup complete.")


def run_xmp(target_dir: str, recursive: bool = False, overwrite: bool = False):
    if not check_exiftool():
        print("Error: exiftool not found.")
        print(
            "Install exiftool to enable XMP sidecar generation:\n"
            "  - Linux: sudo apt-get install exiftool\n"
            "  - macOS: brew install exiftool\n"
            "  - Windows: https://exiftool.org/"
        )
        return

    target_path = Path(target_dir)
    if not target_path.exists():
        print(f"Error: Directory '{target_dir}' does not exist")
        return

    converted = xmp_convert(target_dir, overwrite=overwrite, recursive=recursive)

    if converted > 0:
        print(f"Converted {converted} files to XMP.")


def print_help():
    print("Usage: uv run main.py <command> <folder_path> [options]")
    print("")
    print("Commands:")
    print("  tag                   Generate tags for images (default)")
    print("  xmp                   Convert existing .txt files to XMP sidecars")
    print("  clean                 Remove generated tag files")
    print("")
    print("Tag Options:")
    print("  --batch-size N        Batch size (default: 6)")
    print("  --gen-thresh N        General threshold (default: 0.35)")
    print("  --char-thresh N       Character threshold (default: 0.85)")
    print(
        "  --model MODEL         Model repo (default: SmilingWolf/wd-swinv2-tagger-v3)"
    )
    print("  --recursive           Process subdirectories")
    print("  --txt                 Keep .txt files after XMP conversion")
    print("")
    print("XMP Options:")
    print("  --recursive           Process subdirectories")
    print("  --overwrite           Overwrite existing XMP files")
    print("")
    print("Clean Options:")
    print("  --clean               Delete .txt tag files (default)")
    print("  --clean-all           Delete both .txt and .xmp sidecar files")
    print("  --prune               Delete orphaned .txt/.xmp files (no matching image)")
    print("  --recursive           Clean subdirectories")
    print("  --dry-run             Preview what would be deleted (default)")
    print("  --force               Skip confirmation prompt")
    print("")
    print("Examples:")
    print("  uv run main.py tag ./photos --recursive")
    print("  uv run main.py tag ./photos --txt")
    print("  uv run main.py xmp ./photos")
    print("  uv run main.py clean ./photos --dry-run")
    print("  uv run main.py clean ./photos --clean-all --force")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h", "help"):
        print_help()
        sys.exit(0)

    if sys.argv[1] == "tag":
        command = "tag"
        if len(sys.argv) < 3:
            print("Error: Directory path required")
            sys.exit(1)
        target_dir = sys.argv[2]
        args = sys.argv[3:]
    elif sys.argv[1] == "xmp":
        command = "xmp"
        if len(sys.argv) < 3:
            print("Error: Directory path required")
            sys.exit(1)
        target_dir = sys.argv[2]
        args = sys.argv[3:]
    elif sys.argv[1] == "clean":
        command = "clean"
        if len(sys.argv) < 3:
            print("Error: Directory path required")
            sys.exit(1)
        target_dir = sys.argv[2]
        args = sys.argv[3:]
    else:
        print("Error: Command required. Use 'tag', 'xmp', or 'clean'.")
        print("Examples:")
        print("  uv run main.py tag ./photos")
        print("  uv run main.py xmp ./photos")
        print("  uv run main.py clean ./photos")
        sys.exit(1)

    if command == "tag":
        batch_size = 6
        general_threshold = 0.35
        character_threshold = 0.85
        model_repo = "SmilingWolf/wd-swinv2-tagger-v3"
        recursive = False
        keep_txt = False

        i = 0
        while i < len(args):
            if args[i] == "--batch-size" and i + 1 < len(args):
                batch_size = int(args[i + 1])
                i += 2
            elif args[i] == "--gen-thresh" and i + 1 < len(args):
                general_threshold = float(args[i + 1])
                i += 2
            elif args[i] == "--char-thresh" and i + 1 < len(args):
                character_threshold = float(args[i + 1])
                i += 2
            elif args[i] == "--model" and i + 1 < len(args):
                model_repo = args[i + 1]
                i += 2
            elif args[i] == "--recursive":
                recursive = True
                i += 1
            elif args[i] == "--txt":
                keep_txt = True
                i += 1
            else:
                i += 1

        run_tagging(
            target_dir,
            batch_size=batch_size,
            general_threshold=general_threshold,
            character_threshold=character_threshold,
            model_repo=model_repo,
            recursive=recursive,
            keep_txt=keep_txt,
        )

    elif command == "xmp":
        recursive = False
        overwrite = False

        i = 0
        while i < len(args):
            if args[i] == "--recursive":
                recursive = True
                i += 1
            elif args[i] == "--overwrite":
                overwrite = True
                i += 1
            else:
                i += 1

        run_xmp(target_dir, recursive=recursive, overwrite=overwrite)

    elif command == "clean":
        recursive = False
        clean_xmp = False
        prune = False
        dry_run = True
        force = False

        i = 0
        while i < len(args):
            if args[i] == "--recursive":
                recursive = True
                i += 1
            elif args[i] == "--clean":
                i += 1
            elif args[i] == "--clean-all":
                clean_xmp = True
                i += 1
            elif args[i] == "--prune":
                prune = True
                i += 1
            elif args[i] == "--dry-run":
                dry_run = True
                i += 1
            elif args[i] == "--force":
                force = True
                dry_run = False
                i += 1
            else:
                i += 1

        if not clean_xmp and not prune:
            pass

        run_cleanup(
            target_dir,
            recursive=recursive,
            clean_xmp=clean_xmp,
            prune=prune,
            dry_run=dry_run,
            force=force,
        )
