-- Track A analytical views and business questions.
-- All joins here are within track_a only (same customer_id across four
-- tables that all originate from churn_prediction.csv). This does not
-- cross into track_b.

CREATE OR REPLACE VIEW track_a.track_a_customer_profile AS
SELECT
    c.customer_id,
    c.age,
    c.age_under_18_flag,
    c.gender,
    c.dependents,
    c.occupation,
    c.customer_nw_category,
    b.current_balance,
    b.previous_month_end_balance,
    b.average_monthly_balance_prevq,
    a.current_month_credit,
    a.current_month_debit,
    a.last_transaction,
    -- 2019-12-31 is the latest last_transaction date observed anywhere in the
    -- data, used here as the reference point for recency. Not an assumed
    -- "today", confirmed by checking max(last_transaction) directly.
    date_diff('day', a.last_transaction, DATE '2019-12-31') AS days_since_last_transaction,
    ch.churn
FROM track_a.dim_customer c
JOIN track_a.fact_customer_balance b USING (customer_id)
JOIN track_a.fact_customer_activity a USING (customer_id)
JOIN track_a.fact_customer_churn ch USING (customer_id);

CREATE OR REPLACE VIEW track_a.track_a_churn_summary AS
SELECT
    CASE
        WHEN age < 18 THEN 'under 18'
        WHEN age BETWEEN 18 AND 25 THEN '18-25'
        WHEN age BETWEEN 26 AND 35 THEN '26-35'
        WHEN age BETWEEN 36 AND 45 THEN '36-45'
        WHEN age BETWEEN 46 AND 55 THEN '46-55'
        WHEN age BETWEEN 56 AND 65 THEN '56-65'
        ELSE '66+'
    END AS age_group,
    customer_nw_category,
    count(*) AS customer_count,
    round(avg(churn), 4) AS churn_rate,
    round(avg(current_balance), 2) AS avg_current_balance,
    round(median(current_balance), 2) AS median_current_balance
FROM track_a.track_a_customer_profile
GROUP BY 1, 2
ORDER BY 1, 2;

-- Q1: overall churn rate
SELECT count(*) AS customers, round(avg(churn), 4) AS churn_rate
FROM track_a.track_a_customer_profile;

-- Q2: churn by age group
SELECT
    CASE
        WHEN age < 18 THEN 'under 18'
        WHEN age BETWEEN 18 AND 25 THEN '18-25'
        WHEN age BETWEEN 26 AND 35 THEN '26-35'
        WHEN age BETWEEN 36 AND 45 THEN '36-45'
        WHEN age BETWEEN 46 AND 55 THEN '46-55'
        WHEN age BETWEEN 56 AND 65 THEN '56-65'
        ELSE '66+'
    END AS age_group,
    count(*) AS customer_count,
    round(avg(churn), 4) AS churn_rate
FROM track_a.track_a_customer_profile
GROUP BY 1
ORDER BY 1;

-- Q3: churn by customer net worth category
SELECT customer_nw_category, count(*) AS customer_count, round(avg(churn), 4) AS churn_rate
FROM track_a.track_a_customer_profile
GROUP BY 1
ORDER BY 1;

-- Q4: churn by current balance quartile
WITH quartiled AS (
    SELECT current_balance, churn,
           ntile(4) OVER (ORDER BY current_balance) AS balance_quartile
    FROM track_a.track_a_customer_profile
)
SELECT
    balance_quartile,
    count(*) AS customer_count,
    round(min(current_balance), 2) AS min_balance,
    round(max(current_balance), 2) AS max_balance,
    round(avg(churn), 4) AS churn_rate
FROM quartiled
GROUP BY 1
ORDER BY 1;

-- Q5: churn by transaction recency band
SELECT
    CASE
        WHEN days_since_last_transaction IS NULL THEN 'no valid last_transaction date'
        WHEN days_since_last_transaction <= 30 THEN '0-30 days'
        WHEN days_since_last_transaction <= 90 THEN '31-90 days'
        WHEN days_since_last_transaction <= 180 THEN '91-180 days'
        ELSE '180+ days'
    END AS recency_band,
    count(*) AS customer_count,
    round(avg(churn), 4) AS churn_rate
FROM track_a.track_a_customer_profile
GROUP BY 1
ORDER BY 2 DESC;

-- Q6: which groups have the highest average balances (occupation x nw category, min 100 customers)
SELECT occupation, customer_nw_category, count(*) AS customer_count,
       round(avg(current_balance), 2) AS avg_balance
FROM track_a.track_a_customer_profile
GROUP BY 1, 2
HAVING count(*) >= 100
ORDER BY avg_balance DESC
LIMIT 10;

-- Q7: groups combining high balance with high churn (min 100 customers)
SELECT occupation, customer_nw_category, count(*) AS customer_count,
       round(avg(current_balance), 2) AS avg_balance,
       round(avg(churn), 4) AS churn_rate
FROM track_a.track_a_customer_profile
GROUP BY 1, 2
HAVING count(*) >= 100 AND avg(current_balance) > (SELECT avg(current_balance) FROM track_a.track_a_customer_profile)
ORDER BY churn_rate DESC
LIMIT 10;
