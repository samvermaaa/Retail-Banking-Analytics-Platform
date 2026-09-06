-- Loads the cleaned CSVs produced by src/data/clean.py. Run after
-- 01_create_schema.sql and 02_create_tables.sql, from the project root
-- (paths below are relative to data/processed/).

-- read_csv_auto's type sniffer infers a column as BOOLEAN when the only
-- values it sees are "yes"/"no", which is exactly what happens to the
-- target column y in both marketing files. It is forced to VARCHAR here
-- so "yes"/"no" are preserved as text rather than silently becoming
-- true/false.

INSERT INTO track_a.dim_customer
SELECT customer_id, vintage, age, age_under_18_flag, gender, dependents,
       occupation, city, customer_nw_category, branch_code
FROM read_csv_auto('data/processed/churn_clean.csv');

INSERT INTO track_a.fact_customer_balance
SELECT customer_id, current_balance, previous_month_end_balance,
       average_monthly_balance_prevQ AS average_monthly_balance_prevq,
       average_monthly_balance_prevQ2 AS average_monthly_balance_prevq2,
       current_month_balance, previous_month_balance
FROM read_csv_auto('data/processed/churn_clean.csv');

INSERT INTO track_a.fact_customer_activity
SELECT customer_id, current_month_credit, previous_month_credit,
       current_month_debit, previous_month_debit,
       last_transaction::DATE
FROM read_csv_auto('data/processed/churn_clean.csv');

INSERT INTO track_a.fact_customer_churn
SELECT customer_id, churn
FROM read_csv_auto('data/processed/churn_clean.csv');

INSERT INTO track_b.marketing_observation
SELECT ROW_NUMBER() OVER () AS observation_id,
       age, job, marital, education,
       "default" AS default_credit,
       housing, loan, contact, month, day_of_week, duration, campaign,
       previous_contact_flag, days_since_previous_contact, previous,
       poutcome,
       "emp.var.rate" AS emp_var_rate,
       "cons.price.idx" AS cons_price_idx,
       "cons.conf.idx" AS cons_conf_idx,
       euribor3m,
       "nr.employed" AS nr_employed,
       y
FROM read_csv('data/processed/bank_additional_clean.csv', types={'y': 'VARCHAR'});

INSERT INTO track_b.marketing_observation_bank_full
SELECT ROW_NUMBER() OVER () AS observation_id,
       age, job, marital, education,
       "default" AS default_credit,
       balance, housing, loan, contact, day, month, duration, campaign,
       previous_contact_flag, days_since_previous_contact, previous,
       poutcome, y
FROM read_csv('data/processed/bank_full_clean.csv', types={'y': 'VARCHAR'});
