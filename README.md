# SmartMart Retail Analytics

Salesforce Developer Edition + Streamlit Community Cloud analytics project.

> Scaffold only: implementation files are placeholders.

## Structure

```text
smartmart-analytics/
├── app.py
├── src/
│   ├── salesforce_client.py
│   ├── transforms.py
│   ├── kpis.py
│   └── charts.py
├── scripts/
│   ├── generate_data.py
│   ├── clean_validate.py
│   ├── load_salesforce.py
│   └── verify_kpis.py
├── data/
│   ├── raw/
│   ├── clean/
│   └── quality/
├── tests/
├── .streamlit/
│   └── secrets.toml.example
├── requirements.txt
└── README.md
```

## Planned pipeline

1. `scripts/generate_data.py` creates synthetic raw CSVs.
2. `scripts/clean_validate.py` validates and cleans them.
3. `scripts/load_salesforce.py` upserts clean data into Salesforce.
4. `app.py` serves the dashboard from Salesforce, with a CSV fallback.
5. `scripts/verify_kpis.py` reconciles KPI totals.

## Local setup

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in
Salesforce credentials. The real secrets file is git-ignored.
