# Data Dictionary

Descriptions for the bank marketing variables are taken from the documentation shipped with the dataset (`bank-names.txt`, `bank-additional-names.txt`). Descriptions for the churn dataset are marked as inferred, since no formal data dictionary was included with that file, only column names and observed values.

## Bank Marketing (bank-full.csv / bank-additional-full.csv)

"Present in" shows which file has the column. A blank means the column is not in that file.

| Field | Description | Type | Present in | Valid Values | Analytical Use |
|---|---|---|---|---|---|
| age | Client age | Numeric | Both | 17 to 98 | Demographic segmentation |
| job | Type of job | Categorical | Both | 12 categories, e.g. admin., blue-collar, management, technician, student, retired | Segmentation, product targeting |
| marital | Marital status | Categorical | Both | married, single, divorced (divorced includes widowed) | Segmentation |
| education | Education level | Categorical | Both | bank-full: unknown, primary, secondary, tertiary. bank-additional-full: 8 finer levels including basic.4y/6y/9y, high.school, illiterate, professional.course, university.degree | Segmentation |
| default | Has credit in default | Categorical (yes/no, +unknown in additional) | Both | Credit risk indicator |
| balance | Average yearly balance, in euros | Numeric | bank-full only | -8,019 to 102,127 | Financial value, wealth indicator |
| housing | Has a housing loan | Categorical (yes/no) | Both | Product ownership |
| loan | Has a personal loan | Categorical (yes/no) | Both | Product ownership |
| contact | Contact communication type | Categorical | Both | cellular, telephone (bank-full also has unknown) | Channel analysis |
| day | Last contact day of month | Numeric | bank-full only | 1 to 31 | Campaign timing |
| day_of_week | Last contact day of week | Categorical | bank-additional-full only | mon to fri | Campaign timing |
| month | Last contact month | Categorical | Both | jan to dec | Campaign timing, seasonality |
| duration | Last contact duration, in seconds | Numeric | Both | 0 to 4,918 | Excluded from realistic prediction, see DATA_LEAKAGE.md |
| campaign | Number of contacts performed during this campaign, for this client, including the last contact | Numeric | Both | bank-full: 1 to 63, bank-additional-full: 1 to 56 | Engagement intensity |
| pdays | Days since the client was last contacted from a previous campaign | Numeric with sentinel | Both | bank-full: -1 means never contacted. bank-additional-full: 999 means never contacted | Recontact recency, needs sentinel handling |
| previous | Number of contacts performed before this campaign, for this client | Numeric | Both | bank-full: 0 to 275, bank-additional-full: 0 to 7 | Prior engagement |
| poutcome | Outcome of the previous marketing campaign | Categorical | Both | bank-full: unknown, other, failure, success. bank-additional-full: failure, nonexistent, success | Prior response history |
| emp.var.rate | Employment variation rate, quarterly indicator | Numeric | bank-additional-full only | -3.4 to 1.4 | Macroeconomic context |
| cons.price.idx | Consumer price index, monthly indicator | Numeric | bank-additional-full only | 92.201 to 94.767 | Macroeconomic context |
| cons.conf.idx | Consumer confidence index, monthly indicator | Numeric | bank-additional-full only | -50.8 to -26.9 | Macroeconomic context |
| euribor3m | Euribor 3-month rate, daily indicator | Numeric | bank-additional-full only | 0.634 to 5.045 | Macroeconomic context |
| nr.employed | Number of employees, quarterly indicator (national) | Numeric | bank-additional-full only | 4,963.6 to 5,228.1 | Macroeconomic context |
| y | Has the client subscribed a term deposit | Categorical (yes/no) | Both | Target variable |

Source: UCI Machine Learning Repository, Bank Marketing dataset (Moro, Cortez, Rita).

## Churn Dataset (churn_prediction.csv)

No external data dictionary shipped with this file. Descriptions below are inferred from column names and the observed value ranges documented in DATA_AUDIT.md, not from an official source.

| Field | Description (inferred) | Type | Valid Values | Analytical Use |
|---|---|---|---|---|
| customer_id | Unique customer identifier | Numeric | 1 to 30,301, unique | Primary key |
| vintage | Days since account was opened (inferred from range and name) | Numeric | 73 to 2,476 | Tenure |
| age | Customer age | Numeric | 1 to 90, see audit finding 3.3 | Demographic |
| gender | Customer gender | Categorical | Male, Female | Demographic |
| dependents | Number of dependents | Numeric | 0 to 9 typical, contains implausible outliers, see audit finding 3.1 | Household size proxy |
| occupation | Customer occupation category | Categorical | self_employed, salaried, student, retired, company | Segmentation |
| city | City code (inferred, not a real numeric quantity) | Numeric code | 0 to 1,649, 1,604 unique values | Geographic grouping if aggregated, not usable raw |
| customer_nw_category | Bank-assigned net worth tier (inferred from name; exact tier definitions not documented in the source files) | Numeric (ordinal, 1 to 3) | 1, 2, 3 | Wealth segmentation |
| branch_code | Branch identifier | Numeric code | 1 to 4,782, 3,185 unique values | Not usable as a raw feature, high cardinality |
| current_balance | Current account balance | Numeric | -5,503.96 to 5,905,904.03 | Financial value |
| previous_month_end_balance | Balance at the end of the previous month | Numeric | -3,149.57 to 5,740,438.63 | Financial value, trend input |
| average_monthly_balance_prevQ | Average monthly balance, previous quarter | Numeric | 1,428.69 to 5,700,289.57 | Financial value |
| average_monthly_balance_prevQ2 | Average monthly balance, quarter before that | Numeric | -16,506.10 to 5,010,170.10 | Financial value, trend input |
| current_month_credit | Total credits (inflows) this month | Numeric | 0.01 to 12,269,845.39 | Activity, heavy right skew |
| previous_month_credit | Total credits (inflows) last month | Numeric | 0.01 to 2,361,808.29 | Activity |
| current_month_debit | Total debits (outflows) this month | Numeric | 0.01 to 7,637,857.36 | Activity, heavy right skew |
| previous_month_debit | Total debits (outflows) last month | Numeric | 0.01 to 1,414,168.06 | Activity |
| current_month_balance | Average or closing balance this month (exact definition not documented; distinct from current_balance in the source) | Numeric | -3,374.18 to 5,778,184.77 | Financial value |
| previous_month_balance | Average or closing balance last month | Numeric | -5,171.92 to 5,720,144.50 | Financial value |
| churn | Whether the customer churned | Numeric (0/1) | 0 = retained (81.5%), 1 = churned (18.5%) | Target variable |
| last_transaction | Date of the customer's last transaction | Date (stored as text, needs conversion) | Contains literal "NaT" strings for 11.4% of rows, see audit finding 3.2 | Recency |

Two columns, `current_month_balance` and `current_balance`, appear related but are not identical in the raw data and their exact difference is not documented anywhere in the source files. This is flagged rather than guessed at; whoever writes the cleaning script should decide how to treat both fields rather than assuming they are duplicates.
