"""How well do height and weight predict each girth? Residual SDs from ANSUR II (task 4.5).

Run from engine/:  uv run python scripts/ansur_sds.py <male.csv> <female.csv>
The CSVs are the public ANSUR II 2012 files (US Army anthropometric survey, public domain), from
https://www.openlab.psu.edu/ansur2/ . They are not kept in git. For each sex and measurement the
script fits measurement = a + b·stature + c·weight + d·BMI by least squares and prints the residual
standard deviation: the uncertainty of a measurement the shopper did not enter.
"""

import csv
import sys

import numpy as np

# Our measurement -> ANSUR II column (millimetres). Notes on the mismatches are in measurements.md.
COLUMNS = {
    "chest_girth": "chestcircumference",
    "waist_girth": "waistcircumference",
    "hip_girth": "buttockcircumference",
    "upper_arm_girth": "bicepscircumferenceflexed",
    "thigh_girth": "thighcircumference",
    "back_length": "waistbacklength",
    "vertical_trunk_girth": "verticaltrunkcircumferenceusa",
}


def load(path):
    with open(path, newline="", encoding="latin-1") as f:
        rows = list(csv.DictReader(f))
    lower = {key: key.lower() for key in rows[0]}
    return [{lower[k]: v for k, v in row.items()} for row in rows]


def residual_sd_cm(rows, column):
    stature = np.array([float(r["stature"]) for r in rows]) / 1000  # mm -> m
    weight = np.array([float(r["weightkg"]) for r in rows]) / 10  # ANSUR II stores 0.1 kg units
    y = np.array([float(r[column]) for r in rows]) / 10  # mm -> cm
    x = np.column_stack([np.ones_like(stature), stature, weight, weight / stature**2])
    coefficients, *_ = np.linalg.lstsq(x, y, rcond=None)
    residuals = y - x @ coefficients
    return float(np.sqrt(residuals @ residuals / (len(y) - x.shape[1]))), float(y.std(ddof=1))


def main():
    male, female = (load(p) for p in sys.argv[1:3])
    print(f"ANSUR II: {len(male)} men, {len(female)} women")
    print("| Measurement | ANSUR II column | men: SD given height+weight / raw SD | women |")
    print("|---|---|---|---|")
    for ours, column in COLUMNS.items():
        cells = []
        for rows in (male, female):
            residual, raw = residual_sd_cm(rows, column)
            cells.append(f"{residual:.2f} / {raw:.2f}")
        print(f"| {ours} | {column} | {cells[0]} | {cells[1]} |")


if __name__ == "__main__":
    main()
