# 💬 Registro de Prompts

---

## 🔁 Turno 1

### 👤 Usuario

Puedes crear un openapi.yaml (3.1) para una API de un proyecto de facturación?

Recursos:
- EmpresasDelUsuario {id, usuario, empresa}
- Facturas {id, monto, fecha, numero}
- Certificados {id, proveedor, fechaVencimiento}


Endpoints GETs:
- GET /{empresa}/invoices
- GET /user-companies
- GET /certificates

Incorpora los demás métodos para el endpoint "invoices". El cual es el único que se puede recibir, eliminar, etc. de las facturas.
Las compañías y certificados no se pueden hacer altas, bajas o modificaciones, solo visualización.

La URL base es: appfacturacion.globant.com

### 🤖 IA

He creado el archivo OpenAPI 3.1 completo para tu API de facturación, incluyendo:

* Recursos:

  * EmpresasDelUsuario
  * Facturas
  * Certificados
* Endpoints GET solicitados
* CRUD completo para `invoices`
* Schemas reutilizables
* Base URL configurada
* Tags y operationIds


---
## 🔁 Turno 2

### 👤 Usuario

Podrías realizar las siguientes actualizaciones: 
1) Cambia la descripción del server a: Ambiente de producción. 
2) Agrega el error "El usuario no pertenece a esa compañía" a los endponits de facturación. Nota adicional: No agregues nada correspondiente al usuario, dado que este se obtiene del JWT y luego se hace la validación con el get de las empresas. 
3) Agrega el endpoint "assigned-invoices" con una lógica similar al de "invoices"

### 🤖 IA

He actualizado el archivo OpenAPI con los siguientes cambios:

* Descripción del server cambiada a:

  * `Ambiente de producción`
* Agregado el error `403 - El usuario no pertenece a esa compañía` en todos los endpoints de facturación
* No se agregó información del usuario en los requests, considerando que se obtiene desde el JWT
* Incorporado el nuevo recurso:

  * `/{empresa}/assigned-invoices`
  * `/{empresa}/assigned-invoices/{invoiceId}`
* CRUD completo para `assigned-invoices`, siguiendo la misma lógica que `invoices`

---
## 🔁 Turno 3

### 👤 Usuario

Corrige esto:
1) Las facturas asignadas solamente manten el metodo GET. El resto elimina ya que no es posible crear, actualizar o eliminar una factura asignada.
2) En vez de devolver 403 cuando el usuario no pertenece a la compañia, devuelve 400 dado que no es un unauthorized, sino que directamente ese usuario no pertenece a la companía (un tema funcional).

### 🤖 IA

He realizado las correcciones solicitadas:

* Eliminados los métodos:

  * `POST`
  * `PUT`
  * `PATCH`
  * `DELETE`

  del recurso `assigned-invoices`, dejando únicamente los métodos `GET`.

* Reemplazado el código de error:

  * `403` → `400`

  en todos los endpoints de facturación, manteniendo la descripción:

  * `El usuario no pertenece a esa compañía`