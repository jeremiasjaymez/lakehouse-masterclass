from dagster import asset


@asset
def gold_people(silver_people):
    df = silver_people.copy()
    df["record_source"] = "dagster"
    return df
