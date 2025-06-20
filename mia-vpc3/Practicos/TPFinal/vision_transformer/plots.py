from collections import Counter
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
from PIL import Image
from loguru import logger
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from tqdm import tqdm
import typer

import plotly.graph_objects as go
import plotly.figure_factory as ff
import pandas as pd
from pathlib import Path

from vision_transformer.config import DATASET_CONFIG, FIGURES_DIR, PROCESSED_DATA_DIR
from vision_transformer.utils import DatasetFormat

from sklearn.metrics import confusion_matrix
import numpy as np
import matplotlib.pyplot as plt

app = typer.Typer()


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = PROCESSED_DATA_DIR / "dataset.csv",
    output_path: Path = FIGURES_DIR / "plot.png",
    # -----------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----
    logger.info("Generating plot from data...")
    for i in tqdm(range(10), total=10):
        if i == 5:
            logger.info("Something happened for iteration 5.")
    logger.success("Plot generation complete.")
    # -----------------------------------------


def show_image(image: Image, label: str = "Unknown") -> None:
    """
    Muestra una imagen y su etiqueta.
    Args:
        image (Image.Image): Imagen a mostrar.
        label (str): Etiqueta de la imagen.
    """
    plt.imshow(image)
    plt.title(f"Etiqueta: {label}")
    plt.axis("off")
    plt.show()


def show_image_grid(data: dict, title: str = "Grilla de Imágenes", num_cols: int = 4) -> None:
    """
    Muestra una grilla de imágenes con sus etiquetas.

    Args:
        data (dict): Diccionario con las claves "images" (lista de objetos Image)
                     y "labels" (lista de strings de etiquetas).
        title (str): Título general para la grilla de imágenes.
        num_cols (int): Número de columnas en la grilla.
    """
    images = data.get("images", [])
    labels = data.get("labels", [])

    if not images:
        logger.warning("No hay imágenes para mostrar.")
        return

    num_images = len(images)
    num_cols = max(1, min(num_cols, num_images))
    num_rows = math.ceil(num_images / num_cols)

    fig, axes = plt.subplots(num_rows, num_cols, figsize=(num_cols * 3, num_rows * 3))
    axes = axes.flatten()

    for i in range(num_images):
        ax = axes[i]
        ax.imshow(images[i])
        ax.set_title(f"Etiqueta: {labels[i] if i < len(labels) else 'Unknown'}")
        ax.axis("off")

    # Ocultar subplots vacíos si hay...
    for j in range(num_images, len(axes)):
        fig.delaxes(axes[j])

    fig.suptitle(title, fontsize=16)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()


def plot_class_distribution(dataset, id2label, splits=("train",), colors=None):
    """
    Grafica la distribución de clases en un único gráfico de barras apiladas por clase.

    Args:
        dataset: diccionario HuggingFace con claves por split.
        id2label: diccionario {id: nombre de clase}.
        splits: tupla con los nombres de los splits a incluir.
        colors: tupla de colores (uno por split), opcional.
    """
    from collections import Counter
    import pandas as pd
    import matplotlib.pyplot as plt

    # Contar ocurrencias por clase y split
    data = {split: Counter(dataset[split]["label"]) for split in splits}

    # Construir DataFrame
    rows = []
    for idx, name in id2label.items():
        row = {"class": f"{idx}: {name}"}
        for split in splits:
            row[split] = data[split].get(idx, 0)
        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.set_index("class")
    df = df.loc[df.sum(axis=1).sort_values(ascending=True).index]  # ordenar por total

    # Graficar barras apiladas
    ax = df.plot.barh(
        stacked=True,
        figsize=(6, 4),
        width=0.8,
        color=colors if colors is not None else None
    )

    ax.set_title("Cantidad de imágenes por clase (stacked por split)", fontsize=10)
    ax.set_ylabel("")
    ax.set_xlabel("Cantidad de imágenes")
    ax.set_xlim([0, df.sum(axis=1).max() * 1.15])  # margen derecho para etiquetas y leyenda

    # Etiquetas internas
    for i, (idx, row) in enumerate(df.iterrows()):
        x_offset = 0
        for j, split in enumerate(splits):
            count = row[split]
            if count > 0:
                ax.text(
                    x_offset + count / 2,
                    i,
                    str(count),
                    va="center",
                    ha="center",
                    fontsize=7,
                    color="white",
                    fontweight="bold"
                )
                x_offset += count

    plt.tight_layout()
    plt.show()


def _compute_class_histograms(dataset, id2label, split="train"):
    class_histograms = {}

    y = np.array(dataset[split]["label"])
    for label_id, label_name in id2label.items():
        imgs_idx = np.where(y == label_id)[0]

        # Accumulate histograms per channel
        hist_H = np.zeros(180, dtype=np.float32)
        hist_S = np.zeros(256, dtype=np.float32)
        hist_L = np.zeros(256, dtype=np.float32)

        for idx in imgs_idx:
            img_pil = dataset[split][int(idx)]["image"]
            img_hls = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2HLS)

            # Split H, L, S channels
            H, L, S = cv2.split(img_hls)

            hist_H += cv2.calcHist([H], [0], None, [180], [0, 180]).flatten()
            hist_S += cv2.calcHist([S], [0], None, [256], [0, 256]).flatten()
            hist_L += cv2.calcHist([L], [0], None, [256], [0, 256]).flatten()

        class_histograms[label_name] = [hist_H, hist_S, hist_L]

    return class_histograms


def _get_colormap_bar_colors(channel, bins=256):
    """Return a list of RGB colors representing the channel values visually."""
    if channel == "H":  # Hue (0–179 in OpenCV HLS, but assuming 0–255 here)
        hsv = np.stack([np.linspace(0, 179, bins), np.full(bins, 255), np.full(bins, 255)], axis=1).astype(np.uint8)
        rgb = cv2.cvtColor(hsv.reshape(-1, 1, 3), cv2.COLOR_HSV2RGB).reshape(-1, 3)
    elif channel == "S":  # Saturation
        hsv = np.stack([np.full(bins, 0), np.linspace(0, 255, bins), np.full(bins, 200)], axis=1).astype(np.uint8)
        rgb = cv2.cvtColor(hsv.reshape(-1, 1, 3), cv2.COLOR_HSV2RGB).reshape(-1, 3)
    elif channel == "L":  # Lightness
        rgb = np.stack([np.linspace(0, 255, bins)] * 3, axis=1)
    else:
        raise ValueError(f"Invalid channel: {channel}")
    return rgb / 255  # Normalize for matplotlib


def plot_class_histograms(dataset, id2label, split="train"):
    class_histograms = _compute_class_histograms(dataset, id2label, split)

    channel_bins = {"H": 180, "S": 256, "L": 256}

    class_names = list(class_histograms.keys())
    channel_names = ["H", "S", "L"]
    full_titles = ["Hue", "Saturation", "Lightness"]

    num_classes = len(class_names)
    fig, axes = plt.subplots(num_classes, 3, figsize=(9, num_classes * 1), sharex=True, sharey=False)

    if num_classes == 1:
        axes = np.expand_dims(axes, 0)

    for row_idx, class_name in enumerate(class_names):
        histograms = class_histograms[class_name]

        for col_idx, (channel, hist) in enumerate(zip(channel_names, histograms)):
            ax = axes[row_idx][col_idx]

            bins = channel_bins[channel]
            colors = _get_colormap_bar_colors(channel, bins)

            # Normalize histogram
            hist = hist[:bins]  # Ensure it's trimmed properly
            hist = hist / hist.max()

            for x in range(bins):
                ax.bar(x, hist[x], color=colors[x], width=1)

            ax.set_xlim([0, bins])
            ax.set_ylim([0, 1])
            ax.set_xticks([])
            ax.set_yticks([])

            if row_idx == 0:
                ax.set_title(full_titles[col_idx], fontsize=10)

            if col_idx == 0:
                ax.set_ylabel(class_name, fontsize=9, rotation=0, labelpad=55, va="center")

    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    fig.suptitle("Histograma acumulado por clase para los canales HSL", fontsize=16)
    plt.show()


def plot_metric(
    df: pd.DataFrame,
    x_col: str,
    y_cols: List[str],
    title: str,
    filename: str,
    dirpath: Path = FIGURES_DIR,
    y_labels: List[str] = None,
) -> None:
    """
    Grafica métricas en función de una columna específica del DataFrame.

    Args:
        df (pd.DataFrame): DataFrame que contiene los datos a graficar.
        x_col (str): Nombre de la columna que se usará como eje X.
        y_cols (List[str]): Lista de nombres de columnas que se graficarán en el eje Y.
        title (str): Título del gráfico.
        filename (str): Nombre del archivo para guardar el gráfico.
        dirpath (Path, optional): Directorio donde se guardará el gráfico. Por defecto es FIGURES_DIR.
        y_labels (List[str], optional): Lista de etiquetas para las métricas en el gráfico. Por defecto es None.

    Ejemplo de uso:
        >>> df = pd.DataFrame({
        ...    "epoch": [1, 2, 3, 4],
        ...    "accuracy": [0.8, 0.85, 0.9, 0.92],
        ...    "loss": [0.5, 0.4, 0.3, 0.2]
        ... })
        >>> plot_metric(
        ...    df=df,
        ...    x_col="epoch",
        ...    y_cols=["accuracy", "loss"],
        ...    title="Curvas de Métricas",
        ...    filename="metric_curves",
        ...    y_labels=["Precisión", "Pérdida"]
        ... )
    """
    fig = go.Figure()

    for i, y_col in enumerate(y_cols):
        fig.add_trace(
            go.Scatter(x=df[x_col], y=df[y_col], mode="lines+markers", name=y_labels[i] if y_labels else y_col)
        )

    fig.update_layout(
        title=title, xaxis_title=x_col, yaxis_title="Valor", legend_title="Métrica", template="plotly_white"
    )

    fig.show()

    dirpath.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(dirpath / f"{filename}.html"))
    fig.write_image(str(dirpath / f"{filename}.png"))


def plot_confusion_matrix(
    y_true, y_pred, filename, dirpath: Path = FIGURES_DIR, labels=None, show_as_percentaje=True
) -> None:
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    cm = cm.astype(np.int32)

    # Calcular porcentajes por fila
    cm_sum = cm.sum(axis=1, keepdims=True)
    cm_percent = np.divide(cm, cm_sum, where=cm_sum != 0) * 100

    # Combinar texto: valor (xx) + porcentaje (yy%)
    z_text = (
        [
            [f"{pct:.1f}%" if cm_sum[i][0] != 0 else "0" for j, (val, pct) in enumerate(zip(row, cm_percent[i]))]
            for i, row in enumerate(cm)
        ]
        if show_as_percentaje
        else cm.astype(str).tolist()
    )

    fig = ff.create_annotated_heatmap(
        z=cm, x=labels, y=labels, annotation_text=z_text, colorscale="Blues", showscale=True, reversescale=False
    )

    fig.update_layout(
        title="Matriz de Confusion",
        xaxis_title="Etiqueta Predicha",
        yaxis_title="Etiqueta Verdadera",
        template="plotly_white",
    )

    fig.update_yaxes(autorange="reversed")

    fig.show()

    dirpath.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(dirpath / f"{filename}.html"))
    fig.write_image(str(dirpath / f"{filename}.png"))


def plot_radar_chart(
    df: pd.DataFrame,
    metrics: List[str],
    title: str,
    filename: str,
    range_values: List[float] = [0.9, 1.0],
    dirpath: Path = FIGURES_DIR,
    colors: Optional[Dict[str, str]] = None,
    fig_size: Optional[Tuple[int, int]] = None
) -> None:
    fig = go.Figure()

    # Creamos los ejes del radar chart
    for model in df["Model"].unique():
        model_data = df[df["Model"] == model].iloc[0]
        values = [model_data[metric] for metric in metrics]
        values = values + [values[0]]  # Esto sirve para cerrar el gráfico

        fig.add_trace(
            go.Scatterpolar(
                r=values,
                theta=metrics + [metrics[0]],  # Se repite para cerrar el gráfico
                # fill='toself', # Rellenar el área del gráfico
                name=model,
                line=dict(color=colors[model]) if colors and model in colors else None,
            )
        )

    fig.update_layout(
        polar=dict(
            radialaxis_visible=True,
            radialaxis=dict(
                gridcolor="rgba(0, 0, 0, 0.2)",
                linecolor="rgba(0, 0, 0, 0.2)",
                tickfont_color="rgba(0, 0, 0, 0.8)",
                range=range_values,
            ),
            angularaxis=dict(
                linewidth=1,
                linecolor="gray",
                gridcolor="rgba(0, 0, 0, 0.2)",
                tickfont_color="rgba(0, 0, 0, 0.8)",
                ticklen=10,
                tickfont_size=10,
            ),
        ),
        title=title,
        title_x=0.5,  # Center the title
        legend=dict(orientation="v", yanchor="bottom", y=0.75, xanchor="right", x=1.00),
    )

    if fig_size:
        fig.update_layout(width=fig_size[0], height=fig_size[1])

    fig.show()
    dirpath.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(dirpath / f"{filename}.html"))
    fig.write_image(str(dirpath / f"{filename}.png"))


if __name__ == "__main__":
    app()
