CREATE TABLE IF NOT EXISTS sensor (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    location TEXT,
    value DOUBLE PRECISION,
    unit TEXT,
    status TEXT,
    timestamp TIMESTAMPTZ DEFAULT now()
);

SELECT create_hypertable('sensor', 'timestamp', if_not_exists => TRUE);
