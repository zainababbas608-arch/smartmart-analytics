"""Data loading, validation and cleaning transforms."""

from __future__ import annotations

import pandas as pd

SALES_COLUMNS = [
    "Sale_ID", "Sale_Date", "Customer_ID", "Product_ID", "Store_ID",
    "Quantity", "Unit_Price", "Discount_Pct",
]
CUSTOMER_COLUMNS = ["Customer_ID", "Customer_Name", "Email", "Phone", "City", "Region", "Join_Date"]
PRODUCT_COLUMNS = ["Product_ID", "Product_Name", "Category", "Unit_Price", "Unit_Cost"]
STORE_COLUMNS = ["Store_ID", "Store_Name", "City", "Region", "Channel"]
NATURAL_KEY = ["Sale_Date", "Customer_ID", "Product_ID", "Store_ID", "Quantity", "Unit_Price", "Discount_Pct"]
ALLOWED_REGIONS = {"north", "south", "east", "west", "online", "unknown"}


def _text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def _upper_id(series: pd.Series) -> pd.Series:
    return _text(series).str.upper()


def normalize_category(value: object) -> str:
    text = str(value).strip().lower()
    if "electronic" in text:
        return "Electronics"
    if "cloth" in text or "apparel" in text:
        return "Clothing"
    if "appliance" in text or text.startswith("home"):
        return "Home Appliances"
    if "grocer" in text:
        return "Grocery"
    return "Unknown"


def normalize_region(value: object) -> str:
    text = str(value).strip().title()
    return text if text.lower() in ALLOWED_REGIONS else "Unknown"


def normalize_channel(value: object) -> str:
    return "Online" if "online" in str(value).lower() else "Store"


def clean_products(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = raw.copy()
    for column in PRODUCT_COLUMNS:
        df[column] = _text(df[column])
    df["Product_ID"] = _upper_id(df["Product_ID"])
    df["Category"] = df["Category"].map(normalize_category)
    df["Unit_Price"] = pd.to_numeric(df["Unit_Price"], errors="coerce")
    df["Unit_Cost"] = pd.to_numeric(df["Unit_Cost"], errors="coerce")
    invalid = ~(df["Product_ID"].ne("") & df["Unit_Price"].gt(0) & df["Unit_Cost"].ge(0))
    invalid_count = int(invalid.sum())
    df = df.loc[~invalid].copy()
    duplicate_count = int(df.duplicated("Product_ID").sum())
    df = df.drop_duplicates("Product_ID", keep="first").sort_values("Product_ID").reset_index(drop=True)
    return df, {"invalid_rows": invalid_count, "duplicate_ids_removed": duplicate_count}


def clean_customers(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = raw.copy()
    for column in CUSTOMER_COLUMNS:
        df[column] = _text(df[column])
    df["Customer_ID"] = _upper_id(df["Customer_ID"])
    df["Email"] = df["Email"].str.lower()
    df["Region"] = df["Region"].map(normalize_region)
    df["Join_Date"] = pd.to_datetime(df["Join_Date"], format="%Y-%m-%d", errors="coerce")
    df["Join_Date"] = df["Join_Date"].fillna(pd.Timestamp("2024-01-01"))
    invalid = df["Customer_ID"].eq("")
    invalid_count = int(invalid.sum())
    df = df.loc[~invalid].copy()
    duplicate_count = int(df.duplicated("Customer_ID").sum())
    df = df.drop_duplicates("Customer_ID", keep="first").reset_index(drop=True)
    if "CUST-0000" not in set(df["Customer_ID"]):
        guest = pd.DataFrame([{
            "Customer_ID": "CUST-0000", "Customer_Name": "Guest Customer", "Email": "",
            "Phone": "", "City": "Unknown", "Region": "Unknown",
            "Join_Date": pd.Timestamp("2024-01-01"),
        }])
        df = pd.concat([guest, df], ignore_index=True)
    return df.sort_values("Customer_ID").reset_index(drop=True), {
        "invalid_rows": invalid_count,
        "duplicate_ids_removed": duplicate_count,
    }


def clean_stores(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = raw.copy()
    for column in STORE_COLUMNS:
        df[column] = _text(df[column])
    df["Store_ID"] = _upper_id(df["Store_ID"])
    df["Region"] = df["Region"].map(normalize_region)
    df["Channel"] = df["Channel"].map(normalize_channel)
    invalid = df["Store_ID"].eq("")
    invalid_count = int(invalid.sum())
    df = df.loc[~invalid].copy()
    duplicate_count = int(df.duplicated("Store_ID").sum())
    df = df.drop_duplicates("Store_ID", keep="first").sort_values("Store_ID").reset_index(drop=True)
    return df, {"invalid_rows": invalid_count, "duplicate_ids_removed": duplicate_count}


def clean_sales(
    raw: pd.DataFrame,
    customers: pd.DataFrame,
    products: pd.DataFrame,
    stores: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    df = raw.copy()
    for column in ["Sale_ID", "Customer_ID", "Product_ID", "Store_ID"]:
        df[column] = _upper_id(df[column])
    raw_dates = _text(df["Sale_Date"])
    df["Sale_Date"] = pd.to_datetime(raw_dates, format="%Y-%m-%d", errors="coerce")
    for column in ["Quantity", "Unit_Price", "Discount_Pct"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    reasons = pd.Series("", index=df.index, dtype="object")

    def mark(mask: pd.Series, label: str) -> None:
        mask = mask.fillna(False).astype(bool)
        reasons.loc[mask & reasons.eq("")] = label

    mark(df["Sale_Date"].isna(), "invalid_date")
    mark(df["Quantity"].isna() | df["Quantity"].le(0), "invalid_quantity")
    mark(df["Unit_Price"].isna() | df["Unit_Price"].le(0), "invalid_price")
    mark(df["Discount_Pct"].isna() | df["Discount_Pct"].lt(0) | df["Discount_Pct"].gt(100), "invalid_discount")
    mark(~df["Product_ID"].isin(set(products["Product_ID"])), "unknown_product")
    mark(~df["Store_ID"].isin(set(stores["Store_ID"])), "unknown_store")

    known_customers = set(customers["Customer_ID"])
    imputed_mask = ~df["Customer_ID"].isin(known_customers)
    imputed_count = int(imputed_mask.sum())
    df.loc[imputed_mask, "Customer_ID"] = "CUST-0000"
    df["Customer_Imputed"] = imputed_mask

    rejected = df.loc[reasons.ne(""), :].copy()
    rejected["Rejection_Reason"] = reasons.loc[reasons.ne("")]
    rejected["Sale_Date"] = raw_dates.loc[rejected.index]
    valid = df.loc[reasons.eq(""), :].copy()

    duplicate_mask = valid.duplicated("Sale_ID", keep="first")
    duplicate_count = int(duplicate_mask.sum())
    valid = valid.loc[~duplicate_mask].copy()
    valid["Suspected_Duplicate"] = valid.duplicated(NATURAL_KEY, keep="first")
    suspected_count = int(valid["Suspected_Duplicate"].sum())

    valid["Line_Revenue"] = (
        valid["Quantity"] * valid["Unit_Price"] * (1 - valid["Discount_Pct"] / 100)
    ).round(2)
    cost_map = products.set_index("Product_ID")["Unit_Cost"]
    valid["Unit_Cost"] = valid["Product_ID"].map(cost_map).fillna(0.0)

    date_min = valid["Sale_Date"].min()
    date_max = valid["Sale_Date"].max()
    valid = valid.sort_values(["Sale_Date", "Sale_ID"]).reset_index(drop=True)
    valid["Sale_Date"] = valid["Sale_Date"].dt.strftime("%Y-%m-%d")

    output_columns = [
        "Sale_ID", "Sale_Date", "Customer_ID", "Product_ID", "Store_ID",
        "Quantity", "Unit_Price", "Discount_Pct", "Line_Revenue", "Unit_Cost",
        "Customer_Imputed", "Suspected_Duplicate",
    ]
    valid = valid[output_columns]
    rejected = rejected[
        ["Sale_ID", "Sale_Date", "Customer_ID", "Product_ID", "Store_ID",
         "Quantity", "Unit_Price", "Discount_Pct", "Rejection_Reason"]
    ]
    stats = {
        "rejected_rows": int(len(rejected)),
        "duplicate_sale_ids_removed": duplicate_count,
        "customers_imputed": imputed_count,
        "suspected_natural_duplicates": suspected_count,
        "rejection_reasons": {str(k): int(v) for k, v in rejected["Rejection_Reason"].value_counts().items()},
        "date_min": date_min.strftime("%Y-%m-%d") if pd.notna(date_min) else None,
        "date_max": date_max.strftime("%Y-%m-%d") if pd.notna(date_max) else None,
        "revenue_total": round(float(valid["Line_Revenue"].sum()), 2),
    }
    return valid, rejected.reset_index(drop=True), stats
