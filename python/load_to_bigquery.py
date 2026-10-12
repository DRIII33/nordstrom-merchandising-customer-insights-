from google.colab import auth
from google.cloud import bigquery

auth.authenticate_user()
PROJECT, DATASET = "driiiportfolio", "merchandising_insights"
client = bigquery.Client(project=PROJECT)

ds = bigquery.Dataset(f"{PROJECT}.{DATASET}")
ds.location = "US"
client.create_dataset(ds, exists_ok=True)

F = bigquery.SchemaField
SCHEMAS = {
    "raw_transactions": [
        F("transaction_id", "STRING"), F("transaction_date", "STRING"), F("customer_id", "STRING"),
        F("sales_channel", "STRING"), F("merchandise_category", "STRING"), F("brand_id", "STRING"),
        F("units_sold", "INT64"), F("unit_price", "FLOAT64"), F("is_promotional", "INT64"),
        F("discount_percentage", "FLOAT64"), F("gross_revenue", "FLOAT64"), F("net_revenue", "FLOAT64"),
        F("cost_of_goods_sold", "FLOAT64"), F("gross_margin", "FLOAT64"), F("is_returned", "INT64"),
        F("returned_net_revenue", "FLOAT64")],
    "raw_customers": [
        F("customer_id", "STRING"), F("signup_date", "DATE"), F("home_channel", "STRING"),
        F("loyalty_tier", "STRING")],
    "raw_brands": [
        F("brand_id", "STRING"), F("brand_name", "STRING"), F("merchandise_category", "STRING"),
        F("price_tier", "STRING")],
    "raw_promo_calendar": [
        F("event_id", "STRING"), F("event_name", "STRING"), F("start_date", "DATE"), F("end_date", "DATE"),
        F("sales_channel", "STRING"), F("discount_options", "STRING")],
    "raw_inventory_monthly": [
        F("month_start", "DATE"), F("sales_channel", "STRING"), F("merchandise_category", "STRING"),
        F("avg_inventory_cost", "FLOAT64")],
}

for table, schema in SCHEMAS.items():
    cfg = bigquery.LoadJobConfig(schema=schema, source_format=bigquery.SourceFormat.CSV,
                                 skip_leading_rows=1, write_disposition="WRITE_TRUNCATE")
    with open(f"data/{table}.csv", "rb") as fh:
        client.load_table_from_file(fh, f"{PROJECT}.{DATASET}.{table}", job_config=cfg).result()
    print(table, client.get_table(f"{PROJECT}.{DATASET}.{table}").num_rows, "rows")
