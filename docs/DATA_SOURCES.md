# Data Sources

## Bank Customer Churn Data (Track A)

Source: https://www.kaggle.com/datasets/pentakrishnakishore/bank-customer-churn-data

Dataset: Bank Customer Churn Data
Uploader: Penta Krishna Kishore
License (as listed on the Kaggle page): Apache 2.0
Records: 28,382

**What has been independently verified:** the file used in this project (`churn_prediction.csv`, 28,382 rows, 21 columns: `customer_id`, `vintage`, `age`, `gender`, `dependents`, `occupation`, `city`, `customer_nw_category`, `branch_code`, the balance/credit/debit columns, `churn`, `last_transaction`) matches this exact schema, and this schema circulates publicly across several independent repositories under the same filename. The license and row count shown above were confirmed directly from a screenshot of the live Kaggle page ("28,382 customers," "License: Apache 2.0"), taken after this project's own tooling was unable to load the page due to Kaggle's bot protection.

**An additional finding worth recording:** the identical problem statement and dataset also appear in unrelated contexts as a data science course or bootcamp capstone assignment (the phrasing "A Bank wants to take care of customer retention for its product: savings accounts" and a corresponding "final project solution" file both turn up independently of any Kaggle listing). This suggests the dataset was originally distributed as course material and has since been re-uploaded to multiple platforms, including Kaggle, by different people. A license selected by a re-uploader reflects what that person chose to attach to their upload, not necessarily a verified chain of rights back to the data's original source.

Usage in this project: used as the source dataset for Track A customer churn analysis, statistical analysis, segmentation, and predictive modeling. The raw dataset is not modified; all cleaning and transformations are performed by the project's reproducible pipeline (`src/data/clean.py`).

**Verification status: confirmed.** The license field on the live Kaggle page has been directly viewed and matches what is recorded above. The remaining nuance worth keeping in mind, given the course-assignment origin noted below, is that this confirms what the current Kaggle uploader has attached to their upload, which is the relevant fact for using this specific file, rather than a full chain of title back to whichever bank the underlying anonymized data originally came from. For the purposes of this project and its attribution, that is sufficient.

## UCI Bank Marketing Dataset (Track B)

Source: UCI Machine Learning Repository, Bank Marketing dataset (Moro, Cortez, Rita)
Files used: `bank-full.csv`, `bank-additional-full.csv` (and their 10% sample counterparts, not used in analysis)
License: public for research use, citation required

This dataset's documentation ships with the files themselves (`bank-names.txt`, `bank-additional-names.txt`) and was independently reviewed in full during DATA_AUDIT.md. No verification gap exists here.
