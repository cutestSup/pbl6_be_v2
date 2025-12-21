import cv2
import torch
import numpy as np

class SimpleTextPreprocessor:

    def __init__(self):
        pass

    def preprocess(self, img_bgr, short_size=736, img_name=None):
        h, w = img_bgr.shape[:2]
        scale = short_size / min(h, w)
        new_h = int(h * scale)
        new_w = int(w * scale)

        new_h = (new_h + 31) // 32 * 32
        new_w = (new_w + 31) // 32 * 32

        img_resized = cv2.resize(img_bgr, (new_w, new_h))

        gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)

        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        binary = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=15,
            C=10
        )

        binary_bgr = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

        img_tensor = (
            torch.from_numpy(binary_bgr)
            .permute(2, 0, 1)
            .unsqueeze(0)
            .float() / 255.0
        )

        return img_tensor, binary_bgr, (new_h, new_w)
