CREATE TABLE case_record (
    id SERIAL PRIMARY KEY,
    citizen_id TEXT NOT NULL,
    status TEXT NOT NULL,
    payload JSONB NOT NULL
);
