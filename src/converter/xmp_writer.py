import argparse
import subprocess
from pathlib import Path


def convert_to_xmp(target_dir: str, overwrite: bool = False):
    """Convert .txt tag files to XMP sidecar files using exiftool."""
    target_path = Path(target_dir)
    if not target_path.exists():
        print(f"Error: Directory '{target_dir}' does not exist")
        return

    txt_files = list(target_path.glob("*.txt"))
    if not txt_files:
        print("No .txt files found")
        return

    print(f"Converting {len(txt_files)} files to XMP...")

    for txt_file in txt_files:
        base_name = txt_file.stem
        image_extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".JPG",
            ".JPEG",
            ".PNG",
            ".WEBP",
        ]

        image_file = None
        for ext in image_extensions:
            candidate = target_path / f"{base_name}{ext}"
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

        cmd = [
            "exiftool",
            "-ext",
            "txt",
            "-tagsfromfile",
            str(image_file),
            f"-xmp:subject<{txt_file}",
            "-o",
            str(xmp_file),
            str(target_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error processing {txt_file.name}: {result.stderr}")
        else:
            print(f"Created {xmp_file.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert WD14 tag .txt files to XMP sidecars"
    )
    parser.add_argument("directory", help="Directory containing .txt tag files")
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing XMP files"
    )
    args = parser.parse_args()

    convert_to_xmp(args.directory, overwrite=args.overwrite)
