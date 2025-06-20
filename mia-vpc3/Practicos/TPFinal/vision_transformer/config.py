import os
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
from loguru import logger

from vision_transformer.utils import DatasetFormat

# Load environment variables from .env file if it exists
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

# Paths
PROJ_ROOT = Path(__file__).resolve().parents[1]
logger.info(f"PROJ_ROOT path is: {PROJ_ROOT}")

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
logger.info(f"Actual environment is: {ENVIRONMENT}")
RANDOM_SEED = 42

# Folders
DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

MODELS_DIR = PROJ_ROOT / "models"

# Modelos
MODEL_NAME_SWINV2_TINY = "swinv2-tiny"
MODEL_NAME_SWINV2_BASE = "swinv2-base"
MODEL_NAME_SWINV2_LARGE = "swinv2-large"
MODEL_NAME_CVT_13 = "cvt-13"
MODEL_NAME_CVT_21 = "cvt-21"
MODEL_NAME_VIT_BASE = "vit-base-patch16-224"
MODEL_NAME_YOLOV11_M = "yolo11m-cls"

MODELS_DIR_SIWNV2_TINY = MODELS_DIR / "swinv2-tiny"
MODELS_DIR_SIWNV2_BASE = MODELS_DIR / "swinv2-base"
MODELS_DIR_SIWNV2_LARGE = MODELS_DIR / "swinv2-large"
MODELS_DIR_CVT_13 = MODELS_DIR / "cvt-13"
MODELS_DIR_CVT_21 = MODELS_DIR / "cvt-21"
MODELS_DIR_VIT_BASE = MODELS_DIR / "vit-base-patch16-224"
MODEL_DIR_YOLOV11_M = MODELS_DIR / "yolo11m-cls"

REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

RAW_DATA_EXTRACTION_DIR = RAW_DATA_DIR / "EuroSAT_RGB"

# URLs
DATA_RAW_URL = "https://zenodo.org/records/7711810/files/EuroSAT_RGB.zip?download=1"
MLFLOW_URL = os.getenv("MLFLOW_URL", "http://localhost:8080")
PREFECT_URL = os.getenv("PREFECT_URL", "http://localhost:4200")

# FilesNames
DATA_RAW_FILENAME = "EuroSAT_RGB"
DATA_RAW_FILENAME_ZIP = f"{DATA_RAW_FILENAME}.zip"
METRICS_FILENAME = "metrics.csv"
HISTORY_FILENAME = "history.csv"
PREDICTIONS_FILENAME = "predictions.csv"

# Datasets formats
DATASET_CONFIG = {
    DatasetFormat.YOLO: {
        "extension": ".txt",
        "interim_folderpath": INTERIM_DATA_DIR / f"{DATA_RAW_FILENAME}_yolo",
        "processed_folderpath": PROCESSED_DATA_DIR / f"{DATA_RAW_FILENAME}_yolo",
        "structure": "annotations",
        "classes_file": "classes.names",
    },
    DatasetFormat.HUGGINGFACE: {
        "extension": ".json",
        "interim_folderpath": INTERIM_DATA_DIR / f"{DATA_RAW_FILENAME}_huggingface",
        "processed_folderpath": PROCESSED_DATA_DIR / f"{DATA_RAW_FILENAME}_huggingface",
        "structure": "datasets",
    },
}

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}

# Dataset info
DATASET_VERSION = "v1.0"
DATASET_NAME = "EuroSAT_RGB"

# Error handling
if not DATA_RAW_URL:
    raise ValueError("DATA_RAW_URL must be defined in the environment variables.")

# If tqdm is installed, configure loguru with tqdm.write
# https://github.com/Delgan/loguru/issues/135
try:
    from tqdm import tqdm

    logger.remove(0)
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
except ModuleNotFoundError:
    pass
