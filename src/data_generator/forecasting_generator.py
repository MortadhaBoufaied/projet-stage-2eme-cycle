import numpy as np
import pandas as pd


def generate_retail_forecasting_data(num_stores=2, num_products=2, num_days=120, start_date="2025-01-01", random_seed=42):
    rng = np.random.default_rng(random_seed)
    rows = []
    for s in range(num_stores):
        for p in range(num_products):
            for day, date in enumerate(pd.date_range(start_date, periods=num_days)):
                promo = int(rng.random() < .15)
                units = max(0, round(100 + 15*np.sin(2*np.pi*day/7) + 20*promo + rng.normal(0, 6)))
                rows.append({"date": date, "store_id": f"STORE_{s+1:03d}", "product_id": f"PROD_{p+1:03d}", "category": "Grocery", "region": "North", "units_sold": units, "inventory_level": max(0, 500-units), "promotions_holidays": promo, "weather_conditions": "Sunny"})
    frame = pd.DataFrame(rows)
    return frame, {"dataset_name": "Synthetic retail demand", "total_records": len(frame), "synthetic": True}
