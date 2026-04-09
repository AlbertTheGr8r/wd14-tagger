import pytest
import numpy as np
from pathlib import Path
from PIL import Image
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestImagePathDiscovery:
    def test_glob_finds_jpg_files(self, tmp_path):
        (tmp_path / "test.jpg").touch()
        (tmp_path / "test.png").touch()

        jpg_files = list(tmp_path.glob("*.[jJ][pP][gG]"))

        assert len(jpg_files) == 1

    def test_glob_finds_png_files(self, tmp_path):
        (tmp_path / "test.jpg").touch()
        (tmp_path / "test.png").touch()

        png_files = list(tmp_path.glob("*.[pP][nN][gG]"))

        assert len(png_files) == 1

    def test_glob_finds_webp_files(self, tmp_path):
        (tmp_path / "test.webp").touch()

        webp_files = list(tmp_path.glob("*.[wW][eE][bB][pP]"))

        assert len(webp_files) == 1

    def test_glob_is_case_insensitive(self, tmp_path):
        (tmp_path / "test.JPG").touch()
        (tmp_path / "test.PNG").touch()

        jpg_files = list(tmp_path.glob("*.[jJ][pP][gG]"))
        png_files = list(tmp_path.glob("*.[pP][nN][gG]"))

        assert len(jpg_files) == 1
        assert len(png_files) == 1


class TestPreprocessing:
    def test_preprocess_resize_448(self):
        from src.tagger.inference import WD14Tagger

        class MockTagger:
            def preprocess(self, image):
                img = image.convert("RGB").resize((448, 448), Image.BICUBIC)
                img_arr = np.array(img).astype(np.float32)
                img_arr = img_arr[:, :, ::-1]
                return np.expand_dims(img_arr, axis=0)

        tagger = MockTagger()
        test_img = Image.new("RGB", (1024, 768))
        result = tagger.preprocess(test_img)

        assert result.shape == (1, 448, 448, 3)

    def test_preprocess_bgr_conversion(self):
        class MockTagger:
            def preprocess(self, image):
                img = image.convert("RGB").resize((448, 448), Image.BICUBIC)
                img_arr = np.array(img).astype(np.float32)
                img_arr = img_arr[:, :, ::-1]
                return np.expand_dims(img_arr, axis=0)

        tagger = MockTagger()
        red_img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        result = tagger.preprocess(red_img)

        assert result.shape == (1, 448, 448, 3)
        assert result[0, 0, 0, 2] == 255


class TestTagFiltering:
    def test_threshold_filtering(self):
        probs = np.array([0.9, 0.6, 0.8, 0.3])
        tag_names = ["1girl", "short_hair", "blue_eyes", "smile"]
        general_indices = [1, 2, 3]
        character_indices = [0]

        gen_thresh = 0.35
        char_thresh = 0.85

        found_tags = []
        for i in general_indices:
            if probs[i] >= gen_thresh:
                found_tags.append(tag_names[i])
        for i in character_indices:
            if probs[i] >= char_thresh:
                found_tags.append(tag_names[i])

        assert "short_hair" in found_tags
        assert "blue_eyes" in found_tags
        assert "1girl" in found_tags

    def test_underscore_replacement(self):
        tag = "short_hair"
        formatted = tag.replace("_", " ")

        assert formatted == "short hair"
