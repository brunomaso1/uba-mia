CREATE TABLE IF NOT EXISTS app_user (
    id            UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    keycloak_sub  TEXT          UNIQUE NOT NULL,
    display_name  TEXT          NOT NULL,
    email         TEXT          UNIQUE NOT NULL,
    created_at    TIMESTAMPTZ   DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS "group" (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT        NOT NULL,
    created_by  UUID        NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS group_member (
    user_id   UUID        NOT NULL REFERENCES app_user(id)  ON DELETE CASCADE,
    group_id  UUID        NOT NULL REFERENCES "group"(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, group_id)
);

CREATE TABLE IF NOT EXISTS category (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT        UNIQUE NOT NULL,
    description TEXT,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS expense (
    id          UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id    UUID          NOT NULL REFERENCES "group"(id) ON DELETE CASCADE,
    paid_by     UUID          NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
    category_id UUID          NOT NULL REFERENCES category(id) ON DELETE RESTRICT,
    amount      NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    description TEXT,
    date        DATE          NOT NULL,
    created_at  TIMESTAMPTZ   DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_expense_group_id       ON expense(group_id);
CREATE INDEX IF NOT EXISTS idx_expense_paid_by        ON expense(paid_by);
CREATE INDEX IF NOT EXISTS idx_expense_category_id    ON expense(category_id);
CREATE INDEX IF NOT EXISTS idx_group_member_user_id   ON group_member(user_id);
CREATE INDEX IF NOT EXISTS idx_group_member_group_id  ON group_member(group_id);
