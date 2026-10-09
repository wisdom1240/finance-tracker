CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    first_name    VARCHAR(50)  NOT NULL,
    last_name     VARCHAR(50)  NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT         NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE categories (
    id    SERIAL PRIMARY KEY,
    name  VARCHAR(50) NOT NULL,
    type  VARCHAR(7)  NOT NULL CHECK (type IN ('INCOME', 'EXPENSE')),
    UNIQUE (name, type)
);

CREATE TABLE transactions (
    id               SERIAL PRIMARY KEY,
    user_id          INTEGER       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id      INTEGER       NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    type             VARCHAR(7)    NOT NULL CHECK (type IN ('INCOME', 'EXPENSE')),
    amount           NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    description      VARCHAR(255),
    transaction_date DATE          NOT NULL,
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_transactions_user_date ON transactions (user_id, transaction_date DESC);

CREATE TABLE budgets (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER       NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    amount      NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    month       SMALLINT      NOT NULL CHECK (month BETWEEN 1 AND 12),
    year        SMALLINT      NOT NULL CHECK (year BETWEEN 2000 AND 2100),
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, category_id, month, year)
);

CREATE TABLE savings_goals (
    id             SERIAL PRIMARY KEY,
    user_id        INTEGER       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name           VARCHAR(100)  NOT NULL,
    target_amount  NUMERIC(12,2) NOT NULL CHECK (target_amount > 0),
    current_amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (current_amount >= 0),
    target_date    DATE,
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

INSERT INTO categories (name, type) VALUES
    ('Food',         'EXPENSE'),
    ('Transport',    'EXPENSE'),
    ('Rent',         'EXPENSE'),
    ('Education',    'EXPENSE'),
    ('Data',         'EXPENSE'),
    ('Electricity',  'EXPENSE'),
    ('Entertainment','EXPENSE'),
    ('Shopping',     'EXPENSE'),
    ('Medical',      'EXPENSE'),
    ('Other',        'EXPENSE'),
    ('Salary',       'INCOME'),
    ('Business',     'INCOME'),
    ('Freelance',    'INCOME'),
    ('Gift',         'INCOME'),
    ('Investment',   'INCOME'),
    ('Other',        'INCOME');
