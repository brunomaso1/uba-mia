from prefect import flow, task

from loguru import logger

from vision_transformer.dataset import (
    convert_dataset_to_model_format,
    download_raw_data,
    extract_raw_data,
    split_dataset,
)
from vision_transformer.utils import DatasetFormat


@task
def download_raw_data_task() -> None:
    logger.info(f"Ejecutando tarea download_raw_data_task...")
    download_raw_data()
    logger.info(f"Tarea download_raw_data_task completada.")


@task
def extract_raw_data_task() -> None:
    logger.info(f"Ejecutando tarea extract_raw_data_task...")
    extract_raw_data()
    logger.info(f"Tarea extract_raw_data_task completada.")


@task
def convert_dataset_to_model_format_task(format: DatasetFormat) -> None:
    logger.info(f"Ejecutando tarea convert_dataset_to_model_format...")
    convert_dataset_to_model_format(format)
    logger.info(f"Tarea convert_dataset_to_model_format completada.")


@task
def split_dataset_task(format: DatasetFormat) -> None:
    logger.info(f"Ejecutando tarea split_dataset_task...")
    split_dataset(format)
    logger.info(f"Tarea split_dataset_task completada.")


@flow
def execute_flow(format: DatasetFormat) -> None:
    download_raw_data_task()
    extract_raw_data_task()
    convert_dataset_to_model_format_task(format)
    split_dataset_task(format)
