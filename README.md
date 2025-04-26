# UBA-NLP2
Repositorio de la Maestría en Inteligencia Artificial (MIA) - Universidad de Buenos Aires (UBA) - NLP 2

## Estructura
Puedes encontrar la siguiente estructura de carpetas en el repositorio:

```bash
mia-nlp2
├── Ejemplos/
├── Practico 1/
├── Practico 2/
├── Practico 3/
└── resources/
```

- **[Ejemplos/](./mia-nlp2/Ejemplos/)**: contiene ejemplos de usos y pruebas de conceptos.
- **[Practico 1/](./mia-nlp2/Practico%201/)**: contiene el primer práctico de la materia.
- **[Practico 2/](./mia-nlp2/Practico%202/)**: contiene el segundo práctico de la materia.
- **[Practico 3/](./mia-nlp2/Practico%203/)**: contiene el tercer práctico de la materia.
- **[resources/](./mia-nlp2/resources/)**: contiene recursos adicionales

> [!Important]  
> Cada práctico tiene su propio notebook llamado `research.ipynb` donde se encuentra el análisis realizado. En él se incluye como ejecutar las aplicaciones de los prácticos 1 y 2. El práctico 3 no tiene aplicación, dado que es un práctico de investigación.

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

