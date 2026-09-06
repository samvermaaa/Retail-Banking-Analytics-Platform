-- Two schemas, one per analytical track. This is the database-level
-- enforcement of the decision documented in DATA_AUDIT.md section 4.1:
-- churn_prediction.csv and the bank marketing files describe different
-- populations with no shared customer identifier, so they are never
-- joined at the row level. Putting them in separate schemas makes an
-- accidental cross-track join a two-part name away from obvious.

CREATE SCHEMA IF NOT EXISTS track_a;
CREATE SCHEMA IF NOT EXISTS track_b;
