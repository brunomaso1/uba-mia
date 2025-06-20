import pytest
import os
from pathlib import Path
from unittest.mock import patch

# Mocking DatasetFormat
from enum import Enum
class MockDatasetFormat(Enum):
    YOLO = "yolo"
    HUGGINGFACE = "huggingface"

@pytest.fixture(autouse=True)
def setup_mock_dataset_format():
    """
    Patch DatasetFormat para que se utilice MockDatasetFormat en lugar de la clase real.
    Esto permite que las pruebas funcionen sin depender de la implementación real de DatasetFormat.
    """
    with patch('vision_transformer.config.DatasetFormat', new=MockDatasetFormat):
        yield # Permite que continúe con las pruebas usando el mock

def reload_config_module(monkeypatch_fixture):
    """
    Esta función permite recargar el módulo de configuración después de aplicar el parche (monkeypatch).
    Esto se tiene que hacer porque config.py lee las variables de entorno en el momento de la importación.
    """
    # Se remueve el módulo de configuración de sys.modules para forzar su recarga
    if 'vision_transformer.config' in os.sys.modules:
        del os.sys.modules['vision_transformer.config']
    
    with patch('dotenv.find_dotenv', return_value='.env_test'), \
         patch('dotenv.load_dotenv'):
        import vision_transformer.config as reloaded_config
        return reloaded_config

# --- Definición de tests ---
def test_proj_root_is_path_and_correct():
    """Verifica que PROJ_ROOT sea un objeto Path y apunte al directorio correcto."""
    import vision_transformer.config as cfg # Para casos donde no se carga de .env, se puede importar directamente
    assert isinstance(cfg.PROJ_ROOT, Path)
    assert cfg.PROJ_ROOT.name == 'vision-transformer'


def test_data_and_model_dirs_are_paths_and_relative_to_proj_root():
    """Verifica que los directorios de datos y modelos sean objetos Path y estén correctamente relacionados con PROJ_ROOT."""
    import vision_transformer.config as cfg
    assert isinstance(cfg.DATA_DIR, Path)
    assert cfg.DATA_DIR == cfg.PROJ_ROOT / "data"
    assert isinstance(cfg.MODELS_DIR, Path)
    assert cfg.MODELS_DIR == cfg.PROJ_ROOT / "models"
    assert isinstance(cfg.REPORTS_DIR, Path)
    assert cfg.REPORTS_DIR == cfg.PROJ_ROOT / "reports"

def test_sub_data_dirs_are_paths_and_relative_to_data_dir():
    """Verifica que los subdirectorios de datos sean objetos Path y estén correctamente relacionados con DATA_DIR."""
    import vision_transformer.config as cfg
    assert isinstance(cfg.RAW_DATA_DIR, Path)
    assert cfg.RAW_DATA_DIR == cfg.DATA_DIR / "raw"
    assert isinstance(cfg.INTERIM_DATA_DIR, Path)
    assert cfg.INTERIM_DATA_DIR == cfg.DATA_DIR / "interim"
    assert isinstance(cfg.PROCESSED_DATA_DIR, Path)
    assert cfg.PROCESSED_DATA_DIR == cfg.DATA_DIR / "processed"
    assert isinstance(cfg.EXTERNAL_DATA_DIR, Path)
    assert cfg.EXTERNAL_DATA_DIR == cfg.DATA_DIR / "external"
    assert isinstance(cfg.RAW_DATA_EXTRACTION_DIR, Path)
    assert cfg.RAW_DATA_EXTRACTION_DIR == cfg.RAW_DATA_DIR / "EuroSAT_RGB"

def test_model_dirs_are_paths_and_relative_to_models_dir():
    """Verifica que los directorios específicos de modelos sean objetos Path y estén correctamente relacionados con MODELS_DIR."""
    import vision_transformer.config as cfg
    assert isinstance(cfg.MODELS_DIR_SIWNV2_TINY, Path)
    assert cfg.MODELS_DIR_SIWNV2_TINY == cfg.MODELS_DIR / "swinv2-tiny"
    assert isinstance(cfg.MODELS_DIR_CVT_13, Path)
    assert cfg.MODELS_DIR_CVT_13 == cfg.MODELS_DIR / "cvt-13"
    assert cfg.MODEL_DIR_YOLOV11_M == cfg.MODELS_DIR / "yolo11m-cls"

def test_urls_constants():
    """Verfica que las URLs sean cadenas de texto y contengan los valores esperados."""
    import vision_transformer.config as cfg
    assert cfg.DATA_RAW_URL == "https://zenodo.org/records/7711810/files/EuroSAT_RGB.zip?download=1"

def test_image_extensions():
    """Verifica que IMAGE_EXTENSIONS sea un conjunto y contenga las extensiones de imagen esperadas."""
    import vision_transformer.config as cfg
    assert isinstance(cfg.IMAGE_EXTENSIONS, set)
    assert '.jpg' in cfg.IMAGE_EXTENSIONS
    assert '.png' in cfg.IMAGE_EXTENSIONS
    assert '.tiff' in cfg.IMAGE_EXTENSIONS
    assert len(cfg.IMAGE_EXTENSIONS) == 6