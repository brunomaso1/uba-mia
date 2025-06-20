import zipfile, requests, shutil, os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sklearn.model_selection import train_test_split

from loguru import logger
from tqdm import tqdm
import typer

from datasets import Dataset, load_dataset

from vision_transformer.config import (
    DATA_RAW_FILENAME_ZIP,
    DATA_RAW_URL,
    DATASET_CONFIG,
    IMAGE_EXTENSIONS,
    INTERIM_DATA_DIR,
    PROCESSED_DATA_DIR,
    RANDOM_SEED,
    RAW_DATA_DIR,
    RAW_DATA_EXTRACTION_DIR,
)
from vision_transformer.utils import DatasetFormat

app = typer.Typer()


@app.command()
def download_raw_data(url: str = DATA_RAW_URL, chunk_size: int = 65_536):
    """
    Descarga el archivo de datos en bruto desde la URL especificada y lo guarda en el directorio RAW_DATA_DIR.
    Muestra una barra de progreso durante la descarga.

    Args:
        url (str, optional): URL desde donde descargar el archivo de datos. Por defecto es DATA_RAW_URL.
        chunk_size (int, optional): Tamaño de cada chunk de descarga en bytes. Por defecto es 65_536.

    Raises:
        typer.Exit: Si ocurre un error durante la descarga o al guardar el archivo.

    Ejecución de ejemplo:
        >>> python -m vision_transformer.dataset download_raw_data --help
    """
    logger.info(f"Downloading raw data from {url}...")
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))  # Get total size of the file, if available
        filename = RAW_DATA_DIR / DATA_RAW_FILENAME_ZIP

        if not os.path.exists(RAW_DATA_DIR):
            os.makedirs(RAW_DATA_DIR)

        with open(filename, "wb") as file:
            # Configure tqdm progress bar if total size is known
            if total_size > 0:
                total_chunks = total_size // chunk_size + (1 if total_size % chunk_size else 0)
                logger.debug(f"Total size: {total_size} bytes, Total chunks: {total_chunks}")

                progress_bar = tqdm(total=total_size, unit="B", unit_scale=True, unit_divisor=1024, desc="Downloading")
            else:
                progress_bar = tqdm(unit="KB", desc="Downloading (unknown size)")

            downloaded = 0
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:  # Filtrar chunks vacíos
                    file.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        progress_bar.update(len(chunk))
                    else:
                        progress_bar.update(len(chunk) // 1024)  # Mostrar en KB
            progress_bar.close()

        logger.success(f"Download complete! File size: {downloaded / (1024*1024):.2f} MB")
        logger.info(f"Data saved to: {filename}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading data: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise typer.Exit(code=1)


@app.command()
def extract_raw_data(zip_file_path: Path = RAW_DATA_DIR / DATA_RAW_FILENAME_ZIP, clean: bool = True):
    """
    Extrae el archivo ZIP de datos en bruto y lo guarda en el directorio RAW_DATA_DIR.
    Si clean es True, elimina el archivo ZIP después de la extracción.

    Args:
        zip_file_path (Path, optional): Ruta al archivo ZIP a extraer. Por defecto es RAW_DATA_DIR / DATA_RAW_FILE.
        clean (bool, optional): Si es True, elimina el archivo ZIP después de la extracción. Por defecto es True.

    Raises:
        typer.Exit: Si ocurre un error durante la extracción o al eliminar el archivo ZIP.

    Ejecución de ejemplo:
        >>> python -m vision_transformer.dataset extract_raw_data --help
    """
    logger.info(f"Extracting raw data from {zip_file_path}...")
    try:
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            members = zip_ref.infolist()
            with tqdm(total=len(members), desc="Extracting", unit="file") as pbar:
                for member in members:
                    zip_ref.extract(member, RAW_DATA_DIR)
                    pbar.update(1)
            logger.success(f"Extraction complete! Files extracted to: {RAW_DATA_DIR}")

        if clean:
            zip_file_path.unlink(missing_ok=True)  # Elimina el archivo ZIP si clean es True
            logger.info(f"Removed the ZIP file: {zip_file_path}")
    except zipfile.BadZipFile as e:
        logger.error(f"Error extracting data: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise typer.Exit(code=1)


@app.command()
def convert_dataset_to_model_format(
    format: DatasetFormat = DatasetFormat.HUGGINGFACE,
    dataset_path: Path = RAW_DATA_EXTRACTION_DIR,
    output_dir: Optional[Path] = None,
    summary: bool = True,
    delete_previous_data: bool = True,
    clean: bool = False,
):
    """
    Convierte un dataset al formato requerido por el modelo especificado.

    Args:
        format (DatasetFormat, optional): Formato de salida del dataset. Por defecto es DatasetFormat.HUGGINGFACE.
        dataset_path (Path, optional): Ruta al directorio de entrada con los datos a convertir. Por defecto es RAW_DATA_EXTRACTION_DIR.
        output_dir (Path, optional): Ruta al directorio donde se guardarán los datos convertidos. Por defecto es la ruta configurada para el formato seleccionado.
        summary (bool, optional): Si es True, genera un archivo de resumen del dataset convertido. Por defecto es True.
        delte_previous_data (bool, optional): Si es True, elimina los datos previos en el directorio de salida antes de la conversión. Por defecto es True.
        clean (bool, optional): Si es True, elimina el directorio de entrada después de la conversión. Por defecto es False.

    Raises:
        typer.Exit: Si el directorio de entrada no existe.
        typer.Exit: Si la estructura del dataset no es compatible con el formato seleccionado.
        typer.Exit: Si ocurre un error al eliminar datos previos.
        typer.Exit: Si el formato solicitado no está implementado.
        typer.Exit: Si ocurre un error inesperado durante la conversión o limpieza.
    """

    # Validar que exista el directorio de entrada
    if not dataset_path.exists():
        logger.error(f"El directorio de entrada no existe: {dataset_path}")
        raise typer.Exit(1)

    # Validaciones sobre el formato: directorio de salida y estructura de entrada.
    match format:
        case DatasetFormat.YOLO:
            if not output_dir:
                logger.debug("No se especificó un directorio de salida, se usará el predeterminado para YOLO")
                output_dir = DATASET_CONFIG[DatasetFormat.YOLO]["interim_folderpath"]
        case DatasetFormat.HUGGINGFACE:
            if not output_dir:
                logger.debug("No se especificó un directorio de salida, se usará el predeterminado para HUGGINGFACE")
                output_dir = DATASET_CONFIG[DatasetFormat.HUGGINGFACE]["interim_folderpath"]

            # Validar estructura de entrada para HuggingFace
            if not _validate_eurosat_structure(dataset_path):
                logger.error(f"La estructura del dataset en {dataset_path} no es compatible con EuroSAT")
                logger.info("Se esperan subdirectorios con imágenes, ej: AnnualCrop/, Forest/, etc.")
                raise typer.Exit(1)
        case _:
            logger.error(f"Formato {format} no implementado aún")
            raise typer.Exit(1)

    # Eliminar datos anteriores si se especifica
    if delete_previous_data and output_dir.exists():
        logger.info(f"Eliminando datos anteriores en el directorio de salida: {output_dir}")
        try:
            shutil.rmtree(output_dir, ignore_errors=True)
            logger.info(f"Datos anteriores eliminados: {output_dir}")
        except Exception as e:
            logger.warning(f"Error al eliminar los datos anteriores: {e}")
            raise typer.Exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Convirtiendo dataset a formato {format.value.upper()}")
    logger.info(f"Entrada: {dataset_path}")
    logger.info(f"Salida: {output_dir}")

    # Obtener configuración específica del formato
    config = DATASET_CONFIG.get(format, {})
    logger.debug(f"Configuración del formato: {config}")

    if format == DatasetFormat.YOLO:
        _convert_to_yolo(dataset_path, output_dir, summary)
    elif format == DatasetFormat.HUGGINGFACE:
        _convert_to_huggingface(dataset_path, output_dir, summary)
    else:
        logger.error(f"Formato {format} no implementado aún")
        raise typer.Exit(1)
    logger.success(f"Conversión completada a formato {format.value.upper()}")

    if clean:
        logger.info(f"Limpiando directorio de entrada: {dataset_path}")
        try:
            shutil.rmtree(dataset_path, ignore_errors=True)
            logger.info(f"Directorio de entrada limpiado: {dataset_path}")
        except Exception as e:
            logger.warning(f"Error al limpiar el directorio de entrada: {e}")
            raise typer.Exit(1)


@app.command()
def split_dataset(
    format: DatasetFormat = DatasetFormat.HUGGINGFACE,
    dataset_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    split: Tuple[float, float, float] = (0.9, 0.1, 0.0),
    summary: bool = True,
    clean: bool = True,
):
    """
    Divide un dataset en conjuntos de entrenamiento, prueba y validación según el formato especificado.

    Args:
        format (DatasetFormat, optional): Formato del dataset a dividir. Por defecto es DatasetFormat.HUGGINGFACE.
        dataset_path (Path, optional): Ruta al directorio de entrada con los datos a dividir. Por defecto es DATASET_CONFIG[DatasetFormat.HUGGINGFACE]["interim_folderpath"].
        output_dir (Path, optional): Ruta al directorio donde se guardarán los datos divididos. Por defecto es DATASET_CONFIG[DatasetFormat.HUGGINGFACE]["processed_folderpath"].
        split (Tuple[float, float, float], optional): Proporciones para train, test y val. Deben sumar 1.0. Por defecto es (0.9, 0.1, 0.0).
        summary (bool, optional): Si es True, genera un archivo de resumen del dataset dividido. Por defecto es True.
        clean (bool, optional): Si es True, elimina el directorio de entrada después de la división. Por defecto es True.

    Raises:
        typer.Exit: Si el directorio de entrada no existe.
        typer.Exit: Si la estructura del dataset no es compatible con el formato seleccionado.
        typer.Exit: Si los porcentajes de división no suman 1.0.
        typer.Exit: Si ocurre un error al eliminar el directorio original.
        typer.Exit: Si el formato solicitado no está implementado.

    Ejecución de ejemplo:
        >>> python -m vision_transformer.dataset split-dataset --help
    """
    # Validar que exista el directorio de entrada
    if dataset_path and not dataset_path.exists():
        logger.error(f"El directorio de entrada no existe: {dataset_path}")
        raise typer.Exit(1)

    match format:
        case DatasetFormat.YOLO:
            if not dataset_path:
                logger.debug("No se especificó un directorio de entrada, se usará el predeterminado para YOLO")
                dataset_path = DATASET_CONFIG[DatasetFormat.YOLO]["interim_folderpath"]
            if not output_dir:
                logger.debug("No se especificó un directorio de salida, se usará el predeterminado para YOLO")
                output_dir = DATASET_CONFIG[DatasetFormat.YOLO]["processed_folderpath"]
        case DatasetFormat.HUGGINGFACE:
            if not dataset_path:
                logger.debug("No se especificó un directorio de entrada, se usará el predeterminado para HUGGINGFACE")
                dataset_path = DATASET_CONFIG[DatasetFormat.HUGGINGFACE]["interim_folderpath"]
            if not output_dir:
                logger.debug("No se especificó un directorio de salida, se usará el predeterminado para HUGGINGFACE")
                output_dir = DATASET_CONFIG[DatasetFormat.HUGGINGFACE]["processed_folderpath"]

            # Validar estructura de entrada para HuggingFace
            if not _validate_huggingface_interim_structure(dataset_path):
                logger.error(f"La estructura del dataset en {dataset_path} no es compatible con HuggingFace")
                logger.info("Se espera una estructura que contiene un subdirectorio 'train' con directorios de clases")
                raise typer.Exit(1)
        case _:
            logger.error(f"Formato {format} no implementado aún")
            raise typer.Exit(1)

    # Normalizar porcentajes
    total = sum(split)
    if total != 1.0:
        logger.error(f"Los porcentajes de división deben sumar 1.0, pero se recibieron: {split}")
        raise typer.Exit(1)

    train_ratio, test_ratio, val_ratio = split

    # Preparar directorio de salida
    output_dir.mkdir(parents=True, exist_ok=True)

    # Directorio base de entrada
    source_base_dir = dataset_path / "train"

    class_dirs = [d for d in source_base_dir.iterdir() if d.is_dir()]
    if not class_dirs:
        logger.warning(f"No se encontraron subdirectorios de clases en: {source_base_dir}")
        return

    logger.debug(f"Encontradas {len(class_dirs)} clases: {[d.name for d in class_dirs]}")

    # Contar el total de archivos para la barra de progreso
    all_files: List[Path] = []
    labels: List[str] = []

    logger.debug("Escaneando archivos...")
    for class_dir in class_dirs:
        for source_file in class_dir.iterdir():
            if source_file.is_file() and source_file.suffix.lower() in IMAGE_EXTENSIONS:
                all_files.append(source_file)
                labels.append(class_dir.name)

    if not all_files:
        logger.warning(f"No se encontraron archivos de imagen en {source_base_dir}. No hay nada que dividir.")
        return

    logger.info(f"Total de {len(all_files)} archivos encontrados para dividir.")

    if train_ratio == 1.0:
        logger.warning(
            "Solo se ha especificado un conjunto de entrenamiento. No se realizará división. Simplemente se copiarán los archivos al directorio de salida."
        )
        files_train = all_files
        labels_train = labels
    else:
        logger.info(
            f"Dividiendo el dataset en train: {train_ratio*100}%, test: {test_ratio*100}%, val: {val_ratio*100}%"
        )
        # Realizar el split de train/test inicial
        files_train, files_test_val, labels_train, labels_test_val = train_test_split(
            all_files, labels, test_size=(test_ratio + val_ratio), stratify=labels, random_state=RANDOM_SEED
        )

        # Realizar el split de test/val del conjunto restante si val_ratio es mayor que 0
        files_test = []
        files_val = []
        if val_ratio > 0 and len(files_test_val) > 0:
            # Calculamos la proporción de validación respecto al total de test_val
            test_val_ratio_sum = test_ratio + val_ratio
            if test_val_ratio_sum == 0:  # Evitar división por cero si ambos son 0 (aunque ya validamos la suma total)
                test_val_ratio_sum = 1  # Solo para evitar el error, no debería darse si sum(split) == 1.0
            val_proportion_of_test_val = val_ratio / test_val_ratio_sum

            files_test, files_val, labels_test, labels_val = train_test_split(
                files_test_val,
                labels_test_val,
                test_size=val_proportion_of_test_val,
                stratify=labels_test_val,
                random_state=42,
            )
        else:
            files_test = files_test_val
            labels_test = labels_test_val  # Aunque no se usa directamente, mantener la simetría

    # Determinar qué splits procesar según los ratios
    if train_ratio == 1.0:
        splits_to_process = {
            "train": (files_train, labels_train),
        }
    elif val_ratio > 0:
        splits_to_process = {
            "train": (files_train, labels_train),
            "test": (files_test, labels_test),
            "val": (files_val, labels_val),
        }
    else:
        splits_to_process = {
            "train": (files_train, labels_train),
            "test": (files_test, labels_test),
        }

    # Copiar archivos a los directorios de salida
    copied_files = 0
    failed_copies = 0
    total_size = 0
    for split_name, (files, _) in splits_to_process.items():
        if not files:
            logger.info(f"No hay archivos para la división '{split_name}'. Saltando...")
            continue

        split_dir = output_dir / split_name
        split_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Copiando {len(files)} archivos al directorio '{split_name}': {split_dir}")

        with tqdm(total=len(files), desc=f"Copiando {split_name} files", unit="archivo") as pbar:
            for source_file in files:
                class_name = source_file.parent.name
                target_class_dir = split_dir / class_name
                target_class_dir.mkdir(exist_ok=True)
                target_file = target_class_dir / source_file.name
                try:
                    shutil.copy2(source_file, target_file)

                    # Actualizar estadísticas
                    file_size = source_file.stat().st_size
                    total_size += file_size
                    copied_files += 1

                    # Actualizar descripción con estadísticas
                    pbar.set_postfix(
                        {
                            "Copiados": copied_files,
                            "Fallos": failed_copies,
                            "Tamaño": f"{total_size / (1024*1024):.1f}MB",
                        }
                    )
                except Exception as e:
                    failed_copies += 1
                    logger.warning(f"Error al copiar {source_file} a {target_file}: {e}")

                    # Actualizar descripción con estadísticas
                    pbar.set_postfix(
                        {
                            "Copiados": copied_files,
                            "Fallos": failed_copies,
                            "Tamaño": f"{total_size / (1024*1024):.1f}MB",
                        }
                    )
                finally:
                    pbar.update(1)

    # Crear archivo de resumen
    if summary:
        _create_split_summary(dataset_path, output_dir, splits_to_process, copied_files, failed_copies, total_size)

    if failed_copies > 0:
        logger.warning(f"División completada con {failed_copies} errores de {copied_files} archivos")
    else:
        logger.success(f"División completada exitosamente: {copied_files} archivos copiados")

    # Limpiar el directorio original si clean es True
    if clean:
        logger.info(f"Limpiando directorio original: {dataset_path}")
        try:
            shutil.rmtree(dataset_path)
            logger.success(f"Directorio original limpiado: {dataset_path}")
        except Exception as e:
            logger.error(f"Error al limpiar el directorio original {dataset_path}: {e}")
            raise typer.Exit(1)


def load_huggingface_dataset(
    dataset_path: Path = DATASET_CONFIG[DatasetFormat.HUGGINGFACE]["processed_folderpath"],
) -> Dataset:
    logger.info("Cargando el dataset procesado...")
    if not dataset_path.exists() or not dataset_path.is_dir():
        raise FileNotFoundError(f"El directorio del dataset no existe: {dataset_path}")

    result, only_train = _validate_huggingface_structure(dataset_path)
    if not result:
        raise ValueError(f"La estructura del dataset en {dataset_path} no es compatible con HuggingFace")

    if only_train:
        logger.info("El dataset solo contiene el conjunto de entrenamiento. Cargando...")
        return load_dataset(str(dataset_path), split="train")
    else:
        logger.info("El dataset contiene múltiples conjuntos (train, test, val). Cargando todos...")
        # Cargar el dataset completo, incluyendo train, test y val
        return load_dataset(str(dataset_path))


def _convert_to_yolo(input_path: Path, output_path: Path):
    """Convierte el dataset al formato YOLO"""
    logger.info("Implementando conversión a YOLO...")
    # TODO: Implementar lógica específica de YOLO
    raise NotImplementedError("Conversión a YOLO pendiente de implementar")


def _convert_to_huggingface(input_path: Path, output_path: Path, summary: bool = True):
    """
    Convierte el dataset al formato compatible con HuggingFace.

    El formato de los archivos de entrada para EuroSAT_RGB es:
    EuroSAT_RGB
    ├── AnnualCrop
    │   ├── AnnualCrop_1.jpg
    │   ├── AnnualCrop_2.jpg
    │   └── ...
    ├── Forest
    │   └── ...
    └── ...

    El objetivo es convertir estos datos a un formato:
    EuroSAT_RGB_huggingface
    └── train
        ├── AnnualCrop
        │   ├── AnnualCrop_1.jpg
        │   ├── AnnualCrop_2.jpg
        │   └── ...
        ├── Forest
        │   └── ...
        └── ...

    En este caso, simplemente se crea una estructura de directorios similar a la original.

    Args:
        input_path (Path): Ruta al directorio con los datos de entrada a convertir.
        output_path (Path): Ruta al directorio donde se guardarán los datos convertidos.

    Raises:
        FileNotFoundError: Si el directorio de entrada no existe.
        PermissionError: Si no hay permisos para crear/escribir en el directorio de salida.
    """
    logger.info("Iniciando conversión a formato HuggingFace...")

    if not input_path.exists():
        raise FileNotFoundError(f"El directorio de entrada no existe: {input_path}")

    # Crear directorio train dentro del output_path
    train_dir = output_path / "train"
    train_dir.mkdir(parents=True, exist_ok=True)

    # Obtener todas las carpetas de clases (subdirectorios del input_path)
    class_dirs = [d for d in input_path.iterdir() if d.is_dir()]

    if not class_dirs:
        logger.warning(f"No se encontraron subdirectorios de clases en: {input_path}")
        return

    logger.debug(f"Encontradas {len(class_dirs)} clases: {[d.name for d in class_dirs]}")

    # Contar el total de archivos para la barra de progreso
    total_files = 0
    files_to_copy: List[Tuple[Path, Path]] = []

    logger.debug("Escaneando archivos...")
    for class_dir in class_dirs:
        # Crear directorio de clase en destino
        target_class_dir = train_dir / class_dir.name
        target_class_dir.mkdir(exist_ok=True)

        # Buscar archivos de imagen (extensiones comunes)
        for file_path in class_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
                target_file_path = target_class_dir / file_path.name
                files_to_copy.append((file_path, target_file_path))
                total_files += 1

    if total_files == 0:
        logger.warning("No se encontraron archivos de imagen para copiar")
        return

    logger.info(f"Iniciando copia de {total_files} archivos...")

    # Copiar archivos con barra de progreso
    copied_files = 0
    failed_copies = 0
    total_size = 0

    with tqdm(total=total_files, desc="Copiando archivos", unit="archivo", unit_scale=False) as pbar:
        for source_file, target_file in files_to_copy:
            try:
                # Copiar archivo manteniendo metadatos
                shutil.copy2(source_file, target_file)

                # Actualizar estadísticas
                file_size = source_file.stat().st_size
                total_size += file_size
                copied_files += 1

                # Actualizar descripción con estadísticas
                pbar.set_postfix(
                    {"Copiados": copied_files, "Fallos": failed_copies, "Tamaño": f"{total_size / (1024*1024):.1f}MB"}
                )
            except Exception as e:
                failed_copies += 1
                logger.warning(f"Error copiando {source_file.name}: {e}")

                # Actualizar descripción con estadísticas
                pbar.set_postfix(
                    {"Copiados": copied_files, "Fallos": failed_copies, "Tamaño": f"{total_size / (1024*1024):.1f}MB"}
                )
            finally:
                pbar.update(1)

    # Crear archivo de resumen
    if summary:
        _create_dataset_summary(output_path, train_dir, total_files, copied_files, failed_copies, total_size)

    # Log final
    if failed_copies > 0:
        logger.warning(f"Conversión completada con {failed_copies} errores de {total_files} archivos")
    else:
        logger.success(f"Conversión completada exitosamente: {copied_files} archivos copiados")

    logger.info(f"Tamaño total del dataset: {total_size / (1024*1024):.2f} MB")
    logger.info(f"Estructura creada en: {train_dir}")


def _validate_huggingface_structure(dataset_path: Path) -> Tuple[bool, bool]:
    """Valida que la estructura del dataset sea compatible con HuggingFace, o sea:
    EuroSAT_RGB_huggingface
    ├── train
    │    ├── AnnualCrop
    │    │   ├── AnnualCrop_1.jpg
    │    │   ├── AnnualCrop_2.jpg
    │    │   └── ...
    │    ├── Forest
    │    │   └── ...
    │    ├── ...
    ├── test
    │    ├── ...
    │    └── ...
    └── val
         └── ...

    Puede tener solo el conjunto de entrenamiento, en cuyo caso no habrá subdirectorios de test o val.
    La función verifica que:
      - El directorio existe y es un directorio.
      - Contiene un subdirectorio 'train'.
      - 'train' contiene al menos un subdirectorio de clase.
      - Cada subdirectorio de clase contiene al menos un archivo de imagen válido.

    Args:
        dataset_path (Path): Ruta al directorio raíz del dataset a validar.

    Returns:
        Tuple[bool, bool]:
            - True si la estructura es válida, False en caso contrario.
            - True si solo tiene el conjunto de entrenamiento, False si también tiene test o val.
    """
    if not dataset_path.exists() or not dataset_path.is_dir():
        return False, False

    # Verificar que exista el subdirectorio 'train'
    train_dir = dataset_path / "train"
    if not train_dir.exists() or not train_dir.is_dir():
        return False, False

    # Verificar que haya al menos un subdirectorio de clase en 'train'
    class_dirs = [d for d in train_dir.iterdir() if d.is_dir()]
    if not class_dirs:
        return False, True  # Solo tiene el conjunto de entrenamiento

    # Verificar que cada subdirectorio de clase contenga al menos un archivo de imagen
    for class_dir in class_dirs:
        image_files = [f for f in class_dir.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]
        if not image_files:
            return False, False

    # Verificar si existen los subdirectorios 'test' y 'val'
    has_test = (dataset_path / "test").exists()
    has_val = (dataset_path / "val").exists()

    if has_test and not (dataset_path / "test").is_dir():
        return False, False
    if has_val and not (dataset_path / "val").is_dir():
        return False, False

    if has_test:
        test_dir = dataset_path / "test"
        if not test_dir.exists() or not test_dir.is_dir():
            return False, False
        # Verificar que haya al menos un subdirectorio de clase en 'test'
        test_class_dirs = [d for d in test_dir.iterdir() if d.is_dir()]
        if not test_class_dirs:
            return False, False
        # Verificar que cada subdirectorio de clase contenga al menos un archivo de imagen
        for class_dir in test_class_dirs:
            image_files = [f for f in class_dir.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]
            if not image_files:
                return False, False

    if has_val:
        val_dir = dataset_path / "val"
        if not val_dir.exists() or not val_dir.is_dir():
            return False, False
        # Verificar que haya al menos un subdirectorio de clase en 'val'
        val_class_dirs = [d for d in val_dir.iterdir() if d.is_dir()]
        if not val_class_dirs:
            return False, False
        # Verificar que cada subdirectorio de clase contenga al menos un archivo de imagen
        for class_dir in val_class_dirs:
            image_files = [f for f in class_dir.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]
            if not image_files:
                return False, False

    return True, not has_test and not has_val


# Función auxiliar para validar la estructura de entrada
def _validate_eurosat_structure(input_path: Path) -> bool:
    """
    Valida que la estructura de entrada sea la esperada, o sea:
    EuroSAT_RGB
    ├── AnnualCrop
    │   ├── AnnualCrop_1.jpg
    │   ├── AnnualCrop_2.jpg
    │   └── ...
    ├── Forest
    │   └── ...
    └── ...

    Args:
        input_path: Directorio a validar

    Returns:
        True si la estructura es válida
    """
    if not input_path.exists() or not input_path.is_dir():
        return False

    # Verificar que hay subdirectorios
    subdirs = [d for d in input_path.iterdir() if d.is_dir()]
    if not subdirs:
        return False

    # Verificar que cada subdirectorio contenga al menos un archivo de imagen
    for subdir in subdirs:
        image_files = [f for f in subdir.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]
        if image_files:
            return True

    return False


def _validate_huggingface_interim_structure(dataset_path: Path) -> bool:
    """
    Valida que la estructura del dataset sea la siguiente:
    EuroSAT_RGB_huggingface
    └── train
        ├── AnnualCrop
        │   ├── AnnualCrop_1.jpg
        │   ├── AnnualCrop_2.jpg
        │   └── ...
        ├── Forest
        │   └── ...
        └── ...

    La función verifica que:
      - El directorio existe y es un directorio.
      - Contiene un subdirectorio 'train'.
      - 'train' contiene al menos un subdirectorio de clase.
      - Cada subdirectorio de clase contiene al menos un archivo de imagen válido.

    Returns:
        bool: True si la estructura es válida, False en caso contrario.

    Args:
        dataset_path (Path): Ruta al directorio raíz del dataset a validar.
    """
    if not dataset_path.exists() or not dataset_path.is_dir():
        return False

    # Verificar que exista el subdirectorio 'train'
    train_dir = dataset_path / "train"
    if not train_dir.exists() or not train_dir.is_dir():
        return False

    # Verificar que haya al menos un subdirectorio de clase en 'train'
    class_dirs = [d for d in train_dir.iterdir() if d.is_dir()]
    if not class_dirs:
        return False

    # Verificar que cada subdirectorio de clase contenga al menos un archivo de imagen
    for class_dir in class_dirs:
        image_files = [f for f in class_dir.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]
        if not image_files:
            return False

    return True


def _create_dataset_summary(
    output_path: Path, train_dir: Path, total_files: int, copied_files: int, failed_copies: int, total_size: int
):
    """
    Crea un archivo de resumen del dataset convertido.

    Args:
        output_path: Directorio de salida principal
        train_dir: Directorio train creado
        total_files: Total de archivos procesados
        copied_files: Archivos copiados exitosamente
        failed_copies: Archivos que fallaron al copiar
        total_size: Tamaño total en bytes
    """
    summary_file = output_path / "dataset_info.txt"

    # Obtener información de clases
    class_info = {}
    for class_dir in train_dir.iterdir():
        if class_dir.is_dir():
            image_count = len([f for f in class_dir.iterdir() if f.is_file()])
            class_info[class_dir.name] = image_count

    # Escribir resumen
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("=== RESUMEN DEL DATASET HUGGINGFACE ===\n\n")
        f.write(f"Archivos totales procesados: {total_files}\n")
        f.write(f"Archivos copiados exitosamente: {copied_files}\n")
        f.write(f"Archivos fallidos: {failed_copies}\n")
        f.write(f"Tamaño total: {total_size / (1024*1024):.2f} MB\n\n")

        f.write("=== DISTRIBUCIÓN POR CLASES ===\n")
        for class_name, count in sorted(class_info.items()):
            f.write(f"{class_name}: {count} imágenes\n")

        f.write(f"\n=== ESTRUCTURA DE DIRECTORIOS ===\n")
        f.write(f"train/\n")
        for class_name in sorted(class_info.keys()):
            f.write(f"├── {class_name}/\n")
        f.write("\n")

    logger.info(f"Resumen del dataset guardado en: {summary_file}")


def _create_split_summary(
    dataset_path: Path,
    output_path: Path,
    splits_to_process: Dict[str, Any],
    copied_files: int,
    failed_copies: int,
    total_size: int,
) -> None:
    """
    Crea un archivo de resumen para la división del dataset en los conjuntos especificados (train, test, val).

    Args:
        dataset_path (Path): Ruta al directorio original del dataset antes de la división.
        output_path (Path): Ruta al directorio donde se guardará el resumen de la división.
        splits_to_process (dict): Diccionario con los splits a procesar y sus archivos, ej: {"train": ([files], [labels]), ...}.
        copied_files (int): Número de archivos copiados exitosamente.
        failed_copies (int): Número de archivos que fallaron al copiarse.
        total_size (int): Tamaño total en bytes de los archivos copiados.

    Returns:
        None
    """
    previous_summary_file = dataset_path / "dataset_info.txt"
    summary_file_target = output_path / "dataset_info.txt"

    if previous_summary_file.exists():
        with open(previous_summary_file, "a", encoding="utf-8") as f:
            _write_split_summary(splits_to_process, copied_files, failed_copies, total_size, f)
        # Copiar el resumen al directorio de salida
        shutil.copy(previous_summary_file, summary_file_target)
    else:
        with open(summary_file_target, "w", encoding="utf-8") as f:
            _write_split_summary(splits_to_process, copied_files, failed_copies, total_size, f)

    logger.info(f"Resumen del dataset guardado en: {summary_file_target}")


def _write_split_summary(
    splits_to_process: Dict[str, Any],
    copied_files: int,
    failed_copies: int,
    total_size: int,
    f,
) -> None:
    """
    Escribe un resumen de la división del dataset en el archivo proporcionado.

    Args:
        splits_to_process (Dict[str, Tuple[List[Any], List[Any]]]): Diccionario con los splits a procesar y sus archivos, ej: {"train": ([files], [labels]), ...}.
        copied_files (int): Número de archivos copiados exitosamente.
        failed_copies (int): Número de archivos que fallaron al copiarse.
        total_size (int): Tamaño total en bytes de los archivos copiados.
        f: Archivo abierto en modo escritura donde se escribirá el resumen.

    Returns:
        None
    """
    f.write("=== RESUMEN DE LA DIVISIÓN DEL DATASET ===\n\n")
    f.write(f"Archivos totales procesados: {sum(len(files) for files, _ in splits_to_process.values())}\n")
    f.write(f"Archivos copiados exitosamente: {copied_files}\n")
    f.write(f"Archivos fallidos: {failed_copies}\n")
    f.write(f"Tamaño total: {total_size / (1024*1024):.2f} MB\n\n")


if __name__ == "__main__":
    app()
