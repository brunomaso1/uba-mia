CREATE TABLE IF NOT EXISTS users (
    id            UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    keycloak_sub  TEXT          UNIQUE NOT NULL,
    display_name  TEXT          NOT NULL,
    email         TEXT          UNIQUE NOT NULL,
    created_at    TIMESTAMPTZ   DEFAULT NOW()
);

COMMENT ON TABLE  users                IS 'Registered application users, synced from Keycloak on first login.';
COMMENT ON COLUMN users.id             IS 'Internal UUID primary key.';
COMMENT ON COLUMN users.keycloak_sub   IS 'Keycloak subject claim (sub) from JWT — used to identify the user.';
COMMENT ON COLUMN users.display_name   IS 'Human-readable name shown in the UI.';
COMMENT ON COLUMN users.email          IS 'User email address, sourced from Keycloak.';
COMMENT ON COLUMN users.created_at     IS 'Timestamp of first login (user creation).';

CREATE TABLE IF NOT EXISTS groups (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT        NOT NULL,
    created_by  UUID        NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE  groups              IS 'Expense groups that users can create and share.';
COMMENT ON COLUMN groups.id           IS 'Internal UUID primary key.';
COMMENT ON COLUMN groups.name         IS 'Display name of the group.';
COMMENT ON COLUMN groups.created_by   IS 'User who created the group.';
COMMENT ON COLUMN groups.created_at   IS 'Timestamp of group creation.';

CREATE TABLE IF NOT EXISTS group_member (
    user_id   UUID        NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
    group_id  UUID        NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, group_id)
);

COMMENT ON TABLE  group_member           IS 'Membership relationship between users and groups.';
COMMENT ON COLUMN group_member.user_id   IS 'Member user.';
COMMENT ON COLUMN group_member.group_id  IS 'Group the user belongs to.';
COMMENT ON COLUMN group_member.joined_at IS 'Timestamp when the user joined the group.';

CREATE TABLE IF NOT EXISTS categories (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT        UNIQUE NOT NULL,
    description TEXT,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE  categories               IS 'Expense categories for classifying expenses.';
COMMENT ON COLUMN categories.id            IS 'Internal UUID primary key.';
COMMENT ON COLUMN categories.name          IS 'Unique category name.';
COMMENT ON COLUMN categories.description   IS 'Optional description of the category.';
COMMENT ON COLUMN categories.is_active     IS 'Whether the category is available for new expenses.';
COMMENT ON COLUMN categories.created_at    IS 'Timestamp of category creation.';

CREATE TABLE IF NOT EXISTS expenses (
    id          UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id    UUID          NOT NULL REFERENCES groups(id)     ON DELETE CASCADE,
    paid_by     UUID          NOT NULL REFERENCES users(id)      ON DELETE RESTRICT,
    category_id UUID          NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    amount      NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    description TEXT,
    date        DATE          NOT NULL,
    created_at  TIMESTAMPTZ   DEFAULT NOW()
);

COMMENT ON TABLE  expenses               IS 'Shared expenses recorded within a group.';
COMMENT ON COLUMN expenses.id            IS 'Internal UUID primary key.';
COMMENT ON COLUMN expenses.group_id      IS 'Group this expense belongs to.';
COMMENT ON COLUMN expenses.paid_by       IS 'User who paid for the expense.';
COMMENT ON COLUMN expenses.category_id   IS 'Category classifying the expense.';
COMMENT ON COLUMN expenses.amount        IS 'Amount paid, up to 12 digits with 2 decimal places.';
COMMENT ON COLUMN expenses.description   IS 'Optional description or note for the expense.';
COMMENT ON COLUMN expenses.date          IS 'Date the expense occurred.';
COMMENT ON COLUMN expenses.created_at    IS 'Timestamp when the expense was recorded.';

CREATE INDEX IF NOT EXISTS idx_expenses_group_id       ON expenses(group_id);
CREATE INDEX IF NOT EXISTS idx_expenses_paid_by        ON expenses(paid_by);
CREATE INDEX IF NOT EXISTS idx_expenses_category_id    ON expenses(category_id);
CREATE INDEX IF NOT EXISTS idx_group_member_user_id    ON group_member(user_id);
CREATE INDEX IF NOT EXISTS idx_group_member_group_id   ON group_member(group_id);
