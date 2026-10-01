"""
Dataset Generator for Smart Agriculture Assistant.
Generates a realistic, agronomic crop recommendation dataset based on ICAR/FAO agro-climatic standards.
Covers 22 crops with realistic Gaussian distributions of N, P, K, temperature, humidity, pH, rainfall, and season.
"""
import os
import random
import pandas as pd
import numpy as np
from pathlib import Path

# Fix seed for reproducibility
np.random.seed(42)
random.seed(42)

# Agronomic parameter profiles (mean, std) for each crop
# Features: [N, P, K, temperature, humidity, ph, rainfall, primary_season]
CROP_PROFILES = {
    "rice": {
        "N": (80, 15), "P": (48, 10), "K": (40, 8),
        "temperature": (24.0, 2.5), "humidity": (82.0, 5.0),
        "ph": (6.4, 0.4), "rainfall": (230.0, 30.0),
        "season": "Kharif"
    },
    "wheat": {
        "N": (105, 18), "P": (55, 12), "K": (40, 8),
        "temperature": (17.5, 2.8), "humidity": (55.0, 6.0),
        "ph": (6.6, 0.4), "rainfall": (65.0, 15.0),
        "season": "Rabi"
    },
    "maize": {
        "N": (78, 16), "P": (48, 10), "K": (20, 5),
        "temperature": (22.5, 3.2), "humidity": (65.0, 7.0),
        "ph": (6.5, 0.5), "rainfall": (85.0, 18.0),
        "season": "Kharif"
    },
    "chickpea": {
        "N": (40, 10), "P": (68, 12), "K": (80, 10),
        "temperature": (18.8, 2.5), "humidity": (45.0, 6.0),
        "ph": (7.3, 0.4), "rainfall": (80.0, 15.0),
        "season": "Rabi"
    },
    "kidneybeans": {
        "N": (20, 8), "P": (68, 12), "K": (20, 5),
        "temperature": (20.0, 2.5), "humidity": (56.0, 5.5),
        "ph": (5.7, 0.3), "rainfall": (105.0, 20.0),
        "season": "Kharif"
    },
    "pigeonpeas": {
        "N": (21, 6), "P": (68, 10), "K": (20, 5),
        "temperature": (27.8, 3.0), "humidity": (48.0, 6.0),
        "ph": (5.8, 0.5), "rainfall": (150.0, 25.0),
        "season": "Kharif"
    },
    "mothbeans": {
        "N": (22, 6), "P": (48, 10), "K": (20, 5),
        "temperature": (28.2, 3.0), "humidity": (53.0, 6.0),
        "ph": (6.8, 0.5), "rainfall": (52.0, 12.0),
        "season": "Kharif"
    },
    "mungbean": {
        "N": (21, 6), "P": (48, 10), "K": (20, 5),
        "temperature": (28.5, 2.8), "humidity": (85.5, 4.0),
        "ph": (6.7, 0.4), "rainfall": (48.0, 10.0),
        "season": "Zaid"
    },
    "blackgram": {
        "N": (40, 10), "P": (68, 10), "K": (19, 5),
        "temperature": (30.0, 3.0), "humidity": (65.0, 6.0),
        "ph": (7.1, 0.4), "rainfall": (68.0, 12.0),
        "season": "Kharif"
    },
    "lentil": {
        "N": (19, 6), "P": (68, 12), "K": (19, 5),
        "temperature": (24.5, 3.0), "humidity": (64.8, 6.0),
        "ph": (6.9, 0.5), "rainfall": (45.0, 10.0),
        "season": "Rabi"
    },
    "pomegranate": {
        "N": (19, 6), "P": (19, 5), "K": (40, 8),
        "temperature": (21.8, 3.0), "humidity": (90.1, 4.0),
        "ph": (6.4, 0.4), "rainfall": (108.0, 15.0),
        "season": "All Season"
    },
    "banana": {
        "N": (100, 15), "P": (75, 12), "K": (50, 10),
        "temperature": (27.4, 2.5), "humidity": (80.4, 5.0),
        "ph": (6.0, 0.4), "rainfall": (104.0, 20.0),
        "season": "All Season"
    },
    "mango": {
        "N": (20, 6), "P": (27, 6), "K": (30, 6),
        "temperature": (31.2, 3.0), "humidity": (50.1, 5.5),
        "ph": (5.8, 0.5), "rainfall": (95.0, 20.0),
        "season": "All Season"
    },
    "grapes": {
        "N": (23, 7), "P": (132, 15), "K": (200, 15),
        "temperature": (23.8, 3.5), "humidity": (81.9, 4.0),
        "ph": (6.0, 0.4), "rainfall": (69.6, 12.0),
        "season": "All Season"
    },
    "watermelon": {
        "N": (99, 15), "P": (17, 5), "K": (50, 8),
        "temperature": (25.6, 3.0), "humidity": (85.2, 4.0),
        "ph": (6.5, 0.4), "rainfall": (50.8, 10.0),
        "season": "Zaid"
    },
    "apple": {
        "N": (21, 6), "P": (134, 15), "K": (200, 15),
        "temperature": (22.6, 3.0), "humidity": (92.3, 3.5),
        "ph": (5.9, 0.4), "rainfall": (112.7, 18.0),
        "season": "All Season"
    },
    "orange": {
        "N": (20, 6), "P": (16, 4), "K": (10, 3),
        "temperature": (22.8, 3.0), "humidity": (92.2, 3.5),
        "ph": (7.0, 0.5), "rainfall": (110.5, 18.0),
        "season": "All Season"
    },
    "papaya": {
        "N": (50, 10), "P": (60, 10), "K": (50, 8),
        "temperature": (33.7, 3.0), "humidity": (92.4, 3.5),
        "ph": (6.7, 0.4), "rainfall": (142.6, 25.0),
        "season": "All Season"
    },
    "coconut": {
        "N": (22, 6), "P": (17, 5), "K": (31, 6),
        "temperature": (27.4, 2.5), "humidity": (94.8, 3.0),
        "ph": (6.0, 0.4), "rainfall": (175.7, 30.0),
        "season": "All Season"
    },
    "cotton": {
        "N": (118, 18), "P": (46, 10), "K": (20, 5),
        "temperature": (24.0, 3.0), "humidity": (79.8, 5.0),
        "ph": (6.9, 0.5), "rainfall": (80.4, 18.0),
        "season": "Kharif"
    },
    "jute": {
        "N": (78, 15), "P": (46, 10), "K": (40, 8),
        "temperature": (25.0, 2.8), "humidity": (79.6, 5.0),
        "ph": (6.7, 0.4), "rainfall": (174.7, 28.0),
        "season": "Kharif"
    },
    "coffee": {
        "N": (101, 15), "P": (28, 8), "K": (30, 6),
        "temperature": (25.5, 2.5), "humidity": (58.9, 5.5),
        "ph": (6.8, 0.4), "rainfall": (158.1, 25.0),
        "season": "All Season"
    },
    "mustard": {
        "N": (75, 14), "P": (45, 10), "K": (38, 8),
        "temperature": (16.5, 2.8), "humidity": (48.0, 6.0),
        "ph": (7.2, 0.4), "rainfall": (38.0, 8.0),
        "season": "Rabi"
    },
    "barley": {
        "N": (65, 12), "P": (38, 8), "K": (35, 7),
        "temperature": (15.0, 2.5), "humidity": (46.0, 5.5),
        "ph": (7.4, 0.4), "rainfall": (35.0, 8.0),
        "season": "Rabi"
    },
    "sugarcane": {
        "N": (135, 20), "P": (58, 12), "K": (85, 15),
        "temperature": (28.0, 3.5), "humidity": (75.0, 6.0),
        "ph": (6.8, 0.5), "rainfall": (160.0, 25.0),
        "season": "All Season"
    },
    "groundnut": {
        "N": (35, 8), "P": (55, 10), "K": (45, 8),
        "temperature": (26.5, 3.0), "humidity": (58.0, 6.0),
        "ph": (6.5, 0.4), "rainfall": (68.0, 14.0),
        "season": "Kharif"
    },
    "soybean": {
        "N": (42, 10), "P": (62, 12), "K": (40, 8),
        "temperature": (25.2, 2.8), "humidity": (72.0, 6.0),
        "ph": (6.6, 0.4), "rainfall": (92.0, 18.0),
        "season": "Kharif"
    },
    "potato": {
        "N": (110, 18), "P": (60, 12), "K": (120, 18),
        "temperature": (17.0, 2.5), "humidity": (68.0, 6.0),
        "ph": (5.8, 0.4), "rainfall": (55.0, 12.0),
        "season": "Rabi"
    },
    "tomato": {
        "N": (95, 16), "P": (58, 12), "K": (90, 15),
        "temperature": (23.5, 3.0), "humidity": (62.0, 6.0),
        "ph": (6.4, 0.4), "rainfall": (68.0, 14.0),
        "season": "Rabi"
    },
    "millet": {
        "N": (50, 12), "P": (30, 8), "K": (25, 6),
        "temperature": (31.0, 3.5), "humidity": (42.0, 6.0),
        "ph": (7.0, 0.5), "rainfall": (42.0, 10.0),
        "season": "Kharif"
    }
}

def generate_crop_dataset(samples_per_crop=100, output_path=None):
    """Generate agronomic dataset and save to CSV."""
    records = []
    
    for crop, profile in CROP_PROFILES.items():
        for _ in range(samples_per_crop):
            # Sample features with bounded gaussian noise
            n = max(0, int(np.random.normal(profile["N"][0], profile["N"][1])))
            p = max(0, int(np.random.normal(profile["P"][0], profile["P"][1])))
            k = max(0, int(np.random.normal(profile["K"][0], profile["K"][1])))
            
            temp = max(5.0, round(float(np.random.normal(profile["temperature"][0], profile["temperature"][1])), 2))
            humidity = min(100.0, max(10.0, round(float(np.random.normal(profile["humidity"][0], profile["humidity"][1])), 2)))
            ph = min(9.5, max(3.5, round(float(np.random.normal(profile["ph"][0], profile["ph"][1])), 2)))
            rainfall = max(10.0, round(float(np.random.normal(profile["rainfall"][0], profile["rainfall"][1])), 2))
            
            # Season assignment with slight variance for adaptable crops
            season = profile["season"]
            
            records.append({
                "N": n,
                "P": p,
                "K": k,
                "temperature": temp,
                "humidity": humidity,
                "ph": ph,
                "rainfall": rainfall,
                "season": season,
                "label": crop
            })
            
    df = pd.DataFrame(records)
    # Shuffle dataset
    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    
    if output_path is None:
        output_path = Path(__file__).resolve().parent / "crop_data.csv"
        
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} samples across {len(CROP_PROFILES)} crops -> {output_path}")
    return df

if __name__ == "__main__":
    generate_crop_dataset()
