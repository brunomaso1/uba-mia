import pytest

# Importar las funciones a testear
from vision_transformer.dataset import (
    _validate_eurosat_structure,
    _validate_huggingface_structure,
    _validate_huggingface_interim_structure,
    _convert_to_huggingface,
    split_dataset,
)

@pytest.fixture
def tmp_eurosat_structure(tmp_path):
    """Crea una estructura de directorios válida para EuroSAT."""
    class_dir = tmp_path / "AnnualCrop"
    class_dir.mkdir()
    (class_dir / "AnnualCrop_1.jpg").touch()
    return tmp_path

def test_validate_eurosat_structure_valid(tmp_eurosat_structure):
    """Testea la validación de la estructura de EuroSAT."""
    assert _validate_eurosat_structure(tmp_eurosat_structure) is True

def test_validate_eurosat_structure_invalid(tmp_path):
    """Testea la validación de una estructura de EuroSAT inválida."""
    assert _validate_eurosat_structure(tmp_path) is False

@pytest.fixture
def tmp_huggingface_structure(tmp_path):
    """Crea una estructura de directorios válida para HuggingFace."""
    train_dir = tmp_path / "train"
    class_dir = train_dir / "Forest"
    class_dir.mkdir(parents=True)
    (class_dir / "Forest_1.jpg").touch()
    return tmp_path

def test_validate_huggingface_structure_valid(tmp_huggingface_structure):
    """Testea la validación de la estructura de HuggingFace."""
    valid, only_train = _validate_huggingface_structure(tmp_huggingface_structure)
    assert valid is True
    assert only_train is True

def test_validate_huggingface_structure_invalid(tmp_path):
    """Testea la validación de una estructura de HuggingFace inválida."""
    valid, only_train = _validate_huggingface_structure(tmp_path)
    assert valid is False

def test_validate_huggingface_interim_structure_valid(tmp_huggingface_structure):
    """Testea la validación de la estructura intermedia de HuggingFace."""
    assert _validate_huggingface_interim_structure(tmp_huggingface_structure) is True

def test_validate_huggingface_interim_structure_invalid(tmp_path):
    """Testea la validación de una estructura intermedia de HuggingFace inválida."""
    assert _validate_huggingface_interim_structure(tmp_path) is False

def test_convert_to_huggingface(tmp_eurosat_structure, tmp_path):
    """Testea la conversión de EuroSAT a la estructura de HuggingFace."""
    output_path = tmp_path / "output"
    _convert_to_huggingface(tmp_eurosat_structure, output_path, summary=False)
    assert (output_path / "train" / "AnnualCrop" / "AnnualCrop_1.jpg").exists()

def test_split_dataset(tmp_huggingface_structure, tmp_path):
    """Testea la división del dataset en conjuntos de entrenamiento, validación y prueba."""
    output_dir = tmp_path / "processed"
    # Llama a la función principal split_dataset (usando los argumentos por defecto)
    split_dataset(
        dataset_path=tmp_huggingface_structure,
        output_dir=output_dir,
        split=(1.0, 0.0, 0.0),
        summary=False,
        clean=False
    )
    assert (output_dir / "train" / "Forest" / "Forest_1.jpg").exists()
