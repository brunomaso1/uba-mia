"""
Dynamic Path Configuration System for UI-to-Code Multi-Agent System
Based on pyprojroot and YAML configuration for flexible project structure management
"""

import json
from dotenv import load_dotenv
from loguru import logger
import yaml
from pyprojroot import here
from pathlib import Path
from typing import Union, Callable, Iterable, Any
import os

ROOT_DIR: Path = here()
env_file_path = ROOT_DIR / ".env"
env_file = str(env_file_path)

if env_file_path.exists():
    load_dotenv(env_file)  # Load environment variables from .env file
    logger.warning(f"Using .env file at {env_file_path.resolve()} for configuration.")


def load_config(config_path: str = "config.yaml") -> dict[str, Any]:
    """
    Load configuration from config.yaml

    Args:
        config_path: Relative path to config file from this module

    Returns:
        Dictionary containing configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    try:
        abs_config_path = os.path.join(os.path.dirname(__file__), config_path)
        with open(abs_config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {abs_config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML configuration: {e}")


def make_dir_function(dir_name: Union[str, Iterable[str]]) -> Callable[..., Path]:
    """
    Create a directory function using pyprojroot

    Args:
        dir_name: Directory name or path components

    Returns:
        Function that returns Path object relative to project root
    """

    def dir_path(*args) -> Path:
        if isinstance(dir_name, str):
            return here().joinpath(dir_name, *args)
        else:
            return here().joinpath(*dir_name, *args)

    return dir_path


def ensure_dir_exists(dir_function: Callable[..., Path]) -> Path:
    """
    Create directory if it doesn't exist and return the Path

    Args:
        dir_function: Function that returns a Path

    Returns:
        Path object of the created/existing directory
    """
    path = dir_function()
    path.mkdir(parents=True, exist_ok=True)
    return path


logger.info("Loading configuration from config.yaml")

# Load configuration
config = load_config()

# Project root and main directories
project_dir = make_dir_function("")
app_dir = make_dir_function("app")
src_dir = make_dir_function("src")

# Data directories (only existing ones)
corpus_dir = make_dir_function(config["data"]["corpus_dir"])

# RAG directories (existing source code structure)
rag_ingestion_dir = make_dir_function(config["rag"]["ingestion_dir"])
rag_retrievers_dir = make_dir_function(config["rag"]["retrievers_dir"])
rag_evaluators_dir = make_dir_function(config["rag"]["evaluators_dir"])
rag_core_dir = make_dir_function(config["rag"]["core_dir"])
rag_ce_model = config["rag"]["ce_model"]

# Application paths
app_main_file = make_dir_function(config["app"]["main_file"])
streamlit_port = config["app"].get("streamlit_port", 8501)

# Source code structure (only existing)
agents_dir = make_dir_function(config["src"]["agents_dir"])
runtime_dir = make_dir_function(config["src"]["runtime_dir"])

# Development directories (only existing ones)
docs_dir = make_dir_function(config["development"]["docs_dir"])

# UI-to-Code directories
ui_examples_dir = make_dir_function(config["ui_to_code"]["ui_examples_dir"])
temp_images_dir = make_dir_function(config["ui_to_code"]["temp_images_dir"])
generated_code_dir = make_dir_function(config["ui_to_code"]["generated_code_dir"])
websight_data_dir = make_dir_function(config["ui_to_code"]["websight_data_dir"])
websight_data_file_name = config["ui_to_code"]["websight_data_file_name"]

# Configuration files
requirements_file = make_dir_function(config["files"]["requirements_file"])
requirements_dev_file = make_dir_function(config["files"]["requirements_dev_file"])
setup_file = make_dir_function(config["files"]["setup_file"])
pyproject_file = make_dir_function(config["files"]["pyproject_file"])
config_file = make_dir_function(config["files"]["config_file"])
env_file = make_dir_function(config["files"]["env_file"])
env_example_file = make_dir_function(config["files"]["env_example_file"])
makefile = make_dir_function(config["files"]["makefile"])
readme_file = make_dir_function(config["files"]["readme_file"])
gitignore_file = make_dir_function(config["files"]["gitignore_file"])
check_deps_file = make_dir_function(config["files"]["check_deps_file"])
quick_start_file = make_dir_function(config["files"]["quick_start_file"])
run_streamlit_file = make_dir_function(config["files"]["run_streamlit_file"])

# Agent service URLs
visual_agent_url = config["agents_endpoints"]["visual_agent_url"]
code_agent_url = config["agents_endpoints"]["code_agent_url"]

# Pinecone configuration
pinecone_index = config["pinecone"]["index"]
pinecone_model_name = config["pinecone"]["model_name"]
pinecone_cloud = config["pinecone"]["cloud"]
pinecone_region = config["pinecone"]["region"]
pinecone_namespace = config["pinecone"]["namespace"]
pinecone_rag_namespace = config["pinecone"]["rag_namespace"]
pinecone_metric = config["pinecone"]["metric"]

# Sentence Transformers configuration
st_model_name = config["sentence_transformers"]["model_name"]

# Server timeout settings
server_timeout_keep_alive = config["server_timeout_keep_alive"]
server_connect_timeout = config["server_connect_timeout"]

# WebSight dataset configuration
websight_max_examples = config["websight_dataset"]["max_examples"]
websight_download_steps = config["websight_dataset"]["download_steps"]
websight_download_offset = config["websight_dataset"]["download_offset"]
websight_download_length = config["websight_dataset"]["download_length"]

# Env variables
try:
    pinecone_api_key = os.environ.get("PINECONE_API_KEY", "")
    print("✅ PINECONE_API_KEY loaded from environment variables.")
    host = os.environ.get("HOST", "")
    print(f"✅ HOST set to '{host}'")
except KeyError:
    raise ValueError("PINECONE_API_KEY not set in environment variables.")

# Post-load
if host == "localhost":
    config["agents_endpoints"]["visual_agent_url"] = "http://localhost:10000"
    config["agents_endpoints"]["code_agent_url"] = "http://localhost:10001"
    visual_agent_url = "http://localhost:10000"
    code_agent_url = "http://localhost:10001"

logger.info("Configuration loaded successfully")
logger.debug(f"Configuration: {json.dumps(config, indent=2)}")


def get_path(key: str, *args) -> Path:
    """
    Get a path by configuration key

    Args:
        key: Configuration key in dot notation (e.g., 'data.corpus_dir')
        *args: Additional path components

    Returns:
        Path object

    Example:
        >>> get_path('ui_to_code.temp_images_dir', 'image.png')
        Path('/path/to/project/data/temp_images/image.png')
    """
    keys = key.split(".")
    value = config
    for k in keys:
        if k in value:
            value = value[k]
        else:
            raise KeyError(f"Configuration key not found: {key}")

    return here().joinpath(value, *args)


def create_all_directories() -> None:
    """Create all directories needed for the UI-to-Code system"""
    directories_to_create = [
        # Core directories
        corpus_dir,
        docs_dir,
        # UI-to-Code data directories
        ui_examples_dir,
        temp_images_dir,
        generated_code_dir,
        websight_data_dir,
    ]

    for dir_func in directories_to_create:
        ensure_dir_exists(dir_func)

    print("✅ All directories created successfully")
