import os
import pandas as pd
import logging

def save_to_excel(data, filename, folder="output"):
    if not data or not isinstance(data, list):
        logging.warning("Empty or invalid data. Skipping save.")
        return
    os.makedirs(folder, exist_ok=True)
    df = pd.DataFrame(data)
    path = os.path.join(folder, filename)
    df.to_excel(path, index=False)
    logging.info(f"Saved {len(df)} rows → {path}")
