from pathlib import Path

import pandas as pd
from dagster import asset

REPO_ROOT = Path(__file__).parents[4]


@asset
def bronze_people():
    df = pd.read_csv(REPO_ROOT / "data" / "bronze" / "people.csv")
    return df
