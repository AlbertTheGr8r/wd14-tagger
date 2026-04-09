import numpy as np
import onnxruntime as ort
from PIL import Image
from huggingface_hub import hf_hub_download
import pandas as pd
from pathlib import Path
import logging
import os
from datetime import datetime


def setup_logging():
    today = datetime.now().strftime("%Y-%m-%d")
    log_dir = Path(".")
    log_pattern = "wd14-tagger-{date}.log"

    for i in range(2, 0, -1):
        old = log_dir / log_pattern.format(date=f"*{i}.log")
        for f in log_dir.glob(f"wd14-tagger-*.log.{i}"):
            f.unlink()
        prev = log_dir / log_pattern.format(date=f"*-{i}.log")
        if prev.exists():
            prev.rename(log_dir / f"wd14-tagger-{today}.log.{i}")

    current_log = log_dir / log_pattern.format(date=today)
    if current_log.exists():
        current_log.rename(log_dir / f"wd14-tagger-{today}.log.1")

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(current_log),
            logging.NullHandler(),
        ],
    )


class WD14Tagger:
    def __init__(
        self,
        model_repo: str = "SmilingWolf/wd-swinv2-tagger-v3",
        device: str = "cuda",
        general_threshold: float = 0.35,
        character_threshold: float = 0.85,
    ):
        self.model_repo = model_repo
        self.device = device
        self.general_threshold = general_threshold
        self.character_threshold = character_threshold
        self.skipped_count = 0

        setup_logging()

        model_path = hf_hub_download(model_repo, "model.onnx")
        label_path = hf_hub_download(model_repo, "selected_tags.csv")

        self.tags_df = pd.read_csv(label_path)
        self.tag_names = self.tags_df["name"].tolist()
        self.character_indices = self.tags_df.index[
            self.tags_df["category"] == 4
        ].tolist()
        self.general_indices = self.tags_df.index[
            self.tags_df["category"] == 0
        ].tolist()

        providers = (
            ["CUDAExecutionProvider", "CPUExecutionProvider"]
            if device == "cuda"
            else ["CPUExecutionProvider"]
        )
        self.session = ort.InferenceSession(model_path, providers=providers)
        self.input_name = self.session.get_inputs()[0].name

    def preprocess(self, image: Image.Image) -> np.ndarray:
        img = image.convert("RGB").resize((448, 448), Image.BICUBIC)
        img_arr = np.array(img).astype(np.float32)
        img_arr = img_arr[:, :, ::-1]
        return np.expand_dims(img_arr, axis=0)

    def predict(
        self,
        image_paths: list[Path],
        general_threshold: float = None,
        character_threshold: float = None,
    ):
        gen_thresh = (
            general_threshold
            if general_threshold is not None
            else self.general_threshold
        )
        char_thresh = (
            character_threshold
            if character_threshold is not None
            else self.character_threshold
        )

        results = {}
        self.skipped_count = 0

        for path in image_paths:
            try:
                img = Image.open(path)
                img.load()
                input_data = self.preprocess(img)
                probs = self.session.run(None, {self.input_name: input_data})[0][0]

                found_tags = []
                for i in self.general_indices:
                    if probs[i] >= gen_thresh:
                        found_tags.append(self.tag_names[i])
                for i in self.character_indices:
                    if probs[i] >= char_thresh:
                        found_tags.append(self.tag_names[i])

                results[path] = ", ".join(found_tags).replace("_", " ")
            except Exception as e:
                logging.warning(f"Skipped {path.name}: {e}")
                results[path] = ""
                self.skipped_count += 1

        return results
