"""Download and prepare the UCI "Gas Turbine CO and NOx Emission" dataset (id 551).

36,733 hourly sensor aggregates (2011-2015) of a gas turbine in north-western Turkey:
ambient conditions + process parameters (inputs) and the CO / NOx emissions (outputs).
Licensed CC BY 4.0, see https://archive.ics.uci.edu/dataset/551.

Writes `<DATA_DIR>/datasets/gas_turbine/gas_turbine.csv` with the column layout expected by
the `gas_turbine` DataConfig in `backend/datamans/sets.py`:

    year (time col) | AT AP AH AFDP GTEP TIT TAT TEY CDP (9 inputs) | CO NOX (2 outputs)

Usage:  python scripts/prepare_gas_turbine.py [--data-dir ./data]
"""

import argparse
import io
import os
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

URL = "https://archive.ics.uci.edu/static/public/551/gas+turbine+co+and+nox+emission+data+set.zip"
INPUTS = ["AT", "AP", "AH", "AFDP", "GTEP", "TIT", "TAT", "TEY", "CDP"]
OUTPUTS = ["CO", "NOX"]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", default=os.getenv("DATA_DIR", "./data"))
    args = parser.parse_args()

    target = Path(args.data_dir) / "datasets" / "gas_turbine" / "gas_turbine.csv"
    target.parent.mkdir(parents=True, exist_ok=True)

    print("Downloading", URL)
    with urllib.request.urlopen(URL) as resp:
        payload = resp.read()

    frames = []
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        for name in sorted(zf.namelist()):
            if not name.endswith(".csv"):
                continue
            year = int(Path(name).stem.split("_")[-1])
            df = pd.read_csv(zf.open(name))
            df.insert(0, "year", year)
            frames.append(df)
    data = pd.concat(frames, ignore_index=True)[["year"] + INPUTS + OUTPUTS]
    data.to_csv(target, index=False)
    print(f"Wrote {len(data)} rows x {data.shape[1]} cols to {target}")


if __name__ == "__main__":
    main()
