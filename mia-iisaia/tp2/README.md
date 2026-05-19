<div align="center">

# TP2 - OpenAPI y ChatGPT Canvas

| Atributo         | Valor                                                                |
| ---------------- | -------------------------------------------------------------------- |
| Materia          | Introducción a la ingeniería de software asistida por IA             |
| Trabajo práctico | TP2 - OpenAPI y ChatGPT Canvas                                       |
| Descripción      | Generación de una especificación de OpenAPI mediante ChatGPT Canvas. |

</div>

## Invoices API

Invoices API es una especificación OpenAPI 3.1 para un sistema de facturación con foco en operaciones sobre facturas por empresa. La API utiliza como base `https://appfacturacion.globant.com` (ambiente de producción) y contempla validación funcional de pertenencia del usuario a la compañía (obtenido vía JWT), devolviendo `400` cuando no corresponde operar sobre la empresa indicada.

### Características principales:

- Especificación en OpenAPI 3.1 con server productivo configurado.
- Recurso principal de facturas por empresa: `/{empresa}/invoices`.
- CRUD completo de facturas:
  - `GET /{empresa}/invoices`
  - `POST /{empresa}/invoices`
  - `GET /{empresa}/invoices/{invoiceId}`
  - `PUT /{empresa}/invoices/{invoiceId}`
  - `PATCH /{empresa}/invoices/{invoiceId}`
  - `DELETE /{empresa}/invoices/{invoiceId}`
- Recurso de facturas asignadas solo de lectura:
  - `GET /{empresa}/assigned-invoices`
  - `GET /{empresa}/assigned-invoices/{invoiceId}`
- Recursos de consulta (sin altas, bajas ni modificaciones):
  - `GET /user-companies`
  - `GET /certificates`
- Manejo de respuestas funcionales por endpoint, incluyendo:
  - `200`, `201` y `204` para operaciones exitosas
  - `400` cuando el usuario no pertenece a la compañía
  - `404` cuando la factura solicitada no existe
- Modelos tipados para `Invoice`, `InvoiceCreateRequest`, `InvoiceUpdateRequest`, `InvoicePatchRequest`, `UserCompany` y `Certificate`.


## Ejemplo de uso:

```yaml
openapi: 3.1.0
info:
  title: API de Facturación
  version: 1.0.0
  description: API para la gestión de facturas, empresas asociadas al usuario y certificados.

servers:
  - url: https://appfacturacion.globant.com
    description: Ambiente de producción

tags:
  - name: Invoices
    description: Operaciones sobre facturas
  - name: User Companies
    description: Empresas asociadas al usuario autenticado
  - name: Certificates
    description: Consulta de certificados

paths:
  /{empresa}/assigned-invoices:
    get:
      tags:
        - Invoices
      summary: Obtener facturas asignadas de una empresa
      operationId: getAssignedInvoices
      parameters:
        - name: empresa
          in: path
          required: true
          description: Identificador de la empresa
          schema:
            type: string
      responses:
        "200":
          description: Lista de facturas asignadas obtenida correctamente
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Invoice"
        "400":
          description: El usuario no pertenece a esa compañía

  /{empresa}/assigned-invoices/{invoiceId}:
    get:
      tags:
        - Invoices
      summary: Obtener una factura asignada por ID
      operationId: getAssignedInvoiceById
      parameters:
        - name: empresa
          in: path
          required: true
          schema:
            type: string
        - name: invoiceId
          in: path
          required: true
          schema:
            type: integer
      responses:
        "200":
          description: Factura asignada encontrada
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Invoice"
        "400":
          description: El usuario no pertenece a esa compañía
        "404":
          description: Factura no encontrada

  /{empresa}/invoices:
    get:
      tags:
        - Invoices
      summary: Obtener facturas de una empresa
      operationId: getInvoices
      parameters:
        - name: empresa
          in: path
          required: true
          description: Identificador de la empresa
          schema:
            type: string
      responses:
        "200":
          description: Lista de facturas obtenida correctamente
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Invoice"
        "400":
          description: El usuario no pertenece a esa compañía

    post:
      tags:
        - Invoices
      summary: Crear una nueva factura
      operationId: createInvoice
      parameters:
        - name: empresa
          in: path
          required: true
          description: Identificador de la empresa
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/InvoiceCreateRequest"
      responses:
        "201":
          description: Factura creada correctamente
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Invoice"
        "400":
          description: El usuario no pertenece a esa compañía

  /{empresa}/invoices/{invoiceId}:
    get:
      tags:
        - Invoices
      summary: Obtener una factura por ID
      operationId: getInvoiceById
      parameters:
        - name: empresa
          in: path
          required: true
          schema:
            type: string
        - name: invoiceId
          in: path
          required: true
          schema:
            type: integer
      responses:
        "200":
          description: Factura encontrada
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Invoice"
        "400":
          description: El usuario no pertenece a esa compañía
        "404":
          description: Factura no encontrada

    put:
      tags:
        - Invoices
      summary: Actualizar completamente una factura
      operationId: updateInvoice
      parameters:
        - name: empresa
          in: path
          required: true
          schema:
            type: string
        - name: invoiceId
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/InvoiceUpdateRequest"
      responses:
        "200":
          description: Factura actualizada correctamente
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Invoice"
        "400":
          description: El usuario no pertenece a esa compañía
        "404":
          description: Factura no encontrada

    patch:
      tags:
        - Invoices
      summary: Actualizar parcialmente una factura
      operationId: patchInvoice
      parameters:
        - name: empresa
          in: path
          required: true
          schema:
            type: string
        - name: invoiceId
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/InvoicePatchRequest"
      responses:
        "200":
          description: Factura actualizada parcialmente
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Invoice"
        "400":
          description: El usuario no pertenece a esa compañía
        "404":
          description: Factura no encontrada

    delete:
      tags:
        - Invoices
      summary: Eliminar una factura
      operationId: deleteInvoice
      parameters:
        - name: empresa
          in: path
          required: true
          schema:
            type: string
        - name: invoiceId
          in: path
          required: true
          schema:
            type: integer
      responses:
        "204":
          description: Factura eliminada correctamente
        "400":
          description: El usuario no pertenece a esa compañía
        "404":
          description: Factura no encontrada

  /user-companies:
    get:
      tags:
        - User Companies
      summary: Obtener empresas asociadas al usuario
      operationId: getUserCompanies
      responses:
        "200":
          description: Lista de empresas del usuario
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/UserCompany"

  /certificates:
    get:
      tags:
        - Certificates
      summary: Obtener certificados
      operationId: getCertificates
      responses:
        "200":
          description: Lista de certificados
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Certificate"

components:
  schemas:
    UserCompany:
      type: object
      required:
        - id
        - usuario
        - empresa
      properties:
        id:
          type: integer
          example: 1
        usuario:
          type: string
          example: bmasoller
        empresa:
          type: string
          example: globant-uy

    Invoice:
      type: object
      required:
        - id
        - monto
        - fecha
        - numero
      properties:
        id:
          type: integer
          example: 1001
        monto:
          type: number
          format: double
          example: 1540.75
        fecha:
          type: string
          format: date
          example: 2026-05-19
        numero:
          type: string
          example: FAC-2026-0001

    InvoiceCreateRequest:
      type: object
      required:
        - monto
        - fecha
        - numero
      properties:
        monto:
          type: number
          format: double
          example: 1540.75
        fecha:
          type: string
          format: date
          example: 2026-05-19
        numero:
          type: string
          example: FAC-2026-0001

    InvoiceUpdateRequest:
      type: object
      required:
        - monto
        - fecha
        - numero
      properties:
        monto:
          type: number
          format: double
        fecha:
          type: string
          format: date
        numero:
          type: string

    InvoicePatchRequest:
      type: object
      properties:
        monto:
          type: number
          format: double
        fecha:
          type: string
          format: date
        numero:
          type: string

    Certificate:
      type: object
      required:
        - id
        - proveedor
        - fechaVencimiento
      properties:
        id:
          type: integer
          example: 10
        proveedor:
          type: string
          example: Digicert
        fechaVencimiento:
          type: string
          format: date
          example: 2027-01-01

```