# Enum para los formatos de dataset
from enum import Enum

import datasets
import evaluate
from evaluate import Metric
from sklearn.metrics import accuracy_score


class DatasetFormat(str, Enum):
    """
    Enum para representar los formatos de dataset soportados.
    Atributos:
        YOLO: Representa el formato de dataset YOLO.
        HUGGINGFACE: Representa el formato de dataset HuggingFace.
    Métodos:
        __str__(): Retorna el valor del formato como string.
        list_formats(): Retorna una lista de todos los formatos disponibles.
        from_string(format_str: str): Crea una instancia del enum a partir de un string (case-insensitive).
    Ejemplo de uso:
        >>> formato = DatasetFormat.from_string("yolo")
        >>> print(formato)  # Salida: yolo
    """

    YOLO = "yolo"
    HUGGINGFACE = "huggingface"

    def __str__(self):
        return self.value

    @classmethod
    def list_formats(cls):
        """Retorna una lista de todos los formatos disponibles"""
        return [fmt.value for fmt in cls]

    @classmethod
    def from_string(cls, format_str: str):
        """Crea un enum desde un string, case-insensitive"""
        format_str = format_str.lower()
        for fmt in cls:
            if fmt.value.lower() == format_str:
                return fmt
        raise ValueError(f"Formato '{format_str}' no válido. Formatos disponibles: {cls.list_formats()}")


class MulticlassAccuracy(Metric):
    """Workaround for the default Accuracy class which doesn't support passing 'average' to the compute method.

    Reference: https://stackoverflow.com/questions/76441777/huggingface-evaluate-function-use-multiple-labels
    """

    def _info(self):
        return evaluate.MetricInfo(
            description="Accuracy",
            citation="",
            inputs_description="",
            features=datasets.Features(
                {
                    "predictions": datasets.Sequence(datasets.Value("int32")),
                    "references": datasets.Sequence(datasets.Value("int32")),
                }
                if self.config_name == "multilabel"
                else {
                    "predictions": datasets.Value("int32"),
                    "references": datasets.Value("int32"),
                }
            ),
            reference_urls=["https://scikit-learn.org/stable/modules/generated/sklearn.metrics.accuracy_score.html"],
        )

    def _compute(self, predictions, references, normalize=True, sample_weight=None, **kwargs):
        # take **kwargs to avoid breaking when the metric is used with a compute method that takes additional arguments
        return {
            "accuracy": float(accuracy_score(references, predictions, normalize=normalize, sample_weight=sample_weight))
        }
