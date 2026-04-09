import sys
from pathlib import Path
from src.tagger.inference import WD14Tagger
from tqdm import tqdm


def run_tagging(
    target_dir: str,
    batch_size: int = 6,
    general_threshold: float = 0.35,
    character_threshold: float = 0.85,
    model_repo: str = "SmilingWolf/wd-swinv2-tagger-v3",
    recursive: bool = False,
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
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(tags)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h", "help"):
        print("Usage: uv run main.py <folder_path> [options]")
        print("")
        print("Options:")
        print("  --batch-size N        Batch size (default: 6)")
        print("  --gen-thresh N        General threshold (default: 0.35)")
        print("  --char-thresh N       Character threshold (default: 0.85)")
        print(
            "  --model MODEL         Model repo (default: SmilingWolf/wd-swinv2-tagger-v3)"
        )
        print("  --recursive           Process subdirectories")
        sys.exit(0)

    target_dir = sys.argv[1]

    batch_size = 6
    general_threshold = 0.35
    character_threshold = 0.85
    model_repo = "SmilingWolf/wd-swinv2-tagger-v3"
    recursive = False

    args = sys.argv[2:]
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
        else:
            i += 1

    run_tagging(
        target_dir,
        batch_size=batch_size,
        general_threshold=general_threshold,
        character_threshold=character_threshold,
        model_repo=model_repo,
        recursive=recursive,
    )
