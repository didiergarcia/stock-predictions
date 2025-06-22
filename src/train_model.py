import datetime
import yfinance as yf
import pandas as pd
import pickle
import os
import wandb
import argparse
import json
from prophet import Prophet
from sklearn.metrics import mean_absolute_error
from google.cloud import storage
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from google.oauth2 import service_account

load_dotenv()
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME") 
PROJECT_ID = os.getenv("PROJECT_ID")
MODELS_DIR = os.getenv("MODELS_DIR")
BEST_MODEL_DIR = os.getenv("BEST_MODEL_DIR")
MODEL_RUNS_DIR = os.getenv("MODEL_RUNS_DIR")
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Debug: Print the credentials path
print(f"CREDENTIALS_PATH: {CREDENTIALS_PATH}")
print(f"File exists: {os.path.exists(CREDENTIALS_PATH) if CREDENTIALS_PATH else 'CREDENTIALS_PATH is None'}")

credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
client = storage.Client(project=PROJECT_ID, credentials=credentials)
bucket = client.bucket(BUCKET_NAME)

def upload_to_gcs(data: pd.DataFrame, ticker: str, period: str):
  """
  Uploads the data to GCS.
  """
  blob = bucket.blob(f"{ticker}/{period}.csv")
  data.to_csv(blob.open("w"), index=False)


def load_data(ticker: str, period: str = "6mo"):
  """
  Loads data from Yahoo Finance for a given ticker and period.
  """
  data = yf.download(ticker, period=period, group_by='ticker', interval='1d', auto_adjust=True)

  if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.droplevel(0)

  data = data.reset_index()
  data = data.rename(columns={"Date": "ds"})

  if "Close" not in data.columns:
    raise ValueError("Close price column not found in data")

  data = data.rename(columns={"Close": "y"})
  return data[["ds", "y"]]


def train_model(data: pd.DataFrame):
  """
  Trains a Prophet model on the data.
  """
  model = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=True)
  model.fit(data)
  return model

def predict(model, periods: int = 7):
  """
  Predicts the next n periods of the data.
  """
  future = model.make_future_dataframe(periods=periods)
  forecast = model.predict(future)
  return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods)

def get_actuals(data: pd.DataFrame, periods: int = 7):
  """
  Gets the actual values for the next n periods.
  """
  return data.tail(periods)

def evaluate(preds: pd.DataFrame, actuals: pd.DataFrame):
  """
  Evaluates the model by calculating the mean absolute error.
  """
  return mean_absolute_error(actuals["y"], preds["yhat"])


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--ticker", type=str, required=True)
  parser.add_argument("--period", type=str, default="6mo")
  parser.add_argument("--forecast_periods", type=int, default=7)
  args = parser.parse_args()

  wandb.login(key=os.getenv("WANDB_API_KEY"))
  wandb.init(project="stock-forecast", config={
      "ticker": args.ticker,
      "period": args.period,
      "predict_days": args.forecast_periods
  })

  print(f"Training model for {args.ticker} with period {args.period} for prediction of {args.forecast_periods} periods (days)")
  run_id = wandb.util.generate_id()
  timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
  run_name = f"{args.ticker}/{args.ticker}-{args.period}-{args.forecast_periods}-{timestamp}-{run_id}"
  wandb.run.name = run_name
  print(f"Run name: {run_name}")
  wandb.run.save(glob_str=f"models/{run_name}/*")

  print("Loading data...")
  data = load_data(args.ticker, args.period)
  train_df = data[:-args.forecast_periods]
  actuals = get_actuals(data, args.forecast_periods)
  print(f"Loaded {len(data)} rows of data")

  model = train_model(train_df)
  print("Model trained")

  preds = predict(model, args.forecast_periods)
  mae = evaluate(preds, actuals)
  plt.plot(actuals["ds"], actuals["y"], label="Actual")
  plt.plot(preds["ds"], preds["yhat"], label="Predicted")
  plt.title(f"{args.ticker} Forecast")
  plt.legend()
  wandb.log({"forecast_plot": wandb.Image(plt)})
  plt.close()
  wandb.log({"mae": mae})
  print(f"Mean Absolute Error: {mae}")

  # Save model locally
  os.makedirs(f"models/{run_name}", exist_ok=True)
  model_path = f"models/{run_name}/model.pkl"
  with open(model_path, "wb") as f:
    pickle.dump(model, f)

  # Save model and mae to GCS
  blob_model = bucket.blob(f"models/runs/{run_name}/model.pkl")
  blob_model.upload_from_string(pickle.dumps(model))
  blob_mae = bucket.blob(f"models/runs/{run_name}/mae.json")
  blob_mae.upload_from_string(json.dumps({"mae": mae}))

  artifact = wandb.Artifact(f"{args.ticker}_model", type="model")
  artifact.add_file(model_path)
  wandb.log_artifact(artifact)

  blob = bucket.blob(f"models/best/{args.ticker}/metadata.json")
  if blob.exists():
    content = blob.download_as_text()
    best_mae = json.loads(content)["mae"]
    print(f"Best model found for {args.ticker} with MAE: {best_mae}")
  else:
    best_mae = float("inf")
    print(f"No best model found for {args.ticker}")

  if mae < best_mae:
    print(f"New best model found for {args.ticker} with MAE: {mae}")
    blob = bucket.blob(f"models/best/{args.ticker}/metadata.json")
    blob.upload_from_string(json.dumps({"mae": mae, "path": blob_model.name, "wandb_run_id": wandb.run.id, "wandb_run_name": wandb.run.name, "wandb_run_url": wandb.run.url}))
    wandb.log({"gcp_path": blob_model.name})
    print(f"Uploaded new best model for {args.ticker} with MAE: {mae}")
  else:
    print(f"Current model for {args.ticker} with MAE: {mae} does not beat the best model with MAE: {best_mae}")
  
  wandb.finish()
