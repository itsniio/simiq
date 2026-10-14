"""Which masses can Anny reach at a given height? Diagnostic for fit-engine-poc 3.4.

Run from engine/:  uv run python scripts/body_ranges.py
Prints mass (kg) and BMI over Anny's weight, muscle and proportions parameters, with Anny's
phenotype extrapolation switched on so values beyond 1 show what extrapolating would give.
"""

import numpy as np
import torch

from simiq_fit.body import anny_age, height_cm, mass_kg

CASES = [  # sex, age, height parameter (chosen near the failing heights), failing input
    ("female", 21, 0.398, "165.3 cm, 72.7 kg (BMI 26.6)"),
    ("male", 58, 0.5, "173.8 cm, 59.3 kg (BMI 19.6)"),
    ("female", 35, 0.5, "reference"),
    ("male", 35, 0.5, "reference"),
]
WEIGHTS = (0.0, 0.5, 1.0, 1.25, 1.5)
MUSCLES = (0.0, 0.25, 0.5, 0.75, 1.0)
PROPORTIONS = (0.0, 0.5, 1.0)


def main():
    import anny

    model = anny.Anny(extrapolate_phenotypes=True).to(dtype=torch.float32)
    faces = np.asarray(model.faces)
    for sex, age, height, note in CASES:
        print(f"\n## {sex}, {age} years, height parameter {height} ({note})")
        for proportions in PROPORTIONS:
            print(f"\nproportions {proportions}: mass kg / BMI; rows weight, columns muscle")
            print("weight | " + " | ".join(f"m={m}" for m in MUSCLES))
            for weight in WEIGHTS:
                cells = []
                for muscle in MUSCLES:
                    phenotype = dict(
                        gender=1.0 if sex == "female" else 0.0,
                        age=anny_age(age),
                        height=height,
                        weight=weight,
                        muscle=muscle,
                        proportions=proportions,
                    )
                    with torch.no_grad():
                        v = model(phenotype_kwargs=phenotype)["rest_vertices"][0].numpy()
                    h, m = height_cm(v), mass_kg(v, faces)
                    cells.append(f"{m:.1f}/{m / (h / 100) ** 2:.1f} ({h:.0f}cm)")
                print(f"{weight} | " + " | ".join(cells))


if __name__ == "__main__":
    main()
