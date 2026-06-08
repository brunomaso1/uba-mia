# Diseño: Aplicación de Gestión de Gastos

**Fecha:** 2026-06-08  
**Stack:** Angular 22 · FastAPI 0.136.3 · Keycloak 26.6.0 · PostgreSQL 19  
**Orquestación:** Docker Compose (monorepo)

---

## 1. Objetivo

Aplicación multi-usuario para registrar gastos compartidos en grupos. Los usuarios se autentican via Keycloak, pertenecen a grupos, y registran gastos indicando quién pagó.

Alcance **excluido**: lógica de splits, liquidaciones (settlements), cálculo de deudas.

---

## 2. Estructura del repositorio

```
tp-final/
├── frontend/          # Angular 22 — SPA
├── backend/           # FastAPI 0.136.3 — API REST
├── keycloak/          # Keycloak 26.6.0 — realm config, client config
├── db/                # PostgreSQL 19 — init scripts, seeds, migraciones SQL
├── infra/             # docker-compose.yml, .env.example
└── docs/              # Documentación y specs
```

---

## 3. Componentes y puertos

| Componente | Tecnología         | Puerto local | Responsabilidad                              |
|------------|--------------------|--------------|----------------------------------------------|
| frontend   | Angular 22         | 4200         | SPA, consume API REST, delega auth a Keycloak |
| backend    | FastAPI 0.136.3    | 8000         | API REST, lógica de negocio, valida JWT       |
| keycloak   | Keycloak 26.6.0    | 8080         | Emisión de tokens JWT, gestión de usuarios    |
| db         | PostgreSQL 19      | 5432         | Persistencia                                  |

---

## 4. Flujo de autenticación

```
Usuario → Angular → Keycloak (login page) → JWT (access token)
Angular → FastAPI  (Authorization: Bearer <token>)
FastAPI → valida firma JWT via JWKS endpoint de Keycloak → responde datos
```

- El backend **no** hace roundtrips a Keycloak por request; valida la firma localmente con la clave pública (JWKS).
- El `sub` (subject) del JWT es el identificador único del usuario en la base de datos.
- Keycloak gestiona contraseñas, sesiones y refresh tokens. El backend solo verifica.

---

## 5. Modelo de datos

```
User
  id              UUID  PK
  keycloak_sub    TEXT  UNIQUE NOT NULL   -- sub del JWT
  display_name    TEXT  NOT NULL
  email           TEXT  UNIQUE NOT NULL
  created_at      TIMESTAMPTZ

Group
  id              UUID  PK
  name            TEXT  NOT NULL
  created_by      UUID  FK → User.id
  created_at      TIMESTAMPTZ

GroupMember
  user_id         UUID  FK → User.id
  group_id        UUID  FK → Group.id
  joined_at       TIMESTAMPTZ
  PRIMARY KEY (user_id, group_id)

Expense
  id              UUID  PK
  group_id        UUID  FK → Group.id  NOT NULL
  paid_by         UUID  FK → User.id   NOT NULL
  amount          NUMERIC(12,2)        NOT NULL
  description     TEXT
  date            DATE                 NOT NULL
  created_at      TIMESTAMPTZ
```

---

## 6. API REST (backend)

Todos los endpoints requieren `Authorization: Bearer <token>`.

### Usuarios
| Método | Path         | Descripción                        |
|--------|--------------|------------------------------------|
| GET    | /users/me    | Perfil del usuario autenticado     |

### Grupos
| Método | Path                      | Descripción                     |
|--------|---------------------------|---------------------------------|
| GET    | /groups                   | Grupos del usuario autenticado  |
| POST   | /groups                   | Crear grupo                     |
| GET    | /groups/{id}              | Detalle del grupo               |
| POST   | /groups/{id}/members      | Agregar miembro al grupo        |
| DELETE | /groups/{id}/members/{uid}| Eliminar miembro del grupo      |

### Gastos
| Método | Path                       | Descripción                     |
|--------|----------------------------|---------------------------------|
| GET    | /groups/{id}/expenses      | Gastos de un grupo              |
| POST   | /groups/{id}/expenses      | Registrar gasto en un grupo     |
| GET    | /expenses/{id}             | Detalle de un gasto             |
| PUT    | /expenses/{id}             | Editar gasto                    |
| DELETE | /expenses/{id}             | Eliminar gasto                  |

---

## 7. Estructura interna del backend

```
backend/
├── app/
│   ├── main.py              # Entrypoint, registro de routers, CORS
│   ├── core/
│   │   ├── config.py        # Settings via pydantic-settings
│   │   └── auth.py          # Validación JWT (JWKS, extracción de sub)
│   ├── db/
│   │   ├── session.py       # Engine SQLAlchemy + SessionLocal
│   │   └── models.py        # ORM models (User, Group, GroupMember, Expense)
│   ├── routers/
│   │   ├── users.py
│   │   ├── groups.py
│   │   └── expenses.py
│   └── schemas/             # Pydantic v2 schemas (request/response)
├── alembic/                 # Migraciones de base de datos
├── requirements.txt
└── Dockerfile
```

---

## 8. Estructura interna del frontend

```
frontend/src/app/
├── core/
│   ├── auth/                # Keycloak integration (keycloak-angular)
│   ├── guards/              # AuthGuard para rutas protegidas
│   └── interceptors/        # HTTP interceptor — agrega JWT al header
├── features/
│   ├── groups/              # Módulo grupos (lista, detalle, miembros)
│   └── expenses/            # Módulo gastos (lista, formulario)
└── shared/                  # Componentes y pipes reutilizables
```

---

## 9. Estructura de Keycloak

```
keycloak/
├── realm-export.json        # Exportación del realm con cliente configurado
└── Dockerfile               # Keycloak con realm importado al arranque
```

- Realm: `expense-app`
- Client: `expense-frontend` (public client, PKCE)
- Redirect URI configurada para `http://localhost:4200/*`

---

## 10. Estructura de db/

```
db/
├── init/
│   └── 01-init.sql          # Schema inicial (tablas, índices)
└── seeds/
    └── 01-seed.sql          # Datos de prueba (opcional)
```

Las migraciones evolutivas se manejan con Alembic desde el backend.

---

## 11. Variables de entorno

Definidas en `infra/.env.example`:

```env
# PostgreSQL
POSTGRES_DB=expense_db
POSTGRES_USER=expense_user
POSTGRES_PASSWORD=changeme
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Keycloak
KEYCLOAK_URL=http://keycloak:8080
KEYCLOAK_REALM=expense-app
KEYCLOAK_CLIENT_ID=expense-frontend

# Backend
BACKEND_CORS_ORIGINS=http://localhost:4200
```

---

## 12. Comandos de desarrollo

```bash
# Levantar todo el stack
docker compose -f infra/docker-compose.yml up

# Solo infraestructura (db + keycloak) mientras se desarrolla backend/frontend localmente
docker compose -f infra/docker-compose.yml up db keycloak

# Correr migraciones
docker compose -f infra/docker-compose.yml exec backend alembic upgrade head

# Frontend en modo dev (hot reload)
cd frontend && ng serve

# Backend en modo dev (hot reload)
cd backend && uvicorn app.main:app --reload
```
