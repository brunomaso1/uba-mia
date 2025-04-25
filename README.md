# uba-mia
Repositorio de la Maestría en Inteligencia Artificial (MIA) - Universidad de Buenos Aires (UBA)

## Estructura
Cada rama es una materia.

## Manejo de dependencias

Para el manejo de dependencias se utiliza poetry. Se puede instalar desde la página oficial de poetry: https://python-poetry.org/docs/#installation
Una vez instalado, se puede instalar las dependencias del proyecto con el siguiente comando:

```bash
poetry install
```

### Comandos útiles

- Para instalar una nueva dependencia:
```bash
poetry add <nombre-dependencia>
poetry add <nombre-dependencia> --dev # para dependencias de desarrollo
```

- Listar las dependencias instaladas:
```bash
poetry show
```

- Listar intérpretes de python disponibles:
```bash
poetry python list
```

- Configurar entorno virtual para crearse en el directorio del proyecto:
```bash
poetry config virtualenvs.in-project true
```

- Activar el entorno virtual:
```powershell
Invoke-Expression (poetry env activate)
```

- Desactivar el entorno virtual:
```bash
deactivate
```

- Especificar el intérprete de python a utilizar:
```bash
poetry env use <ruta-al-intérprete-python>
```

