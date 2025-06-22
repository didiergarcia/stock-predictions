from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import os

# Define tickers here or move to a config file or Variable
TICKERS = ["AAPL", "MSFT", "TSLA", "TWLO"]

# Load env vars (assumes they're passed into Docker container)
env_vars = {
  "GCS_BUCKET_NAME": os.getenv("GCS_BUCKET_NAME"),
  "PROJECT_ID": os.getenv("PROJECT_ID"),
  "MODELS_DIR": os.getenv("MODELS_DIR", "models"),
  "BEST_MODEL_DIR": os.getenv("BEST_MODEL_DIR", "models/best"),
  "MODEL_RUNS_DIR": os.getenv("MODEL_RUNS_DIR", "models/runs"),
  "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
  "WANDB_API_KEY": os.getenv("WANDB_API_KEY"),
}

default_args = {
  "owner": "airflow",
  "retries": 1,
  "retry_delay": timedelta(minutes=5),
}

with DAG(
  dag_id="stock_forecast_daily",
  default_args=default_args,
  description="Train stock forecast model for multiple tickers",
  schedule_interval="0 6 * * *",  # daily at 6AM UTC
  start_date=datetime(2024, 6, 1),
  catchup=False,
) as dag:

  for ticker in TICKERS:
      BashOperator(
          task_id=f"train_model_{ticker.lower()}",
          bash_command=f"python3 /app/src/train_model.py --ticker {ticker} --period 1y --periods 14",
          env=env_vars,
      )
