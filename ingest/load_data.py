#!/usr/bin/env python3
"""E-commerce data ingestion with validation + quarantine."""
import sys, logging, yaml, pandas as pd, psycopg2, requests
from psycopg2.extras import execute_values
from datetime import date
from pathlib import Path

def setup_logging(log_file, level):
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=getattr(logging, level.upper()),
                        format="%(asctime)s | %(levelname)-8s | %(message)s",
                        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)])
    return logging.getLogger(__name__)

def load_config(path):
    with open(path) as f: return yaml.safe_load(f)

def get_db_connection(cfg):
    import os
    db = cfg["database"]
    # Allow env vars to override config (for Airflow/local flexibility)
    host = os.getenv("POSTGRES_HOST", db["host"])
    port = int(os.getenv("POSTGRES_PORT", db["port"]))
    dbname = os.getenv("POSTGRES_DB", db["dbname"])
    user = os.getenv("POSTGRES_USER", db["user"])
    password = os.getenv("POSTGRES_PASSWORD", db["password"])
    return psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)

def fetch_fx_rates(cfg, dates):
    base = cfg["fx_api"]["base_url"]; base_ccy = cfg["fx_api"]["base_currency"]
    timeout = cfg["fx_api"]["timeout_seconds"]; rates = {}
    for d in sorted(set(dates)):
        try:
            r = requests.get(f"{base}/{d.isoformat()}?from={base_ccy}", timeout=timeout)
            r.raise_for_status()
            rates[d.isoformat()] = {c: 1/v for c,v in r.json().get("rates",{}).items()}
            rates[d.isoformat()][base_ccy] = 1.0
        except Exception as e:
            logging.warning(f"FX failed {d}: {e}"); rates[d.isoformat()] = {base_ccy: 1.0}
    return rates

def convert_usd(amt, ccy, dt, rates):
    if ccy == "USD": return amt
    r = rates.get(dt.isoformat(), {}).get(ccy)
    return round(amt * r, 2) if r else amt

def load_csvs(cfg):
    logger = logging.getLogger(__name__)
    d = Path(__file__).parent
    c = pd.read_csv(d / cfg["files"]["customers"])
    o = pd.read_csv(d / cfg["files"]["orders"])
    i = pd.read_csv(d / cfg["files"]["order_items"])
    for n,df in [("c",c),("o",o),("i",i)]:
        if df.empty: raise ValueError(f"{n} empty")
        logger.info(f"Loaded {n}: {len(df)} rows")
    return c,o,i

def validate_cust(r):
    e = []
    if pd.isna(r['customer_id']) or not str(r['customer_id']).strip().isdigit():
        e.append(("INVALID_CUSTOMER_ID", f"customer_id={r['customer_id']}"))
    if pd.isna(r['email']) or "@" not in str(r['email']):
        e.append(("INVALID_EMAIL", f"email={r['email']}"))
    if pd.isna(r['created_at']):
        e.append(("INVALID_CREATED_AT", f"created_at={r['created_at']}"))
    return e

def validate_ord(r):
    e = []
    if pd.isna(r['order_id']) or not str(r['order_id']).strip().isdigit():
        e.append(("INVALID_ORDER_ID", f"order_id={r['order_id']}"))
    if pd.isna(r['customer_id']) or not str(r['customer_id']).strip().isdigit():
        e.append(("INVALID_CUSTOMER_ID_FK", f"customer_id={r['customer_id']}"))
    if pd.isna(r['order_date']):
        e.append(("INVALID_ORDER_DATE", f"order_date={r['order_date']}"))
    if pd.isna(r['total_amount']):
        e.append(("INVALID_AMOUNT", f"total_amount={r['total_amount']}"))
    return e

def validate_item(r):
    e = []
    if pd.isna(r['order_item_id']) or not str(r['order_item_id']).strip().isdigit():
        e.append(("INVALID_ITEM_ID", f"order_item_id={r['order_item_id']}"))
    if pd.isna(r['order_id']) or not str(r['order_id']).strip().isdigit():
        e.append(("INVALID_ORDER_ID_FK", f"order_id={r['order_id']}"))
    if pd.isna(r['product_id']) or not str(r['product_id']).strip().isdigit():
        e.append(("INVALID_PRODUCT_ID", f"product_id={r['product_id']}"))
    if pd.isna(r['quantity']) or int(r['quantity']) <= 0:
        e.append(("INVALID_QUANTITY", f"quantity={r['quantity']}"))
    return e

def upsert_staging(conn, c, o, i):
    logger = logging.getLogger(__name__)
    cur = conn.cursor()
    q = {"c": [], "o": [], "i": []}
    clean = {"c": [], "o": [], "i": []}

    # 1. Validate customers
    for _, r in c.iterrows():
        errs = []
        if pd.isna(r['customer_id']) or not str(r['customer_id']).strip().isdigit():
            errs.append(("INVALID_CUSTOMER_ID", f"customer_id={r['customer_id']}"))
        if pd.isna(r['email']) or "@" not in str(r['email']):
            errs.append(("INVALID_EMAIL", f"email={r['email']}"))
        if pd.isna(r['created_at']):
            errs.append(("INVALID_CREATED_AT", f"created_at={r['created_at']}"))

        if errs:
            for code, detail in errs:
                q["c"].append((r['customer_id'], r['first_name'], r['last_name'],
                               r['email'], r['created_at'], r['country'], code, detail))
        else:
            clean["c"].append((int(r['customer_id']), r['first_name'].strip(), r['last_name'].strip(),
                               r['email'].strip().lower(), pd.to_datetime(r['created_at']).date(),
                               r['country'].strip()))

    # 2. Validate orders
    for _, r in o.iterrows():
        errs = []
        if pd.isna(r['order_id']) or not str(r['order_id']).strip().isdigit():
            errs.append(("INVALID_ORDER_ID", f"order_id={r['order_id']}"))
        if pd.isna(r['customer_id']) or not str(r['customer_id']).strip().isdigit():
            errs.append(("INVALID_CUSTOMER_ID_FK", f"customer_id={r['customer_id']}"))
        if pd.isna(r['order_date']):
            errs.append(("INVALID_ORDER_DATE", f"order_date={r['order_date']}"))
        if pd.isna(r['total_amount']):
            errs.append(("INVALID_AMOUNT", f"total_amount={r['total_amount']}"))

        if errs:
            for code, detail in errs:
                q["o"].append((r['order_id'], r['customer_id'], r['order_date'],
                               r['status'], r['total_amount'], r['currency'], code, detail))
        else:
            clean["o"].append((int(r['order_id']), int(r['customer_id']),
                               pd.to_datetime(r['order_date']).date(),
                               r['status'].strip().lower(), float(r['total_amount']),
                               r['currency'].strip().upper()))

    # 3. Validate order items
    for _, r in i.iterrows():
        errs = []
        if pd.isna(r['order_item_id']) or not str(r['order_item_id']).strip().isdigit():
            errs.append(("INVALID_ITEM_ID", f"order_item_id={r['order_item_id']}"))
        if pd.isna(r['order_id']) or not str(r['order_id']).strip().isdigit():
            errs.append(("INVALID_ORDER_ID_FK", f"order_id={r['order_id']}"))
        if pd.isna(r['product_id']) or not str(r['product_id']).strip().isdigit():
            errs.append(("INVALID_PRODUCT_ID", f"product_id={r['product_id']}"))
        if pd.isna(r['quantity']) or int(r['quantity']) <= 0:
            errs.append(("INVALID_QUANTITY", f"quantity={r['quantity']}"))

        if errs:
            for code, detail in errs:
                q["i"].append((r['order_item_id'], r['order_id'], r['product_id'],
                               r['product_name'], r['category'], r['quantity'],
                               r['unit_price'], r['total_price'], code, detail))
        else:
            clean["i"].append((int(r['order_item_id']), int(r['order_id']), int(r['product_id']),
                               r['product_name'].strip(), r['category'].strip(),
                               int(r['quantity']), float(r['unit_price']), float(r['total_price'])))

    # 4. Insert quarantine
    for table, rows in q.items():
        if not rows: continue
        if table == "c":
            execute_values(cur, "INSERT INTO qtn_customers(customer_id,first_name,last_name,email,created_at,country,error_code,error_detail) VALUES %s", rows)
        elif table == "o":
            execute_values(cur, "INSERT INTO qtn_orders(order_id,customer_id,order_date,status,total_amount,currency,error_code,error_detail) VALUES %s", rows)
        else:
            execute_values(cur, "INSERT INTO qtn_order_items(order_item_id,order_id,product_id,product_name,category,quantity,unit_price,total_price,error_code,error_detail) VALUES %s", rows)
        logger.warning(f"Quarantined {len(rows)} rows in qtn_{table}")

    # 5. Upsert clean
    for table, rows in clean.items():
        if not rows: continue
        if table == "c":
            execute_values(cur, """INSERT INTO stg_customers(customer_id,first_name,last_name,email,created_at,country) VALUES %s ON CONFLICT(customer_id) DO UPDATE SET first_name=EXCLUDED.first_name,last_name=EXCLUDED.last_name,email=EXCLUDED.email,created_at=EXCLUDED.created_at,country=EXCLUDED.country""", rows)
        elif table == "o":
            execute_values(cur, """INSERT INTO stg_orders(order_id,customer_id,order_date,status,total_amount,currency) VALUES %s ON CONFLICT(order_id) DO UPDATE SET customer_id=EXCLUDED.customer_id,order_date=EXCLUDED.order_date,status=EXCLUDED.status,total_amount=EXCLUDED.total_amount,currency=EXCLUDED.currency""", rows)
        else:
            execute_values(cur, """INSERT INTO stg_order_items(order_item_id,order_id,product_id,product_name,category,quantity,unit_price,total_price) VALUES %s ON CONFLICT(order_item_id) DO UPDATE SET order_id=EXCLUDED.order_id,product_id=EXCLUDED.product_id,product_name=EXCLUDED.product_name,category=EXCLUDED.category,quantity=EXCLUDED.quantity,unit_price=EXCLUDED.unit_price,total_price=EXCLUDED.total_price""", rows)
        logger.info(f"Upserted {len(rows)} clean rows to stg_{table}")

    conn.commit()
    cur.close()

def rebuild_dims_fact(conn):
    cur = conn.cursor()
    cur.execute("""
    TRUNCATE dim_customer;
    INSERT INTO dim_customer(customer_id, first_name, last_name, email, created_at, country, region)
    SELECT customer_id, first_name, last_name, email, created_at, country,
      CASE WHEN country IN ('USA','Canada') THEN 'North America'
           WHEN country IN ('UK','Germany','France') THEN 'Europe'
           WHEN country IN ('Australia') THEN 'APAC' ELSE 'Other' END
    FROM stg_customers;
    
    TRUNCATE dim_product;
    INSERT INTO dim_product(product_id, product_name, category, current_price)
    SELECT product_id, product_name, category, unit_price
    FROM (SELECT product_id, product_name, category, unit_price,
                 ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY unit_price DESC) AS rn
          FROM stg_order_items) x WHERE rn = 1;
    
    TRUNCATE dim_date;
    INSERT INTO dim_date(date_key, year, month, day, year_month, day_name, is_weekend)
    SELECT dk, EXTRACT(year FROM dk)::int, EXTRACT(month FROM dk)::int, EXTRACT(day FROM dk)::int,
           TO_CHAR(dk, 'YYYY-MM'), TO_CHAR(dk, 'Day'),
           CASE WHEN EXTRACT(isodow FROM dk) IN (6,7) THEN true ELSE false END
    FROM (SELECT GENERATE_SERIES((SELECT MIN(order_date) FROM stg_orders),
                                 (SELECT MAX(order_date) FROM stg_orders), '1 day')::date AS dk) s;
    
    TRUNCATE fact_order_items;
    INSERT INTO fact_order_items(order_item_id, order_id, customer_id, product_id, order_date, status, currency, quantity, unit_price, total_price, year, month, year_month)
    SELECT i.order_item_id, o.order_id, o.customer_id, i.product_id, o.order_date, o.status, o.currency,
           i.quantity, i.unit_price, i.total_price, d.year, d.month, d.year_month
    FROM stg_order_items i
    JOIN stg_orders o ON i.order_id = o.order_id
    JOIN dim_date d ON o.order_date = d.date_key
    WHERE o.status = 'completed';
    """)
    conn.commit()
    cur.close()
    logging.getLogger(__name__).info("Dims+fact rebuilt")

def main():
    cfg=load_config(Path(__file__).parent/"config.yaml")
    logger=setup_logging(cfg["logging"]["file"],cfg["logging"]["level"])
    logger.info("="*60+"\nIngestion run")
    try:
        c,o,i=load_csvs(cfg)
        dates=pd.to_datetime(o["order_date"]).dt.date.unique().tolist()
        fx=fetch_fx_rates(cfg,dates)
        conn=get_db_connection(cfg)
        upsert_staging(conn,c,o,i)
        rebuild_dims_fact(conn)
        conn.close()
        logger.info("Done")
    except Exception as e:
        logger.exception(f"Failed: {e}"); sys.exit(1)

if __name__=="__main__": main()
