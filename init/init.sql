CREATE TABLE IF NOT EXISTS changes (
    id SERIAL PRIMARY KEY,
    author TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    content TEXT NOT NULL
);

