# Actividad práctica 2: OpenAPI y ChatGPT Canvas

## Consigna

Esta actividad práctica tiene como objetivo generar una especificación de OpenAPI mediante ChatGPT Canvas.

## Requisitos

- Tres métodos (mínimo: GET, POST, DELETE).
- Jerarquía de recursos (por ejemplo, `/users` y `/users/{id}`).
- Una respuesta de error (al menos un 400 o 404 documentado).
- Schemas tipados (type, required, format).
- Iteración en vivo: Agregar un endpoint sin sobrescribir todo.

## Entregables

1. `openapi.yaml` $\rightarrow$ La especificación de OpenAPI generada, lista para ser utilizada con herramientas como Swagger UI o Postman.
2. `prompts.md` $\rightarrow$ La secuencia de prompts en orden, con una anotación breve por prompt.
3. `README.md` $\rightarrow$ Qué es la página, quien lo construyó, qué funcionó y qué no.