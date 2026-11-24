"""Generate synthetic raw SmartMart CSV data with injected quality issues."""

from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
SEED = 42

REGIONS = {
    "North": ["Lahore", "Islamabad", "Rawalpindi"],
    "South": ["Karachi", "Hyderabad"],
    "East": ["Faisalabad", "Multan"],
    "West": ["Quetta", "Peshawar"],
}

PRODUCTS = {
    "Electronics": [
        'Smart LED TV 43"', 'Smart LED TV 55"', "Bluetooth Speaker",
        "Wireless Earbuds", "USB-C Charger 65W", "Power Bank 20000mAh",
        "Gaming Mouse", "Mechanical Keyboard", "Wi-Fi Router",
        "Security Camera", "Smart Watch", 'Tablet 10"', "Laptop Backpack",
        "HDMI Cable 2m", "Surge Protector", "Desk Lamp", "Portable Fan",
        "Action Camera", "Noise-Cancelling Headphones", "4K Streaming Stick",
    ],
    "Clothing": [
        "Men's Cotton Shirt", "Men's Denim Jeans", "Women's Lawn Suit",
        "Women's Abaya", "Kids' T-Shirt", "Kids' Hoodie", "Men's Polo Shirt",
        "Women's Cotton Kurta", "Men's Formal Trousers", "Women's Denim Jacket",
        "Sports Socks Pack", "Men's Hoodie", "Women's Scarf", "Kids' Shorts",
        "Men's Jacket", "Women's Maxi Dress", "Unisex Cap", "Men's Sweater",
        "Women's Cardigan", "Kids' Pajama Set",
    ],
    "Home Appliances": [
        "Microwave Oven", "Electric Kettle", "Vacuum Cleaner", "Air Fryer",
        "Blender", "Toaster", "Coffee Maker", "Rice Cooker", "Electric Iron",
        "Washing Machine", "Refrigerator 12 cu ft", "Air Conditioner 1.5 Ton",
        "Ceiling Fan", "Water Dispenser", "Sewing Machine", "Hair Dryer",
        "Sandwich Maker", "Food Processor", "Room Heater", "Water Purifier",
    ],
    "Grocery": [
        "Basmati Rice 5kg", "Cooking Oil 5L", "Wheat Flour 10kg",
        "White Sugar 5kg", "Red Lentils 1kg", "Green Tea 200g",
        "Milk Powder 1kg", "Breakfast Cereal 500g", "Pasta 500g",
        "Tomato Ketchup 500ml", "Mineral Water 12-Pack", "Eggs 30-Pack",
        "Chicken Spread 500g", "Honey 500g", "Mixed Nuts 500g",
        "Coffee 200g", "Biscuits Family Pack", "Laundry Detergent 3kg",
        "Dishwashing Liquid 1L", "Tissue Box 6-Pack",
    ],
}

CODES = {"Electronics": "ELE", "Clothing": "CLO", "Home Appliances": "HOM", "Grocery": "GRO"}
PRICE_RANGE = {"Electronics": (80, 1200), "Clothing": (15, 80), "Home Appliances": (40, 450), "Grocery": (3, 35)}
QTY_RANGE = {"Electronics": (1, 2), "Clothing": (1, 4), "Home Appliances": (1, 2), "Grocery": (1, 8)}

FIRST_NAMES = [
    "Ali", "Ahmed", "Sara", "Ayesha", "Bilal", "Fatima", "Hassan", "Hina",
    "Usman", "Zainab", "Omar", "Maryam", "Hamza", "Sana", "Tariq", "Nadia",
    "Imran", "Rabia", "Faisal", "Mehwish", "Areeba", "Danish", "Iqra", "Saad", "Noor",
]
LAST_NAMES = ["Khan", "Ahmed", "Ali", "Malik", "Sheikh", "Iqbal", "Butt", "Chaudhry", "Raza", "Siddiqui"]

STORE_CITIES = [
    ("ST-001", "Lahore", "North"), ("ST-002", "Islamabad", "North"),
    ("ST-003", "Karachi", "South"), ("ST-004", "Hyderabad", "South"),
    ("ST-005", "Faisalabad", "East"), ("ST-006", "Multan", "East"),
    ("ST-007", "Quetta", "West"), ("ST-008", "Peshawar", "West"),
]

SALES_COLUMNS = ["Sale_ID", "Sale_Date", "Customer_ID", "Product_ID", "Store_ID", "Quantity", "Unit_Price", "Discount_Pct"]
CUSTOMER_COLUMNS = ["Customer_ID", "Customer_Name", "Email", "Phone", "City", "Region", "Join_Date"]
PRODUCT_COLUMNS = ["Product_ID", "Product_Name", "Category", "Unit_Price", "Unit_Cost"]
STORE_COLUMNS = ["Store_ID", "Store_Name", "City", "Region", "Channel"]


def public(rows: list[dict], columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame([{key: row[key] for key in columns} for row in rows], columns=columns)


def main() -> None:
    rng = random.Random(SEED)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    products = []
    for category, names in PRODUCTS.items():
        lo, hi = PRICE_RANGE[category]
        for index, name in enumerate(names, start=1):
            price = round(rng.uniform(lo, hi), 2)
            products.append({
                "Product_ID": f"{CODES[category]}-{index:03d}",
                "Product_Name": name,
                "Category": category,
                "Unit_Price": price,
                "Unit_Cost": round(price * rng.uniform(0.55, 0.85), 2),
                "_Popularity": rng.randint(1, 10),
            })

    customers = []
    join_start = date(2023, 1, 1)
    join_days = (date(2026, 9, 30) - join_start).days
    for index in range(1, 251):
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        region = rng.choice(list(REGIONS))
        customers.append({
            "Customer_ID": f"CUST-{index:04d}",
            "Customer_Name": f"{first} {last}",
            "Email": f"{first.lower()}.{last.lower()}{index}@example.com",
            "Phone": f"+92-3{rng.randint(10, 49)}-{rng.randint(1000000, 9999999)}",
            "City": rng.choice(REGIONS[region]),
            "Region": region,
            "Join_Date": (join_start + timedelta(days=rng.randrange(join_days + 1))).isoformat(),
            "_Loyalty": round(rng.uniform(0.15, 0.95), 2),
            "_Preferred": rng.choice(list(PRODUCTS)),
        })

    stores = []
    for store_id, city, region in STORE_CITIES:
        stores.append({
            "Store_ID": store_id, "Store_Name": f"SmartMart {city}",
            "City": city, "Region": region, "Channel": "Store",
            "_Popularity": rng.randint(1, 10),
        })
    stores.append({
        "Store_ID": "ONLINE", "Store_Name": "SmartMart Online",
        "City": "Online", "Region": "Online", "Channel": "Online", "_Popularity": 10,
    })

    start, end = date(2025, 1, 1), date(2026, 10, 31)
    dates = [start + timedelta(days=offset) for offset in range((end - start).days + 1)]
    date_weights = [1.45 if day.month in (11, 12) else 1.0 for day in dates]
    physical = [store for store in stores if store["Channel"] == "Store"]
    online = next(store for store in stores if store["Channel"] == "Online")

    sales = []
    for _ in range(1200):
        sale_date = rng.choices(dates, weights=date_weights, k=1)[0]
        eligible = [customer for customer in customers if customer["Join_Date"] <= sale_date.isoformat()]
        customer = rng.choices(eligible, weights=[item["_Loyalty"] for item in eligible], k=1)[0]
        category = customer["_Preferred"] if rng.random() < 0.65 else rng.choice(list(PRODUCTS))
        pool = [product for product in products if product["Category"] == category]
        product = rng.choices(pool, weights=[item["_Popularity"] for item in pool], k=1)[0]
        store = online if rng.random() < 0.35 else rng.choices(physical, weights=[item["_Popularity"] for item in physical], k=1)[0]
        sales.append({
            "Sale_ID": "",
            "Sale_Date": sale_date.isoformat(),
            "Customer_ID": customer["Customer_ID"],
            "Product_ID": product["Product_ID"],
            "Store_ID": store["Store_ID"],
            "Quantity": rng.randint(*QTY_RANGE[category]),
            "Unit_Price": product["Unit_Price"],
            "Discount_Pct": rng.choices([0, 5, 10, 15, 20, 25, 30], weights=[35, 20, 15, 12, 8, 6, 4], k=1)[0],
        })

    sales.sort(key=lambda row: row["Sale_Date"])
    for index, row in enumerate(sales, start=1):
        row["Sale_ID"] = f"SALE-{index:06d}"

    dirty, bad_dates = [], ["2025-02-30", "2025-13-01", "31/12/2025", "not-a-date", "2026-00-15"]
    for _ in range(30):
        dirty.append(dict(sales[rng.randrange(len(sales))]))
    for index in range(1, 21):
        row = dict(sales[rng.randrange(len(sales))])
        row.update({"Sale_ID": f"DIRTY-{index:04d}", "Customer_ID": ""})
        dirty.append(row)
    for index in range(1, 16):
        row = dict(sales[rng.randrange(len(sales))])
        row.update({"Sale_ID": f"DIRTY-{20 + index:04d}", "Sale_Date": bad_dates[(index - 1) % len(bad_dates)]})
        dirty.append(row)
    for index in range(1, 11):
        row = dict(sales[rng.randrange(len(sales))])
        row.update({"Sale_ID": f"DIRTY-{35 + index:04d}", "Quantity": -abs(row["Quantity"])})
        dirty.append(row)
    for index in range(1, 11):
        row = dict(sales[rng.randrange(len(sales))])
        row.update({"Sale_ID": f"DIRTY-{45 + index:04d}", "Discount_Pct": rng.choice([120, -5, 150])})
        dirty.append(row)
    for index in range(1, 11):
        row = dict(sales[rng.randrange(len(sales))])
        row.update({"Sale_ID": f"DIRTY-{55 + index:04d}", "Product_ID": "PROD-9999"})
        dirty.append(row)
    for index in range(1, 6):
        row = dict(sales[rng.randrange(len(sales))])
        row.update({"Sale_ID": f"DIRTY-{65 + index:04d}", "Store_ID": "ST-999"})
        dirty.append(row)
    for index in range(1, 11):
        row = dict(sales[rng.randrange(len(sales))])
        row.update({"Sale_ID": f"SALE-NDUP-{index:03d}"})
        dirty.append(row)

    raw_products = [dict(product) for product in products]
    variants = {
        "Electronics": ["electronics", " ELECTRONICS ", "Electronics "],
        "Clothing": ["clothing", "Clothing ", "apparel"],
        "Home Appliances": ["home appliance", "HOME APPLIANCES", "Home Appliances "],
        "Grocery": ["groceries", " GROCERY ", "Grocery "],
    }
    for index in rng.sample(range(len(raw_products)), 25):
        category = raw_products[index]["Category"]
        raw_products[index]["Category"] = rng.choice(variants[category])
    for index in rng.sample(range(len(raw_products)), 3):
        raw_products[index]["Category"] = "Toys"
    for _ in range(3):
        raw_products.append(dict(raw_products[rng.randrange(len(products))]))

    raw_customers = [dict(customer) for customer in customers]
    for _ in range(3):
        raw_customers.append(dict(raw_customers[rng.randrange(len(customers))]))

    public(sales + dirty, SALES_COLUMNS).to_csv(RAW_DIR / "sales.csv", index=False, encoding="utf-8")
    public(raw_customers, CUSTOMER_COLUMNS).to_csv(RAW_DIR / "customers.csv", index=False, encoding="utf-8")
    public(raw_products, PRODUCT_COLUMNS).to_csv(RAW_DIR / "products.csv", index=False, encoding="utf-8")
    public(stores, STORE_COLUMNS).to_csv(RAW_DIR / "stores.csv", index=False, encoding="utf-8")

    print(f"Wrote raw data to {RAW_DIR}")
    print(f"  sales:     {len(sales) + len(dirty):,} rows ({len(sales):,} valid + {len(dirty)} dirty/duplicate)")
    print(f"  customers: {len(raw_customers):,} rows")
    print(f"  products:  {len(raw_products):,} rows")
    print(f"  stores:    {len(stores):,} rows")


if __name__ == "__main__":
    main()
