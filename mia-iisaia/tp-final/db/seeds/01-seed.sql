-- Seeds use fake keycloak_sub values for local testing.
-- Real users are auto-created by the backend on first login (sub from JWT).
-- Apply manually: docker compose exec db psql -U <db_user> -d <db_name> -f /seeds/01-seed.sql

INSERT INTO category (name, description) VALUES
    ('Gastos genéricos', 'Categoría por defecto para expenses sin clasificar')
ON CONFLICT DO NOTHING;

INSERT INTO app_user (keycloak_sub, display_name, email) VALUES
    ('test-sub-alice', 'Alice Test', 'alice@example.com'),
    ('test-sub-bob',   'Bob Test',   'bob@example.com')
ON CONFLICT DO NOTHING;

INSERT INTO "group" (name, created_by) VALUES
    ('Familia', (SELECT id FROM app_user WHERE keycloak_sub = 'test-sub-alice'))
ON CONFLICT DO NOTHING;

INSERT INTO group_member (user_id, group_id)
SELECT u.id, g.id
FROM app_user u, "group" g
WHERE u.keycloak_sub IN ('test-sub-alice', 'test-sub-bob')
  AND g.name = 'Familia'
ON CONFLICT DO NOTHING;
