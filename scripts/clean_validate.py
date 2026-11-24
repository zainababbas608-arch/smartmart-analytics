"""Clean and validate raw CSVs, then write clean data and a quality report."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.transforms import (  # noqa: E402
    clean_customers,
    clean_products,
    clean_sales,
    clean_stores,
)


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def main() -> None:
    raw_dir = ROOT / "data" / "raw"
    clean_dir = ROOT / "data" / "clean"
    quality_dir = ROOT / "data" / "quality"
    for directory in (clean_dir, quality_dir):
        directory.mkdir(parents=True, exist_ok=True)

    raw_sales = read_csv(raw_dir / "sales.csv")
    raw_customers = read_csv(raw_dir / "customers.csv")
    raw_products = read_csv(raw_dir / "products.csv")
    raw_stores = read_csv(raw_dir / "stores.csv")

    customers, customer_stats = clean_customers(raw_customers)
    products, product_stats = clean_products(raw_products)
    stores, store_stats = clean_stores(raw_stores)
    sales, rejected, sales_stats = clean_sales(raw_sales, customers, products, stores)

    sales.to_csv(clean_dir / "sales.csv", index=False, float_format="%.2f")
    customers.to_csv(clean_dir / "customers.csv", index=False)
    products.to_csv(clean_dir / "products.csv", index=False, float_format="%.2f")
    stores.to_csv(clean_dir / "stores.csv", index=False)
    rejected.to_csv(quality_dir / "rejected_rows.csv", index=False)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "raw": {
            "sales": len(raw_sales), "customers": len(raw_customers),
            "products": len(raw_products), "stores": len(raw_stores),
        },
        "clean": {
            "sales": len(sales), "customers": len(customers),
            "products": len(products), "stores": len(stores),
        },
        "rejected_sales": sales_stats["rejected_rows"],
        "duplicate_sale_ids_removed": sales_stats["duplicate_sale_ids_removed"],
        "missing_or_unknown_customers_imputed": sales_stats["customers_imputed"],
        "suspected_natural_duplicates": sales_stats["suspected_natural_duplicates"],
        "rejection_reasons": sales_stats["rejection_reasons"],
        "revenue_total": sales_stats["revenue_total"],
        "date_range": {"min": sales_stats["date_min"], "max": sales_stats["date_max"]},
        "dimension_quality": {
            "customers": customer_stats,
            "products": product_stats,
            "stores": store_stats,
        },
    }
    (quality_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Clean data written to {clean_dir}")
    print(f"  raw sales:      {len(raw_sales):,}")
    print(f"  clean sales:    {len(sales):,}")
    print(f"  rejected:       {len(rejected):,}  {sales_stats['rejection_reasons']}")
    print(f"  duplicates:     {sales_stats['duplicate_sale_ids_removed']:,} removed")
    print(f"  customers:      {len(customers):,} (guest included)")
    print(f"  products:       {len(products):,}")
    print(f"  revenue total:  ${sales_stats['revenue_total']:,.2f}")
    print(f"  quality report: {quality_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
