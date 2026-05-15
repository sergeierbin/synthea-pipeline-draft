CREATE TABLE IF NOT EXISTS patients (
    id          TEXT PRIMARY KEY,
    birth_date  DATE,
    gender      TEXT,
    city        TEXT,
    state       TEXT,
    country     TEXT
);

CREATE TABLE IF NOT EXISTS conditions (
    id               TEXT PRIMARY KEY,
    patient_id       TEXT NOT NULL REFERENCES patients(id),
    code             TEXT,
    display          TEXT,
    onset_date       DATE,
    abatement_date   DATE,
    clinical_status  TEXT
);

CREATE TABLE IF NOT EXISTS medications (
    id           TEXT PRIMARY KEY,
    patient_id   TEXT NOT NULL REFERENCES patients(id),
    code         TEXT,
    display      TEXT,
    authored_on  DATE,
    status       TEXT
);

CREATE TABLE IF NOT EXISTS observations (
    id             TEXT PRIMARY KEY,
    patient_id     TEXT NOT NULL REFERENCES patients(id),
    code           TEXT,
    display        TEXT,
    value          NUMERIC,
    unit           TEXT,
    effective_date DATE
);

CREATE INDEX IF NOT EXISTS idx_conditions_patient_id  ON conditions(patient_id);
CREATE INDEX IF NOT EXISTS idx_conditions_code        ON conditions(code);

CREATE INDEX IF NOT EXISTS idx_medications_patient_id ON medications(patient_id);
CREATE INDEX IF NOT EXISTS idx_medications_code       ON medications(code);

CREATE INDEX IF NOT EXISTS idx_observations_patient_id ON observations(patient_id);
CREATE INDEX IF NOT EXISTS idx_observations_code       ON observations(code);
