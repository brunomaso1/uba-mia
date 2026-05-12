# 💬 Registro de Prompts

---

## 🔁 Turno 1

### 👤 Usuario

> Construí un captcha de carácteres chinos, pero desde el captcha salen volando todas las sílabas chinas que existen, y el usuario tiene que seleccionar las que corresponden al captcha en orden.

**Estructura:** Utiliza HTML semántico.  
**Estilo:** Utiliza un diseño similar a material design.  
**Comportamiento:**
- Los carácteres quedan en la pantalla flotando.
- Existe un tiempo límite, configurable entre 5 y 30 segundos.
- Se puede seleccionar la cantidad de carácteres para el captcha entre 5 y 10 carácteres.
- La selección debe ser en orden.
- Los carácteres "vuelan" desde un punto del capcha.

**Constraints:** Un solo archivo HTML, vanilla JS, sin dependencias externas. JS y CSS incluído en el mismo archivo.

### 🤖 IA

Listo. Creé un único archivo HTML con:

- ✅ HTML semántico.
- ✅ Estilo inspirado en Material Design.
- ✅ Caracteres chinos flotando desde un punto central.
- ✅ Selección obligatoria en orden.
- ✅ Tiempo configurable entre 5 y 30 segundos.
- ✅ Cantidad configurable entre 5 y 10 caracteres.
- ✅ Vanilla JS puro.
- ✅ CSS y JS embebidos en el mismo archivo.
- ✅ Sin dependencias externas.

---

## 🔁 Turno 2

### 👤 Usuario

> Corrige estos errores:

**Errores a corregir:**
1. No se están viendo los carácteres que está flotando. Tienen color blanco y no se ven correctamente. Podrías convertir el texto en negro?
2. El captcha aparece con el símbolo `?`. Deberían aparecer los carácteres que se deben buscar en la sopa de carácteres chinos.

**Cosas que están bien:**
1. La UI está bien. Elimina el punto central azul, no es necesario.

### 🤖 IA

Realicé las correcciones:

- 🔧 Los caracteres flotantes ahora tienen texto negro para que sean visibles correctamente.
- 🔧 El captcha ahora muestra directamente los caracteres que deben seleccionarse, en vez de `?`.
- 🔧 Eliminé el punto azul central y el efecto radial asociado.

La UI y el comportamiento general se mantuvieron igual.

---

## 🔁 Turno 3

### 👤 Usuario

> Perfecto, ya quedó bien.
>
> Podrías agregar la opción de que la cantidad de carácteres sea de 2 hasta 10? Hoy es de 5 a 10.

### 🤖 IA

Actualicé el rango de cantidad de caracteres para que ahora permita seleccionar entre 2 y 10 caracteres.