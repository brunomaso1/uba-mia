from pathlib import Path

from loguru import logger
from pyparsing import Union
import torch
from tqdm import tqdm
import typer

from PIL import Image

from transformers import ViTImageProcessor, ViTImageProcessorFast

# Transformaciones de imágenes (Torchvision)
from torchvision.transforms import (
    Compose,
    Normalize,
    ToTensor,
    RandomResizedCrop,
    RandomHorizontalFlip,
    Resize,
    CenterCrop,
    RandomApply,
    RandomRotation,
    RandomCrop,
    ColorJitter,
)

from vision_transformer.config import PROCESSED_DATA_DIR


app = typer.Typer()


class SwinV2Transforms:
    """Clase para aplicar transformaciones a las imágenes usando la configuración de un `ViTImageProcessor`.

    Args:
        image_processor (Union[ViTImageProcessor, ViTImageProcessorFast]): Procesador de imágenes ViT para obtener la configuración de las transformaciones.
    """

    def __init__(self, image_processor: Union[ViTImageProcessor, ViTImageProcessorFast]) -> None:
        self.image_processor = image_processor
        self.mean = image_processor.image_mean
        self.std = image_processor.image_std

        if "height" in image_processor.size:
            self.size = (image_processor.size["height"], image_processor.size["width"])
            self.crop_size = self.size
            self.max_size = None
        elif "shortest_edge" in image_processor.size:
            self.size = image_processor.size["shortest_edge"]
            self.crop_size = (self.size, self.size)
            self.max_size = image_processor.size.get("longest_edge")

        self.train_transforms = Compose(
            [
                RandomResizedCrop(self.crop_size),
                RandomHorizontalFlip(),
                ToTensor(),
                Normalize(mean=self.mean, std=self.std),
            ]
        )

        self.val_transforms = Compose(
            [
                Resize(self.size),
                CenterCrop(self.crop_size),
                ToTensor(),
                Normalize(mean=self.mean, std=self.std),
            ]
        )

        self._unnormalize = Normalize(
            mean=[-m / s for m, s in zip(self.mean, self.std)],
            std=[1 / s for s in self.std],
        )

    def __call__(self, batch, train=True):
        return self.transforms(batch, train)

    def transforms(self, batch, train=True):
        batch["pixel_values"] = (
            [self.train_transforms(img) for img in batch["image"]]
            if train
            else [self.val_transforms(img) for img in batch["image"]]
        )
        del batch["image"]

        return batch

    def unnormalize(self, img: torch.Tensor) -> torch.Tensor:
        return self._unnormalize(img)

    def transforms_to_string(self) -> str:
        def format_compose(compose):
            return "\n  - " + "\n  - ".join(str(t) for t in compose.transforms)

        return (
            f"Transformaciones de entrenamiento:{format_compose(self.train_transforms)}\n\n"
            f"Transformaciones de validacion:{format_compose(self.val_transforms)}"
        )

    def transforms_to_dict(self) -> dict:
        """Devuelve un diccionario con las transformaciones de entrenamiento y validación."""
        return {
            "train_transforms": [str(t) for t in self.train_transforms],
            "val_transforms": [str(t) for t in self.val_transforms],
        }


class CVTTransforms:
    """Clase para aplicar transformaciones a las imágenes usando la configuración de un `ViTImageProcessor`.

    Args:
        image_processor (Union[ViTImageProcessor, ViTImageProcessorFast]): Procesador de imágenes ViT para obtener la configuración de las transformaciones.
    """

    def __init__(self, image_processor: Union[ViTImageProcessor, ViTImageProcessorFast]) -> None:
        self.image_processor = image_processor
        self.mean = image_processor.image_mean
        self.std = image_processor.image_std
        self.size = image_processor.size["shortest_edge"]  # 224

        self.train_transforms = Compose(
            [
                RandomApply([RandomRotation(15)], p=0.8),
                RandomApply(
                    [
                        Resize((72, 72), interpolation=Image.BICUBIC),
                        RandomCrop(64, padding=0),
                    ],
                    p=0.8,
                ),
                RandomHorizontalFlip(),
                RandomApply([ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1)], p=0.8),
                Resize((224, 224), interpolation=Image.BICUBIC),  # required for CvT
                ToTensor(),
                Normalize(mean=self.mean, std=self.std),
            ]
        )

        self.val_transforms = Compose(
            [
                Resize((self.size, self.size), interpolation=Image.BICUBIC),
                ToTensor(),
                Normalize(mean=self.mean, std=self.std),
            ]
        )

        self._unnormalize = Normalize(
            mean=[-m / s for m, s in zip(self.mean, self.std)],
            std=[1 / s for s in self.std],
        )

    def __call__(self, batch, train=True):
        return self.transforms(batch, train)

    def transforms(self, batch, train=True):
        images = (
            [self.train_transforms(img) for img in batch["image"]]
            if train
            else [self.val_transforms(img) for img in batch["image"]]
        )

        return {"pixel_values": images, "label": batch["label"]}

    def unnormalize(self, img: torch.Tensor) -> torch.Tensor:
        return self._unnormalize(img)

    def transforms_to_string(self) -> str:
        def format_compose(compose):
            return "\n  - " + "\n  - ".join(str(t) for t in compose.transforms)

        return (
            f"Transformaciones de entrenamiento:{format_compose(self.train_transforms)}\n\n"
            f"Transformaciones de validacion:{format_compose(self.val_transforms)}"
        )

    def transforms_to_dict(self) -> dict:
        """Devuelve un diccionario con las transformaciones de entrenamiento y validación."""
        return {
            "train_transforms": [str(t) for t in self.train_transforms],
            "val_transforms": [str(t) for t in self.val_transforms],
        }


class VitBaseTransforms:
    """Clase para aplicar transformaciones a las imágenes usando la configuración de un `ViTImageProcessor`.

    Args:
        image_processor (Union[ViTImageProcessor, ViTImageProcessorFast]): Procesador de imágenes ViT para obtener la configuración de las transformaciones.
    """

    def __init__(self, image_processor: Union[ViTImageProcessor, ViTImageProcessorFast]) -> None:
        self.image_processor = image_processor
        self.mean = image_processor.image_mean
        self.std = image_processor.image_std
        self.size = 224

        self.train_transforms = Compose(
            [
                RandomApply([RandomRotation(15)], p=0.8),
                RandomApply(
                    [Resize((72, 72), interpolation=Image.BICUBIC), RandomCrop(64, padding=0)],
                    p=0.8,
                ),
                RandomHorizontalFlip(),
                RandomApply(
                    [ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1)], p=0.8
                ),
                Resize((224, 224), interpolation=Image.BICUBIC),
                ToTensor(),
                Normalize(mean=self.mean, std=self.std),
            ]
        )

        self.val_transforms = Compose(
            [
                Resize((self.size, self.size), interpolation=Image.BICUBIC),
                ToTensor(),
                Normalize(mean=self.mean, std=self.std),
            ]
        )

        self._unnormalize = Normalize(
            mean=[-m / s for m, s in zip(self.mean, self.std)],
            std=[1 / s for s in self.std],
        )

    def __call__(self, batch, train=True):
        return self.transforms(batch, train)

    def transforms(self, batch, train=True):
        images = (
            [self.train_transforms(img) for img in batch["image"]]
            if train
            else [self.val_transforms(img) for img in batch["image"]]
        )

        return {"pixel_values": images, "label": batch["label"]}

    def unnormalize(self, img: torch.Tensor) -> torch.Tensor:
        return self._unnormalize(img)

    def transforms_to_string(self) -> str:
        def format_compose(compose):
            return "\n  - " + "\n  - ".join(str(t) for t in compose.transforms)

        return (
            f"Transformaciones de entrenamiento:{format_compose(self.train_transforms)}\n\n"
            f"Transformaciones de validacion:{format_compose(self.val_transforms)}"
        )

    def transforms_to_dict(self) -> dict:
        """Devuelve un diccionario con las transformaciones de entrenamiento y validación."""
        return {
            "train_transforms": [str(t) for t in self.train_transforms],
            "val_transforms": [str(t) for t in self.val_transforms],
        }


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = PROCESSED_DATA_DIR / "dataset.csv",
    output_path: Path = PROCESSED_DATA_DIR / "features.csv",
    # -----------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----
    logger.info("Generating features from dataset...")
    for i in tqdm(range(10), total=10):
        if i == 5:
            logger.info("Something happened for iteration 5.")
    logger.success("Features generation complete.")
    # -----------------------------------------


if __name__ == "__main__":
    app()
