from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os

# Define tickers here or move to a config file or Variable
TICKERS = ["AAPL", "MSFT", "TSLA", "TWLO"]

# Load env vars (assumes they're passed into Docker container)
env_vars = {
  "GCS_BUCKET_NAME": os.getenv("GCS_BUCKET_NAME", "test-bucket"),
  "PROJECT_ID": os.getenv("PROJECT_ID", "test-project"),
  "MODELS_DIR": os.getenv("MODELS_DIR", "models"),
  "BEST_MODEL_DIR": os.getenv("BEST_MODEL_DIR", "models/best"),
  "MODEL_RUNS_DIR": os.getenv("MODEL_RUNS_DIR", "models/runs"),
  "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/app/.gcp/test-credentials.json"),
  "WANDB_API_KEY": os.getenv("WANDB_API_KEY", "test-key"),
}

# Filter out None values
env_vars = {k: v for k, v in env_vars.items() if v is not None}

# Debug function to print environment variables
def debug_env_vars(**context):
    print("=== Environment Variables in DAG ===")
    for key, value in env_vars.items():
        print(f"{key}: {value}")
    print("=== End Environment Variables ===")
    return "Environment variables logged"

default_args = {
  "owner": "airflow",
  "retries": 0,
  "retry_delay": timedelta(minutes=5),
}

with DAG(
  dag_id="stock_forecast_daily",
  default_args=default_args,
  description="Train stock forecast model for multiple tickers",
  schedule="*/15 * * * *",  # every 15 minutes
  start_date=datetime(2024, 6, 1),
  catchup=False,
) as dag:

  # Debug task to show environment variables
  debug_task = PythonOperator(
      task_id="debug_env_vars",
      python_callable=debug_env_vars,
  )

  for ticker in TICKERS:
      train_task = BashOperator(
          task_id=f"train_model_{ticker.lower()}",
          bash_command=f"python3 /app/src/train_model.py --ticker {ticker} --period 1y --forecast_periods 14",
          env=env_vars,
      )
      debug_task >> train_task
