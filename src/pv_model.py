"""pv_model.py

Module for parsing, cleaning, and processing raw PVGIS hourly solar generation data.
"""

from pathlib import Path
import io
import pandas as pd


def load_and_clean_pvgis_data(file_path: str | Path) -> pd.DataFrame:
  """Parses and cleans a raw PVGIS hourly CSV export file, returning a pristine

  numeric DataFrame with a DatetimeIndex.

  Parameters:
  - file_path (str or Path): Path to the raw PVGIS CSV file.

  Returns:
  - pd.DataFrame: Cleaned hourly dataset containing PV power and weather metrics.
  """
  file_path = Path(file_path)

  if not file_path.exists():
    raise FileNotFoundError(f"Raw data file not found at: {file_path}")

  # 1. Read lines and find the header
  with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

  header_idx = None
  for i, line in enumerate(lines):
    if "time" in line.lower() and "," in line and ":" not in line:
      header_idx = i
      break

  if header_idx is None:
    raise ValueError(
        f"Could not locate valid time-series header in {file_path}"
    )

  # 2. Collect valid data lines (skipping header and the units row at header_idx + 1)
  valid_lines = [lines[header_idx]]
  for line in lines[header_idx + 2:]:
    if any(
        term in line for term in ["Month", "Disclaimer", "Averages", "--", "*"]
    ):
      break
    if line.strip():
      valid_lines.append(line)

  # 3. Load into DataFrame
  df = pd.read_csv(io.StringIO("".join(valid_lines)))

  # 4. Parse timestamps and set as index
  if "time" in df.columns:
    df["time"] = pd.to_datetime(
        df["time"].astype(str), format="%Y%m%d:%H%M", errors="coerce"
    )
    df.set_index("time", inplace=True)

  # 5. Convert all data columns to numeric float64
  for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

  # 6. Drop trailing metadata or NaN rows (e.g., footer artifacts)
  df = df.dropna(subset=["P"])

  return df


def save_processed_data(
    df: pd.DataFrame, output_path: str | Path = "../data/processed/pvgis_nordhausen_clean.csv"
) -> None:
  """Saves the cleaned DataFrame to the data/processed directory as a CSV file."""
  output_path = Path(output_path)
  # Ensure the target directory exists
  output_path.parent.mkdir(parents=True, exist_ok=True)
  
  df.to_csv(output_path)
  print(f"Processed PV data successfully saved to: {output_path}")


if __name__ == "__main__":
  # Example execution when run directly as a script
  raw_path = "../data/raw/pvgis_hourly_nordhausen.csv"
  processed_path = "../data/processed/pvgis_nordhausen_clean.csv"
  
  df_clean = load_and_clean_pvgis_data(raw_path)
  save_processed_data(df_clean, processed_path)
  print(df_clean.info())