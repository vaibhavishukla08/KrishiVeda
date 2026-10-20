"""CNN architecture and preprocessing shared by training (ml/training) and inference (backend).

Keeping both in one place guarantees the image is prepared exactly the same way at
training time and at prediction time.
"""

import numpy as np
from PIL import Image, ImageOps

ARCH = "mobilenet_v3_large"
IMAGE_SIZE = 224  # CNN input size (pixels)
RESIZE = 256  # shorter side is resized to this before the centre crop
MEAN = (0.485, 0.456, 0.406)  # ImageNet statistics (the backbone was pre-trained on ImageNet)
STD = (0.229, 0.224, 0.225)


def build_model(num_classes: int, pretrained: bool = False):
    """MobileNetV3-Large CNN with a new classification head for our disease classes.

    Feature extraction happens inside the convolutional layers of this same network;
    the final linear layer maps those features to disease classes.
    """
    import torch.nn as nn
    from torchvision.models import MobileNet_V3_Large_Weights, mobilenet_v3_large

    weights = MobileNet_V3_Large_Weights.IMAGENET1K_V2 if pretrained else None
    model = mobilenet_v3_large(weights=weights)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, num_classes)
    return model


def preprocess(image: Image.Image, resize: int = RESIZE, size: int = IMAGE_SIZE,
               mean=MEAN, std=STD) -> np.ndarray:
    """PIL image -> float32 array of shape (1, 3, size, size), normalised for the CNN."""
    image = ImageOps.exif_transpose(image).convert("RGB")  # respect phone camera rotation
    w, h = image.size
    scale = resize / min(w, h)
    image = image.resize((max(size, round(w * scale)), max(size, round(h * scale))), Image.BILINEAR)
    w, h = image.size
    left, top = (w - size) // 2, (h - size) // 2
    image = image.crop((left, top, left + size, top + size))
    arr = np.asarray(image, dtype=np.float32) / 255.0
    arr = (arr - np.array(mean, dtype=np.float32)) / np.array(std, dtype=np.float32)
    return arr.transpose(2, 0, 1)[np.newaxis, ...]
