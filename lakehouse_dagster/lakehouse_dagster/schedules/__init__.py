# lakehouse_dagster/schedules/__init__.py
from lakehouse_dagster.schedules.etl_schedule import daily_etl_schedule

__all__ = ["daily_etl_schedule"]
