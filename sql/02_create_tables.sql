-- Track A: churn_prediction.csv, one row per customer, split into a
-- customer dimension and three fact areas (attributes, balance, activity,
-- churn outcome kept apart rather than as one wide table).

CREATE TABLE track_a.dim_customer (
    customer_id        BIGINT PRIMARY KEY,
    vintage             INTEGER,
    age                 INTEGER,
    age_under_18_flag   BOOLEAN,
    gender              VARCHAR,
    dependents          DOUBLE,
    occupation          VARCHAR,
    city                DOUBLE,
    customer_nw_category INTEGER,
    branch_code         INTEGER
);

CREATE TABLE track_a.fact_customer_balance (
    customer_id                     BIGINT PRIMARY KEY,
    current_balance                 DOUBLE,
    previous_month_end_balance      DOUBLE,
    average_monthly_balance_prevq   DOUBLE,
    average_monthly_balance_prevq2  DOUBLE,
    current_month_balance           DOUBLE,
    previous_month_balance          DOUBLE
);

CREATE TABLE track_a.fact_customer_activity (
    customer_id            BIGINT PRIMARY KEY,
    current_month_credit   DOUBLE,
    previous_month_credit  DOUBLE,
    current_month_debit    DOUBLE,
    previous_month_debit   DOUBLE,
    last_transaction       DATE
);

CREATE TABLE track_a.fact_customer_churn (
    customer_id  BIGINT PRIMARY KEY,
    churn        INTEGER
);

-- Track B: bank-additional-full.csv (primary) and bank-full.csv
-- (secondary). Neither file carries a persistent customer identity, so
-- each row is a campaign contact observation, not a customer. No PRIMARY
-- KEY column exists in the source; observation_id is a surrogate row
-- number added at load time.

CREATE TABLE track_b.marketing_observation (
    observation_id                BIGINT PRIMARY KEY,
    age                           INTEGER,
    job                           VARCHAR,
    marital                       VARCHAR,
    education                     VARCHAR,
    default_credit                VARCHAR,
    housing                       VARCHAR,
    loan                          VARCHAR,
    contact                       VARCHAR,
    month                         VARCHAR,
    day_of_week                   VARCHAR,
    duration                      INTEGER,   -- LEAKAGE_FOR_PREDICTION, see docs/DATA_LEAKAGE.md
    campaign                      INTEGER,
    previous_contact_flag         BOOLEAN,
    days_since_previous_contact   DOUBLE,
    previous                      INTEGER,
    poutcome                      VARCHAR,
    emp_var_rate                  DOUBLE,
    cons_price_idx                DOUBLE,
    cons_conf_idx                 DOUBLE,
    euribor3m                     DOUBLE,
    nr_employed                   DOUBLE,
    y                             VARCHAR
);

CREATE TABLE track_b.marketing_observation_bank_full (
    observation_id                BIGINT PRIMARY KEY,
    age                           INTEGER,
    job                           VARCHAR,
    marital                       VARCHAR,
    education                     VARCHAR,
    default_credit                VARCHAR,
    balance                       INTEGER,   -- present here, not in the additional-full extract
    housing                       VARCHAR,
    loan                          VARCHAR,
    contact                       VARCHAR,
    day                           INTEGER,
    month                         VARCHAR,
    duration                      INTEGER,   -- LEAKAGE_FOR_PREDICTION, see docs/DATA_LEAKAGE.md
    campaign                      INTEGER,
    previous_contact_flag         BOOLEAN,
    days_since_previous_contact   DOUBLE,
    previous                      INTEGER,
    poutcome                      VARCHAR,
    y                             VARCHAR
);
