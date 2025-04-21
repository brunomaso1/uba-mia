# Aprendizaje por Refuerzo - Trabajos Prácticos

Este repositorio contiene los trabajos prácticos de la materia **Aprendizaje por Refuerzo I**, parte del posgrado en Inteligencia Artificial.

## Objetivo

Explorar, implementar y entrenar agentes que interactúan con entornos complejos utilizando técnicas clásicas de Aprendizaje por Refuerzo (Reinforcement Learning).

## Entorno de trabajo

Este proyecto utiliza [Poetry](https://python-poetry.org/) para la gestión del entorno virtual y las dependencias.  
Para instalar el entorno y trabajar correctamente:

```bash
poetry install
poetry shell
```

> Recordá activar el entorno con `poetry shell` antes de correr cualquier script.

## Trabajos prácticos disponibles

- `TP1-QLearning`: Implementación y entrenamiento de un agente taxi usando **Q-Learning** en un entorno personalizado tipo ciudad, con:
  - Obstáculos (manzanas)
  - Sentido único de circulación por calles
  - Penalizaciones por circular en contramano
  - Recogida y entrega de pasajeros

---
---

## TP1 - Q-Learning

### Descripción

El agente aprende a moverse en una ciudad cuadriculada simulada, optimizando su política para:
- Recoger pasajeros en ubicaciones aleatorias
- Llevarlos a su destino
- Minimizar penalizaciones por errores y tiempo

El entorno simula calles de un solo sentido y permite renderizar visualmente los movimientos del taxi.


### Entrenamiento y prueba

Asegurate de estar dentro de la carpeta `TP1-QLearning` para que se puedan importar correctamente los módulos del entorno:

```bash
cd TP1-QLearning
```

#### Entrenamiento (`train.py`)

- Entrena una Q-table utilizando **Optuna** para buscar los mejores hiperparámetros.
- Guarda los resultados y genera visualizaciones de la evolución del aprendizaje.
- También evalúa el modelo final entrenado.

```bash
python train.py
```



#### Evaluación (`test.py`)

- Carga la mejor Q-table entrenada y realiza una simulación visual del taxi operando con la política aprendida.

```bash
python test.py --video
```

Esto generará un video del recorrido en `results/best_result/img/`.

> Si querés evitar visualizar en pantalla cada paso, podés usar:  
> `--no-render` para desactivar el render  
> `--video` para guardar un GIF/MP4 del recorrido


## Requisitos

- Python 3.10+
- [`poetry`](https://python-poetry.org/docs/#installation)

Instalá las dependencias con:

```bash
poetry install
```