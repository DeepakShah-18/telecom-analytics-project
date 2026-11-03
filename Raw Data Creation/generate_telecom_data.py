"""
Simplified synthetic telecom dataset generator
----------------------------------------------
Creates 7 CSV files for a fictional Indian telecom operator:
10,000 customers across 90 days (1 Jan to 31 Mar 2025).

Only 10 intentional data-quality issues are introduced:
- 5 in customers.csv
- 5 in daily_usage.csv

All other datasets are generated without intentional errors.
The data is synthetic and contains no real customer information.

Requirements:
    pip install pandas numpy

Run:
    python generate_telecom_data.py

Output:
    telecom_raw_data/
"""

from pathlib import Path
import numpy as np
import pandas as pd

# -------------------------
# 1. Settings
# -------------------------
SEED = 42
N_CUSTOMERS = 10_000
START_DATE = pd.Timestamp("2025-01-01")
END_DATE = pd.Timestamp("2025-03-31")
OUTPUT_DIR = Path("telecom_raw_data")

rng = np.random.default_rng(SEED)
OUTPUT_DIR.mkdir(exist_ok=True)

# -------------------------
# 2. Customer master data
# -------------------------
regions = {
    "North": ["Delhi", "Jaipur", "Chandigarh", "Lucknow"],
    "South": ["Bengaluru", "Chennai", "Hyderabad", "Kochi"],
    "East": ["Kolkata", "Patna", "Bhubaneswar", "Guwahati"],
    "West": ["Mumbai", "Pune", "Ahmedabad", "Surat"],
    "Central": ["Bhopal", "Indore", "Nagpur", "Raipur"],
}

plan_options = [
    (101, "Basic", 199, 1.5, 100),
    (102, "Smart", 299, 2.0, 200),
    (103, "Plus", 399, 2.5, 300),
    (104, "Premium", 599, 3.0, 500),
    (105, "Family", 799, 4.0, 700),
]

plan_df = pd.DataFrame(
    plan_options,
    columns=["plan_id", "plan_name", "monthly_rental_inr",
             "data_allowance_gb_per_day", "call_allowance_minutes"]
)

customer_ids = [f"CUST{i:06d}" for i in range(1, N_CUSTOMERS + 1)]
region_names = list(regions.keys())
customer_regions = rng.choice(region_names, N_CUSTOMERS,
                               p=[0.22, 0.20, 0.18, 0.22, 0.18])
cities = [rng.choice(regions[r]) for r in customer_regions]

plan_indices = rng.choice(len(plan_options), N_CUSTOMERS,
                          p=[0.20, 0.30, 0.25, 0.18, 0.07])
selected_plans = plan_df.iloc[plan_indices].reset_index(drop=True)

customers = pd.DataFrame({
    "customer_id": customer_ids,
    "customer_age": rng.integers(18, 71, N_CUSTOMERS),
    "region": customer_regions,
    "city": cities,
    "customer_segment": rng.choice(
        ["Prepaid", "Postpaid"], N_CUSTOMERS, p=[0.65, 0.35]
    ),
    "sales_channel": rng.choice(
        ["Retail Store", "Online", "Partner", "Telecalling"],
        N_CUSTOMERS, p=[0.35, 0.25, 0.25, 0.15]
    ),
    "signup_date": START_DATE - pd.to_timedelta(
        rng.integers(30, 900, N_CUSTOMERS), unit="D"
    ),
    "plan_id": selected_plans["plan_id"].to_numpy(),
    "plan_name": selected_plans["plan_name"].to_numpy(),
    "monthly_rental_inr": selected_plans["monthly_rental_inr"].to_numpy(),
    "data_allowance_gb_per_day": selected_plans[
        "data_allowance_gb_per_day"
    ].to_numpy(),
    "call_allowance_minutes": selected_plans[
        "call_allowance_minutes"
    ].to_numpy(),
})

# -------------------------
# 3. Churn status
# -------------------------
# A small group churns during the 90-day period.
churn_flags = rng.random(N_CUSTOMERS) < 0.06
churn_dates = np.full(N_CUSTOMERS, np.datetime64("NaT"),
                      dtype="datetime64[ns]")
churn_dates[churn_flags] = (
    START_DATE + pd.to_timedelta(
        rng.integers(5, 90, churn_flags.sum()), unit="D"
    )
)

# -------------------------
# 4. Daily usage and network quality
# -------------------------
date_range = pd.date_range(START_DATE, END_DATE, freq="D")
customer_index = np.repeat(np.arange(N_CUSTOMERS), len(date_range))
date_values = np.tile(date_range, N_CUSTOMERS)

daily = pd.DataFrame({
    "customer_id": np.array(customer_ids)[customer_index],
    "usage_date": date_values,
})

# Stop activity after the disconnection date.
daily["disconnection_date"] = churn_dates[customer_index]
daily = daily[
    daily["disconnection_date"].isna()
    | (daily["usage_date"] <= daily["disconnection_date"])
].copy()

# Usage is broadly plausible and remains within sensible daily limits.
daily["daily_data_consumption_gb"] = np.round(
    rng.gamma(shape=2.0, scale=0.65, size=len(daily)), 2
)
daily["call_minutes"] = rng.poisson(lam=35, size=len(daily))
daily["sms_count"] = rng.poisson(lam=8, size=len(daily))

# Network quality is recorded at the same customer-day grain.
network = daily[["customer_id", "usage_date"]].copy()
network["network_availability_pct"] = np.round(
    np.clip(rng.normal(97.0, 1.8, len(network)), 88, 100), 2
)
network["average_latency_ms"] = np.round(
    np.clip(rng.normal(55, 18, len(network)), 10, 180), 1
)
network["average_download_speed_mbps"] = np.round(
    np.clip(rng.normal(35, 12, len(network)), 2, 100), 2
)
network["dropped_calls"] = rng.poisson(lam=0.25, size=len(network))
network["network_quality_score"] = np.round(
    np.clip(
        100
        - (100 - network["network_availability_pct"]) * 2
        - network["average_latency_ms"] * 0.08
        + rng.normal(0, 3, len(network)),
        50, 100
    ), 1
)

# -------------------------
# 5. Invoices and payments
# -------------------------
billing_dates = pd.to_datetime(
    ["2025-01-01", "2025-01-31", "2025-03-02"]
)
invoice_rows = []
payment_rows = []
invoice_number = 1
payment_number = 1

customer_lookup = customers.set_index("customer_id")

for billing_date in billing_dates:
    eligible = customers[
        customers["signup_date"].le(billing_date)
        & (
            pd.Series(churn_dates, index=customers.index).isna()
            | pd.Series(churn_dates, index=customers.index).ge(billing_date)
        )
    ]

    for row in eligible.itertuples(index=False):
        billed = float(row.monthly_rental_inr)
        due_date = billing_date + pd.Timedelta(days=15)
        invoice_id = f"INV{invoice_number:08d}"
        invoice_number += 1

        # Most invoices receive a payment attempt; successful payments
        # reduce the invoice balance. Failed/pending attempts do not.
        if rng.random() < 0.82:
            status = rng.choice(
                ["Successful", "Failed", "Pending"],
                p=[0.90, 0.07, 0.03]
            )
            attempted_amount = round(
                billed * rng.choice([0.5, 0.75, 1.0], p=[0.10, 0.10, 0.80]), 2
            )
            payment_date = billing_date + pd.Timedelta(
                days=int(rng.integers(1, 16))
            )
            payment_amount = attempted_amount

            if status == "Successful":
                paid_amount = payment_amount
            else:
                paid_amount = 0.0

            payment_rows.append({
                "payment_id": f"PAY{payment_number:08d}",
                "invoice_id": invoice_id,
                "customer_id": row.customer_id,
                "payment_date": payment_date,
                "payment_amount_inr": payment_amount,
                "payment_method": rng.choice(
                    ["UPI", "Debit Card", "Credit Card", "Net Banking"]
                ),
                "payment_status": status,
            })
            payment_number += 1
        else:
            paid_amount = 0.0

        outstanding = round(max(billed - paid_amount, 0), 2)
        invoice_status = (
            "Paid" if outstanding == 0
            else "Partially Paid" if paid_amount > 0
            else "Unpaid"
        )

        invoice_rows.append({
            "invoice_id": invoice_id,
            "customer_id": row.customer_id,
            "invoice_date": billing_date,
            "due_date": due_date,
            "billed_amount_inr": billed,
            "outstanding_amount_inr": outstanding,
            "invoice_status": invoice_status,
        })

invoices = pd.DataFrame(invoice_rows)
payments = pd.DataFrame(payment_rows)

# -------------------------
# 6. Complaints
# -------------------------
n_complaints = 5_500
complaint_customer_ids = rng.choice(
    daily["customer_id"].to_numpy(), n_complaints, replace=True
)
complaint_dates = pd.to_datetime(
    rng.choice(date_range.to_numpy(), n_complaints)
)

complaints = pd.DataFrame({
    "complaint_id": [f"COMP{i:07d}" for i in range(1, n_complaints + 1)],
    "customer_id": complaint_customer_ids,
    "complaint_date": complaint_dates,
    "complaint_category": rng.choice(
        ["Network", "Billing", "Internet Speed", "Call Quality", "Other"],
        n_complaints, p=[0.30, 0.20, 0.25, 0.15, 0.10]
    ),
    "complaint_status": rng.choice(
        ["Resolved", "In Progress", "Escalated"],
        n_complaints, p=[0.75, 0.18, 0.07]
    ),
    "resolution_time_hours": rng.integers(1, 121, n_complaints),
})

# -------------------------
# 7. Churn table
# -------------------------
churn = pd.DataFrame({
    "customer_id": customer_ids,
    "churn_status": np.where(churn_flags, "Churned", "Active"),
    "disconnection_date": pd.to_datetime(churn_dates),
    "churn_reason": [
        rng.choice(
            ["High Price", "Poor Network", "Competitor Offer", "Relocation"]
        ) if flag else None
        for flag in churn_flags
    ],
    "churn_risk_score": np.round(
        np.where(
            churn_flags,
            rng.uniform(0.65, 1.00, N_CUSTOMERS),
            rng.uniform(0.00, 0.64, N_CUSTOMERS)
        ), 2
    ),
})

# -------------------------
# 8. Introduce 10 TYPES of data-quality issues
# -------------------------
# We affect multiple records for each issue so that SQL cleaning
# produces meaningful before-and-after row-count differences.
# The selected row groups are separate to avoid overlapping issues.

# CUSTOMERS: 5 issue types
customer_row_ids = rng.permutation(len(customers))

# 1. Missing region: 150 records (fill with "Unknown" or investigate)
customers.loc[customer_row_ids[:150], "region"] = None

# 2. Invalid age: 150 records (outside the valid 18-100 range)
customers.loc[customer_row_ids[150:300], "customer_age"] = 150

# 3. Invalid monthly rental: 150 records (negative values)
customers.loc[customer_row_ids[300:450], "monthly_rental_inr"] = -1

# 4. Inconsistent customer ID format: 200 records (lowercase IDs)
customers.loc[customer_row_ids[450:650], "customer_id"] = (
    customers.loc[customer_row_ids[450:650], "customer_id"].str.lower()
)

# 5. Duplicate customer records: 200 additional rows
duplicate_customer_rows = customers.iloc[customer_row_ids[650:850]].copy()
customers = pd.concat(
    [customers, duplicate_customer_rows], ignore_index=True
)

# DAILY USAGE: 5 issue types
daily = daily.reset_index(drop=True)
usage_row_ids = rng.permutation(len(daily))

# 6. Negative data consumption: 1,000 records
daily.loc[usage_row_ids[:1000], "daily_data_consumption_gb"] = -5

# 7. Invalid call minutes: 1,000 records (more than 24 hours in a day)
daily.loc[usage_row_ids[1000:2000], "call_minutes"] = 1500

# 8. Missing customer IDs: 1,000 records
daily.loc[usage_row_ids[2000:3000], "customer_id"] = None

# 9. Mixed date formats: 2,000 records (valid dates, different format)
mixed_date_rows = usage_row_ids[3000:5000]
daily.loc[mixed_date_rows, "usage_date"] = pd.to_datetime(
    daily.loc[mixed_date_rows, "usage_date"]
).dt.strftime("%d/%m/%Y")

# 10. Duplicate customer-date records: 1,000 additional rows
duplicate_usage_rows = daily.iloc[usage_row_ids[5000:6000]].copy()
daily = pd.concat(
    [daily, duplicate_usage_rows], ignore_index=True
)

# -------------------------
# 9. Save the 7 raw CSV files
# -------------------------
datasets = {
    "customers.csv": customers,
    "daily_usage.csv": daily,
    "invoices.csv": invoices,
    "payments.csv": payments,
    "complaints.csv": complaints,
    "network_quality.csv": network,
    "churn.csv": churn,
}

for filename, dataframe in datasets.items():
    dataframe.to_csv(OUTPUT_DIR / filename, index=False)

print("Dataset generation completed.")
print(f"Output folder: {OUTPUT_DIR.resolve()}")
print("\nGenerated files and row counts:")
for filename, dataframe in datasets.items():
    print(f"{filename:<22} {len(dataframe):>10,} rows")

print("\nIntentional data-quality issue TYPES: 10")
print("customers.csv:")
print("- Missing region: 150")
print("- Invalid age: 150")
print("- Invalid monthly rental: 150")
print("- Lowercase customer IDs: 200")
print("- Duplicate customer records added: 200")
print("daily_usage.csv:")
print("- Negative data consumption: 1,000")
print("- Invalid call minutes: 1,000")
print("- Missing customer IDs: 1,000")
print("- Mixed date formats: 2,000")
print("- Duplicate customer-date records added: 1,000")
print("Other 5 datasets: no intentional issues")
print("\nAll data is fictional.")
