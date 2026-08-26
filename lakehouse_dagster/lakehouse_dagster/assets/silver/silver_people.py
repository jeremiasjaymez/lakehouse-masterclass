from dagster import asset


@asset
def silver_people(bronze_people):
    df = bronze_people.copy()
    df["name_upper"] = df["name"].str.upper()
    return df
