import numpy as np
import pandas as pd


def generate_credit_default_data(num_clients=1000, random_seed=42):
    rng = np.random.default_rng(random_seed)
    data = {"client_id": [f"CLI_{i+1:06d}" for i in range(num_clients)], "LIMIT_BAL": rng.integers(10000, 500000, num_clients), "AGE": rng.integers(21, 76, num_clients), "EDUCATION": rng.integers(1, 5, num_clients), "MARRIAGE": rng.integers(1, 4, num_clients)}
    for i in [0, 2, 3, 4, 5, 6]:
        data[f"PAY_{i}"] = rng.integers(-2, 5, num_clients)
    for i in range(1, 7):
        utilization = rng.beta(2, 3, num_clients)
        data[f"BILL_AMT{i}"] = np.round(data["LIMIT_BAL"] * utilization, -2)
        data[f"PAY_AMT{i}"] = np.round(data[f"BILL_AMT{i}"] * rng.uniform(0, .7, num_clients), -2)
    score = 1.2 * (data["PAY_0"] > 1) + .3 * sum((data[f"PAY_{i}"] > 0) for i in [2, 3, 4, 5, 6]) + rng.normal(0, .7, num_clients)
    data["default_next_month"] = (score > 1.4).astype(int)
    frame = pd.DataFrame(data)
    return frame, {"dataset_name": "Synthetic credit risk", "total_records": len(frame), "default_rate": float(frame["default_next_month"].mean()), "synthetic": True}
