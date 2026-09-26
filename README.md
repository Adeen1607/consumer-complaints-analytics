# Consumer Complaints Analytics

A regulatory-data business-intelligence project for analyzing complaint volume, product and issue trends, company response timeliness, disputed outcomes, and geographic concentration.

## Business questions

- Which products and issues generate the greatest complaint volume?
- Which companies receive unusually high complaint volumes or untimely responses?
- How quickly are complaint volumes changing over time?
- Which submission channels and states are associated with different response patterns?
- How should analysts distinguish volume from complaint rate when market-share denominators are unavailable?

## Data source

The project uses the [Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/) published by the U.S. Consumer Financial Protection Bureau. The database is updated regularly and can be downloaded as CSV or JSON.

Raw complaint narratives can contain sensitive personal experiences. This project does not publish narrative text and limits the reporting model to structured fields.

## Deliverables

- official-source download and extraction;
- chunked ingestion suitable for a multi-million-row CSV;
- normalized complaint fact table;
- monthly, product, issue, company, state, and response scorecards;
- Power BI measures and KPI definitions;
- refresh and privacy controls.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/download_data.py
python src/build_model.py --start-date 2023-01-01
```

## Dashboard pages

1. Executive complaint overview
2. Product and issue trends
3. Company response scorecard
4. Geographic analysis
5. Submission channels and resolution
6. Data quality and refresh status

## Interpretation

Complaint counts are not equivalent to complaint rates. Without reliable customer, account, or market-share denominators, this project reports volume and response behaviour rather than ranking firms by consumer harm. Publication and response timing can also change historical totals.
