# Telecom Business Performance Analytics

An end-to-end analytics project for a fictional Indian telecom operator. The project uses **synthetic data for 10,000 customers across 90 consecutive days (1 January–31 March 2025)** to demonstrate data generation, BigQuery data engineering, data quality validation, and Power BI reporting.

**GitHub repository:** [DeepakShah-18/telecom-analytics-project](https://github.com/DeepakShah-18/telecom-analytics-project)

> **Data notice:** All records are synthetically generated for learning and demonstration. They do not represent real customers or an actual telecom operator.

## Project objectives

- Build a reproducible synthetic telecom dataset using Python.
- Ingest raw datasets into BigQuery while preserving the original source records.
- Clean, standardise, validate, match, and deduplicate data using SQL.
- Create a reliable analytical model for customer, usage, churn, network, complaints, billing, and payments analysis.
- Develop a Power BI dashboard for executive and regional performance monitoring.

## Technology stack

| Area | Technology |
|---|---|
| Data generation | Python |
| Cloud data warehouse | Google BigQuery |
| Data transformation | BigQuery Standard SQL |
| Data modelling and visualisation | Power BI, DAX |
| Source control | Git, GitHub |

## Data pipeline and architecture

The project follows a **Bronze-to-Silver medallion approach**. The Bronze layer preserves the uploaded source data; SQL transformations create validated Silver-layer tables for reporting.

```text
Python synthetic data generation
              |
              v
       Seven raw datasets
              |
              v
  BigQuery: Bronze_Layer_Raw
       (source data retained)
              |
              |  SQL transformations
              |  - standardise and type-cast
              |  - validate business rules
              |  - match customer/invoice keys
              |  - remove duplicates
              |  - derive invoice status
              v
  BigQuery: Silver_Layer_Clean
       (clean analytical tables)
              |
              |  Power BI Import mode
              v
     Power BI semantic model
              |
              v
       Three-page report
   + regional drill-through
   + row-level security
```

### BigQuery environment

- **Google Cloud project:** `weighty-actor-513623-m6`
- **Raw dataset:** `Bronze_Layer_Raw`
- **Clean dataset:** `Silver_Layer_Clean`

The Bronze tables are retained as the original ingestion layer. Cleaning and validation are performed in separate Silver tables, leaving the source tables unchanged.

## Source datasets

The synthetic dataset contains seven files/tables:

| Dataset | Grain / content |
|---|---|
| `customers` | Customer profile, age, region, city, segment, sales channel, signup date, and plan details |
| `daily_usage` | Daily customer data consumption, call minutes, and SMS count |
| `invoices` | Customer invoices, invoice and due dates, billed amount, and outstanding amount |
| `payments` | Payments linked to customers and invoices, including date, amount, method, and status |
| `complaints` | Customer complaints, category, status, and resolution time |
| `network_quality` | Daily network availability, latency, download speed, dropped calls, and quality score |
| `churn` | Customer churn status, disconnection date, churn reason, and churn risk score |

## Bronze-to-Silver data quality results

The following counts were recorded after the Silver-layer transformations.

| Table | Bronze rows | Silver rows | Rows removed | Retention |
|---|---:|---:|---:|---:|
| `churn` | 10,000 | 9,700 | 300 | 97.00% |
| `complaints` | 5,500 | 5,348 | 152 | 97.24% |
| `customers` | 10,201 | 9,700 | 501 | 95.09% |
| `daily_usage` | 877,059 | 845,769 | 31,290 | 96.43% |
| `invoices` | 29,468 | 28,575 | 893 | 96.97% |
| `network_quality` | 876,058 | 849,413 | 26,645 | 96.96% |
| `payments` | 24,045 | 23,313 | 732 | 96.96% |
| **Total** | **1,832,331** | **1,771,818** | **60,513** | **96.70%** |

### Interpreting the row-count differences

Rows are removed during validation, deduplication, date and value filtering, and referential-integrity checks. For example, daily usage and network quality are recorded at customer-day level, so they naturally contain hundreds of thousands of rows. Records associated with customers excluded from `customers_clean` are also excluded from these customer-linked tables. Their row-count reductions can therefore be larger than the number of customer records removed. The difference is not attributable to customer exclusions alone; table-specific validation and duplicate removal also contribute.

## Silver-layer transformation rules

Each table follows a **clean → validate → match where applicable → deduplicate → create Silver table** process.

### 1. Customers — `customers_clean`

- Uppercase and trim `customer_id`; trim text fields.
- Convert age, plan ID, rental, and allowance fields to appropriate numeric types; parse `signup_date` as a date.
- Replace blank or missing regions with `Unknown` rather than discarding the customer for a missing region.
- Remove header rows mistakenly stored as data.
- Retain customers aged 18–100, with a positive monthly rental, a valid signup date, and plan IDs from 101 to 105.
- Deduplicate on `customer_id`.

### 2. Daily usage — `daily_usage_clean`

- Uppercase and trim `customer_id`.
- Parse usage dates in both `YYYY-MM-DD` and `DD/MM/YYYY` formats.
- Convert data consumption, call minutes, and SMS count to numeric types.
- Remove header rows mistakenly stored as data.
- Keep records from 1 January to 31 March 2025; validate data consumption (0–100 GB), call minutes (0–1,440), and non-negative SMS counts.
- Retain only records matching a valid customer in `customers_clean`.
- Deduplicate on `customer_id` and `usage_date`.

### 3. Complaints — `complaints_clean`

- Trim complaint IDs and text fields; uppercase and trim customer IDs.
- Convert complaint dates and resolution hours to appropriate data types.
- Retain only complaints linked to customers in `customers_clean`.
- Require a complaint ID and date; allow statuses `Resolved`, `In Progress`, and `Escalated`; reject negative resolution times.
- Deduplicate on `complaint_id`.

### 4. Churn — `churn_clean`

- Uppercase and trim customer IDs; convert disconnection dates and churn risk scores to appropriate data types.
- Retain only records matching `customers_clean`.
- Allow only `Active` and `Churned` statuses; constrain churn risk scores to the 0–1 range.
- Enforce the date rule: Active customers must have no disconnection date; Churned customers must have a disconnection date.
- Deduplicate on `customer_id`.

### 5. Network quality — `network_quality_clean`

- Uppercase and trim customer IDs; convert usage dates and network metrics to appropriate data types.
- Retain only records matching `customers_clean` and dated from 1 January to 31 March 2025.
- Validate network availability and quality scores within 0–100; require non-negative latency, download speed, and dropped-call counts.
- Deduplicate on `customer_id` and `usage_date`.

### 6. Invoices — `invoices_clean`

- Trim invoice IDs; uppercase and trim customer IDs.
- Convert invoice dates, due dates, and monetary amounts to appropriate data types.
- Retain only invoices linked to customers in `customers_clean`.
- Require an invoice ID and invoice date; ensure the due date is not earlier than the invoice date.
- Require a positive billed amount and an outstanding amount between zero and the billed amount.
- Deduplicate on `invoice_id`.
- Derive `invoice_status` from the outstanding amount rather than relying on the source status: `Paid` when outstanding is zero, `Unpaid` when outstanding equals the billed amount, and `Partially Paid` otherwise.

### 7. Payments — `payments_clean`

- Trim payment and invoice IDs; uppercase and trim customer IDs.
- Convert payment dates and payment amounts to appropriate data types.
- Retain only payments matching both the invoice ID and customer ID in `invoices_clean`.
- Require a payment ID and payment date; reject negative payment amounts.
- Allow only `Successful`, `Failed`, and `Pending` payment statuses.
- Deduplicate on `payment_id`.

## Power BI data model

The Silver tables are imported into Power BI using **Import mode**. The semantic model uses a star-schema approach, with customer and date dimensions connected to the relevant analytical tables.

### Key relationships

| Table | Key / grain | Relationship role |
|---|---|---|
| `customers_clean` | `customer_id` | Customer dimension primary key |
| `daily_usage_clean` | `customer_id` + `usage_date` | Customer and date foreign keys; customer-day grain |
| `network_quality_clean` | `customer_id` + `usage_date` | Customer and date foreign keys; customer-day grain |
| `complaints_clean` | `complaint_id` | Complaint identifier; `customer_id` links to customers |
| `churn_clean` | `customer_id` | One record per customer; links to the customer dimension |
| `invoices_clean` | `invoice_id` | Invoice identifier; `customer_id` links to customers |
| `payments_clean` | `payment_id` | Payment identifier; `invoice_id` links to invoices and `customer_id` links to customers |

**Key terminology:** `customers_clean.customer_id` is the primary key of the customer dimension. In the related tables, `customer_id` is a foreign key to that dimension. Identifiers such as `complaint_id`, `invoice_id`, and `payment_id` identify records in their respective tables; they are not customer foreign keys. In `payments_clean`, `invoice_id` is also a foreign key to `invoices_clean.invoice_id`.

Daily usage and network quality have a customer-day grain, so the natural row identifier is the combination of `customer_id` and `usage_date`. The SQL uses `ROW_NUMBER()` to deduplicate these combinations. The table-creation scripts do not explicitly declare enforced BigQuery primary-key or foreign-key constraints; the keys above describe the logical and Power BI model relationships.

A DAX date dimension is used to support date-based analysis.

## Power BI dashboard and analysis

The Power BI report contains three pages and includes an executive summary and a regional drill-through experience.

### Key performance indicators

The dashboard includes measures and analysis for:

- Active customers, churned customers, churn risk percentage, and churn by risk segment.
- Billed revenue, total collections, outstanding amount, and collection rate.
- Network availability, average daily data usage, average latency, and network quality score.
- Total complaints, resolved complaints, average resolution time, and resolution rate.
- Regional performance and customer-level operational trends.

DAX functions used include `CALCULATE`, `SUM`, `AVERAGE`, `COUNT`, `DISTINCTCOUNT`, `ADDCOLUMNS`, `CALENDAR`, `IF`, `ROUND`, and text-concatenation functions.

### Report functionality

- **Executive summary:** Presents key business metrics for quick performance assessment.
- **Regional drill-through:** A page titled **Regional Performance Details** lets users select a region and navigate to detailed regional insights.
- **Row-level security (RLS):** A role named **North Regional Manager** is configured to restrict the report to North region data. In Power BI Service, assign the appropriate users or groups to the role after publishing.
- **Publishing and refresh:** The report is designed for publication to Power BI Service. Configure data-source credentials, scheduled refresh, and report access there.

### Screenshots

Add the star-schema and three report-page screenshots to the repository (for example, in an `images/` folder) and embed them here using relative Markdown image links. The screenshots were not included with the project details used to prepare this README.

## Re-creating the project

The repository currently includes the following project areas:

- `Raw Data Creation/` — synthetic raw-data generation.
- `Data Cleaning - SQL Scripts/` — SQL transformations for the Silver layer.

To reproduce the workflow:

1. Clone the repository:

   ```bash
   git clone https://github.com/DeepakShah-18/telecom-analytics-project.git
   cd telecom-analytics-project
   ```

2. Run the Python data-generation workflow in `Raw Data Creation/` to create the seven synthetic datasets.
3. Create the BigQuery project datasets `Bronze_Layer_Raw` and `Silver_Layer_Clean`, or update the SQL scripts to use your own project and dataset names.
4. Upload the generated source files to the corresponding tables in `Bronze_Layer_Raw`.
5. Run the SQL scripts in `Data Cleaning - SQL Scripts/`. Create `customers_clean` first because the other customer-linked tables use it for validation. Create `invoices_clean` before `payments_clean` because payments are matched to invoices.
6. Connect the Silver-layer tables to Power BI using Import mode. Recreate the relationships, date dimension, DAX measures, visuals, drill-through page, and RLS role.
7. Publish the report to Power BI Service, configure credentials and scheduled refresh, and assign report access and RLS role membership.

The exact Python package requirements and Power BI report file location should be documented in the repository if they are distributed as part of the project.

## Project scope and considerations

- The dataset represents a fictional operator and is intended for demonstration, portfolio, and learning purposes.
- The reporting window covers 90 days: 1 January–31 March 2025.
- Bronze-to-Silver row-count differences are expected because of data validation, deduplication, date filtering, and relationship checks.
- Power BI scheduled refresh and user access depend on the workspace, data-source credentials, licensing, and any required gateway configuration.

## Repository

[View the source code and SQL scripts on GitHub](https://github.com/DeepakShah-18/telecom-analytics-project)
