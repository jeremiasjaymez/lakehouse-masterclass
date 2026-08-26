from dagster import ScheduleDefinition

from lakehouse_dagster.jobs import etl_job

daily_etl_schedule = ScheduleDefinition(job=etl_job, cron_schedule="0 6 * * *")
