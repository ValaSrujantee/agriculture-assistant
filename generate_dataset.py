"""
Dataset generator for Crop Recommendation Dataset.
Creates a realistic agricultural dataset based on established agronomic benchmarks.
"""

import os
import random
import pandas as pd

# Define crop agronomic profiles (mean and std dev for each feature)
CROP_PROFILES = {
    "rice": {
        "N": (80, 15), "P": (48, 10), "K": (40, 8),
        "temperature": (24, 3.5), "humidity": (82, 5), "ph": (6.4, 0.5), "rainfall": (1800, 300),
        "season": "Kharif"
    },
    "wheat": {
        "N": (118, 12), "P": (58, 8), "K": (42, 6),
        "temperature": (18, 3.0), "humidity": (58, 6), "ph": (6.7, 0.4), "rainfall": (480, 80),
        "season": "Rabi"
    },
    "maize": {
        "N": (78, 14), "P": (48, 10), "K": (20, 5),
        "temperature": (23, 4.0), "humidity": (65, 7), "ph": (6.2, 0.6), "rainfall": (700, 120),
        "season": "Kharif"
    },
    "cotton": {
        "N": (118, 15), "P": (46, 12), "K": (19, 5),
        "temperature": (24, 3.5), "humidity": (80, 6), "ph": (6.9, 0.5), "rainfall": (800, 150),
        "season": "Kharif"
    },
    "sugarcane": {
        "N": (145, 18), "P": (70, 12), "K": (65, 10),
        "temperature": (28, 4.0), "humidity": (75, 8), "ph": (6.8, 0.6), "rainfall": (1600, 250),
        "season": "Annual"
    },
    "chickpea": {
        "N": (40, 10), "P": (68, 12), "K": (80, 12),
        "temperature": (19, 3.0), "humidity": (17, 4), "ph": (7.3, 0.5), "rainfall": (420, 70),
        "season": "Rabi"
    },
    "groundnut": {
        "N": (25, 8), "P": (48, 10), "K": (42, 8),
        "temperature": (26, 3.5), "humidity": (62, 7), "ph": (6.5, 0.5), "rainfall": (620, 100),
        "season": "Kharif"
    },
    "soybean": {
        "N": (35, 10), "P": (62, 10), "K": (44, 8),
        "temperature": (25, 3.0), "humidity": (72, 6), "ph": (6.6, 0.4), "rainfall": (850, 120),
        "season": "Kharif"
    },
    "potato": {
        "N": (130, 15), "P": (75, 12), "K": (90, 12),
        "temperature": (17, 3.0), "humidity": (68, 7), "ph": (5.8, 0.5), "rainfall": (520, 80),
        "season": "Rabi"
    },
    "tomato": {
        "N": (105, 15), "P": (58, 10), "K": (85, 12),
        "temperature": (22, 3.5), "humidity": (64, 7), "ph": (6.4, 0.5), "rainfall": (600, 100),
        "season": "Kharif"
    },
    "banana": {
        "N": (100, 15), "P": (75, 10), "K": (50, 8),
        "temperature": (27, 3.0), "humidity": (80, 5), "ph": (6.0, 0.5), "rainfall": (1600, 200),
        "season": "Annual"
    },
    "coffee": {
        "N": (101, 14), "P": (28, 7), "K": (30, 6),
        "temperature": (25, 2.5), "humidity": (58, 6), "ph": (6.8, 0.4), "rainfall": (1580, 220),
        "season": "Annual"
    },
    "watermelon": {
        "N": (99, 14), "P": (18, 5), "K": (50, 8),
        "temperature": (26, 3.0), "humidity": (88, 4), "ph": (6.5, 0.4), "rainfall": (500, 80),
        "season": "Zaid"
    },
    "mustard": {
        "N": (68, 12), "P": (42, 8), "K": (38, 7),
        "temperature": (18, 3.0), "humidity": (55, 6), "ph": (6.8, 0.4), "rainfall": (380, 60),
        "season": "Rabi"
    },
    "pigeonpea": {
        "N": (21, 6), "P": (68, 10), "K": (20, 5),
        "temperature": (28, 4.0), "humidity": (48, 8), "ph": (5.7, 0.6), "rainfall": (750, 120),
        "season": "Kharif"
    },
    "jute": {
        "N": (78, 12), "P": (46, 9), "K": (40, 7),
        "temperature": (25, 3.0), "humidity": (80, 5), "ph": (6.7, 0.4), "rainfall": (1740, 250),
        "season": "Kharif"
    }
}

def generate_crop_dataset(output_path, samples_per_crop=100):
    random.seed(42)
    rows = []

    for crop_name, params in CROP_PROFILES.items():
        for _ in range(samples_per_crop):
            n = max(5, int(random.gauss(params["N"][0], params["N"][1])))
            p = max(5, int(random.gauss(params["P"][0], params["P"][1])))
            k = max(5, int(random.gauss(params["K"][0], params["K"][1])))
            temp = round(max(5.0, min(45.0, random.gauss(params["temperature"][0], params["temperature"][1]))), 2)
            hum = round(max(10.0, min(99.0, random.gauss(params["humidity"][0], params["humidity"][1]))), 2)
            ph = round(max(3.5, min(9.5, random.gauss(params["ph"][0], params["ph"][1]))), 2)
            rain = round(max(150.0, min(3500.0, random.gauss(params["rainfall"][0], params["rainfall"][1]))), 2)
            season = params["season"]

            rows.append({
                "N": n,
                "P": p,
                "K": k,
                "temperature": temp,
                "humidity": hum,
                "ph": ph,
                "rainfall": rain,
                "season": season,
                "label": crop_name
            })

    df = pd.DataFrame(rows)
    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Dataset successfully created at {output_path} with {len(df)} rows across {len(CROP_PROFILES)} crops.")
    return df

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "data", "crop_data.csv")
    generate_crop_dataset(out)
