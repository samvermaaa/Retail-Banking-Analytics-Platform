-- Track B analytical views and business questions, built on
-- track_b.marketing_observation (bank-additional-full.csv, primary).
-- bank_full is queried separately at the end, specifically for the
-- balance question that the primary dataset cannot answer, and is never
-- joined row-to-row with marketing_observation.

CREATE OR REPLACE VIEW track_b.track_b_campaign_summary AS
SELECT
    month,
    day_of_week,
    count(*) AS observation_count,
    round(avg(CASE WHEN y = 'yes' THEN 1.0 ELSE 0 END), 4) AS adoption_rate
FROM track_b.marketing_observation
GROUP BY 1, 2
ORDER BY observation_count DESC;

CREATE OR REPLACE VIEW track_b.track_b_adoption_summary AS
SELECT
    job, education, housing, loan, poutcome, previous_contact_flag,
    CASE WHEN y = 'yes' THEN 1 ELSE 0 END AS adopted
FROM track_b.marketing_observation;

-- Q1: overall product adoption rate
SELECT count(*) AS observations,
       round(avg(CASE WHEN y = 'yes' THEN 1.0 ELSE 0 END), 4) AS adoption_rate
FROM track_b.marketing_observation;

-- Q2: adoption by age band
SELECT
    CASE
        WHEN age < 25 THEN 'under 25'
        WHEN age BETWEEN 25 AND 34 THEN '25-34'
        WHEN age BETWEEN 35 AND 44 THEN '35-44'
        WHEN age BETWEEN 45 AND 54 THEN '45-54'
        WHEN age BETWEEN 55 AND 64 THEN '55-64'
        ELSE '65+'
    END AS age_band,
    count(*) AS observation_count,
    round(avg(CASE WHEN y = 'yes' THEN 1.0 ELSE 0 END), 4) AS adoption_rate
FROM track_b.marketing_observation
GROUP BY 1
ORDER BY 1;

-- Q3: adoption by job
SELECT job, count(*) AS observation_count,
       round(avg(CASE WHEN y = 'yes' THEN 1.0 ELSE 0 END), 4) AS adoption_rate
FROM track_b.marketing_observation
GROUP BY 1
ORDER BY adoption_rate DESC;

-- Q4: adoption by education
SELECT education, count(*) AS observation_count,
       round(avg(CASE WHEN y = 'yes' THEN 1.0 ELSE 0 END), 4) AS adoption_rate
FROM track_b.marketing_observation
GROUP BY 1
ORDER BY adoption_rate DESC;

-- Q5: adoption by housing loan status
SELECT housing, count(*) AS observation_count,
       round(avg(CASE WHEN y = 'yes' THEN 1.0 ELSE 0 END), 4) AS adoption_rate
FROM track_b.marketing_observation
GROUP BY 1
ORDER BY adoption_rate DESC;

-- Q6: adoption by previous campaign outcome
SELECT poutcome, count(*) AS observation_count,
       round(avg(CASE WHEN y = 'yes' THEN 1.0 ELSE 0 END), 4) AS adoption_rate
FROM track_b.marketing_observation
GROUP BY 1
ORDER BY adoption_rate DESC;

-- Q7: adoption by whether the client was contacted in a prior campaign
SELECT previous_contact_flag, count(*) AS observation_count,
       round(avg(CASE WHEN y = 'yes' THEN 1.0 ELSE 0 END), 4) AS adoption_rate
FROM track_b.marketing_observation
GROUP BY 1
ORDER BY 1;

-- Q8: groups with meaningful sample size (>= 200) and above-average adoption
WITH overall AS (
    SELECT avg(CASE WHEN y = 'yes' THEN 1.0 ELSE 0 END) AS overall_rate
    FROM track_b.marketing_observation
)
SELECT job, education, count(*) AS observation_count,
       round(avg(CASE WHEN y = 'yes' THEN 1.0 ELSE 0 END), 4) AS adoption_rate
FROM track_b.marketing_observation, overall
GROUP BY 1, 2, overall.overall_rate
HAVING count(*) >= 200 AND avg(CASE WHEN y = 'yes' THEN 1.0 ELSE 0 END) > max(overall.overall_rate)
ORDER BY adoption_rate DESC
LIMIT 10;

-- Secondary dataset: balance vs subscription (only answerable from bank-full.csv)
WITH quartiled AS (
    SELECT balance, y,
           ntile(4) OVER (ORDER BY balance) AS balance_quartile
    FROM track_b.marketing_observation_bank_full
)
SELECT
    balance_quartile,
    count(*) AS observation_count,
    round(min(balance), 2) AS min_balance,
    round(max(balance), 2) AS max_balance,
    round(avg(CASE WHEN y = 'yes' THEN 1.0 ELSE 0 END), 4) AS adoption_rate
FROM quartiled
GROUP BY 1
ORDER BY 1;
