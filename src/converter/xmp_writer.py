import argparse
import subprocess
from pathlib import Path
from tqdm import tqdm


def convert_to_xmp(target_dir: str, overwrite: bool = False, recursive: bool = False):
    """Convert .txt tag files to XMP sidecar files using exiftool."""
    target_path = Path(target_dir)
    if not target_path.exists():
        print(f"Error: Directory '{target_dir}' does not exist")
        return 0

    pattern = "**/*.txt" if recursive else "*.txt"
    txt_files = list(target_path.glob(pattern))

    if not txt_files:
        print("No .txt files found")
        return 0

    converted = 0
    for txt_file in tqdm(txt_files, desc="Converting to XMP"):
        try:
            base_name = txt_file.stem
            search_path = txt_file.parent

            image_file = None
            for ext in [
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
                ".JPG",
                ".JPEG",
                ".PNG",
                ".WEBP",
            ]:
                candidate = search_path / f"{base_name}{ext}"
                if candidate.exists():
                    image_file = candidate
                    break

            if not image_file:
                print(f"Skipping {txt_file.name}: no matching image found")
                continue

            xmp_file = txt_file.with_suffix(".xmp")

            if xmp_file.exists() and not overwrite:
                print(
                    f"Skipping {base_name}.xmp: already exists (use --overwrite to replace)"
                )
                continue

            with open(txt_file, "r", encoding="utf-8") as f:
                tags = f.read()

            if overwrite and xmp_file.exists():
                xmp_file.unlink()

            cmd = [
                "exiftool",
                f"-xmp:subject={tags}",
                "-o",
                str(xmp_file),
                str(image_file),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error processing {txt_file.name}: {result.stderr}")
            else:
                converted += 1
                try:
                    txt_file.unlink()
                except OSError as e:
                    print(f"Could not delete {txt_file.name}: {e}")
        except OSError as e:
            print(f"Skipping {txt_file.name}: {e}")
            continue

    return converted


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert WD14 tag .txt files to XMP sidecars"
    )
    parser.add_argument("directory", help="Directory containing .txt tag files")
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing XMP files"
    )
    parser.add_argument(
        "--recursive", action="store_true", help="Process subdirectories"
    )
    args = parser.parse_args()

    convert_to_xmp(args.directory, overwrite=args.overwrite, recursive=args.recursive)
