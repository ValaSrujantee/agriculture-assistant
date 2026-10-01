"""
Model Training Script for Smart Agriculture Assistant.
Trains a Decision Tree Classifier as the primary crop recommendation model,
compares with a Random Forest benchmark, computes metrics and feature importances,
and serializes artifacts with joblib.
"""
import os
import json
import datetime
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, f1_score

from config import (
    CROP_DATA_PATH,
    MODEL_PATH,
    LABEL_ENCODER_PATH,
    METADATA_PATH,
    MODEL_DIR
)


def train_crop_model(data_path=CROP_DATA_PATH, save_dir=MODEL_DIR):
    """
    Loads dataset, preprocesses features, trains Decision Tree model,
    evaluates against Random Forest benchmark, and saves artifacts.
    """
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Model Training Pipeline...")
    
    # 1. Load CSV
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset file not found at: {data_path}. Run generate_dataset.py first.")
    
    df = pd.read_csv(data_path)
    print(f"Loaded dataset: {len(df)} rows, {len(df.columns)} columns.")

    # 2. Validate columns
    required_features = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
    target_col = "label"

    for col in required_features + [target_col]:
        if col not in df.columns:
            raise ValueError(f"Missing required column in dataset: '{col}'")

    # 3. Clean missing / invalid values
    initial_len = len(df)
    df = df.dropna(subset=required_features + [target_col])
    if len(df) < initial_len:
        print(f"Dropped {initial_len - len(df)} rows with missing values.")

    X = df[required_features]
    y_raw = df[target_col].astype(str).str.lower().str.strip()

    # 4. Encode categorical target labels
    le = LabelEncoder()
    y = le.fit_transform(y_raw)
    class_names = list(le.classes_)
    print(f"Target classes ({len(class_names)} crops): {', '.join(class_names)}")

    # 5. Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Dataset split: {len(X_train)} training samples, {len(X_test)} testing samples.")

    # 6. Train Primary Model: Decision Tree Classifier
    dt_model = DecisionTreeClassifier(
        criterion="gini",
        max_depth=15,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42
    )
    dt_model.fit(X_train, y_train)

    # 7. Train Benchmark: Random Forest Classifier
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        random_state=42
    )
    rf_model.fit(X_train, y_train)

    # 8. Evaluate Models
    dt_preds = dt_model.predict(X_test)
    rf_preds = rf_model.predict(X_test)

    dt_acc = accuracy_score(y_test, dt_preds)
    rf_acc = accuracy_score(y_test, rf_preds)
    dt_f1 = f1_score(y_test, dt_preds, average="weighted")
    rf_f1 = f1_score(y_test, rf_preds, average="weighted")

    # 5-fold cross validation on Decision Tree
    cv_scores = cross_val_score(dt_model, X, y, cv=5)

    print(f"\n================ Model Performance Evaluation ================")
    print(f"Primary Model (Decision Tree) Test Accuracy : {dt_acc * 100:.2f}%")
    print(f"Primary Model (Decision Tree) Weighted F1   : {dt_f1 * 100:.2f}%")
    print(f"5-Fold Cross Validation Accuracy            : {cv_scores.mean() * 100:.2f}% (+/- {cv_scores.std() * 100:.2f}%)")
    print(f"Benchmark (Random Forest) Test Accuracy    : {rf_acc * 100:.2f}%")
    print(f"==============================================================\n")

    # 9. Feature Importances
    importances = dt_model.feature_importances_
    feat_importance_dict = {
        feat: round(float(imp), 4)
        for feat, imp in sorted(zip(required_features, importances), key=lambda x: x[1], reverse=True)
    }
    print(f"Decision Tree Feature Importances:")
    for feat, imp in feat_importance_dict.items():
        print(f"  • {feat:<12}: {imp * 100:6.2f}%")

    # 10. Save Artifacts using Joblib
    os.makedirs(save_dir, exist_ok=True)
    joblib.dump(dt_model, MODEL_PATH)
    joblib.dump(le, LABEL_ENCODER_PATH)
    print(f"Saved primary model -> {MODEL_PATH}")
    print(f"Saved label encoder -> {LABEL_ENCODER_PATH}")

    # 11. Save Comprehensive Model Metadata
    metadata = {
        "model_type": "DecisionTreeClassifier",
        "algorithm": "Decision Tree (CART)",
        "parameters": dt_model.get_params(),
        "trained_at": datetime.datetime.now().isoformat(),
        "features": required_features,
        "classes": class_names,
        "total_samples": len(df),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "metrics": {
            "test_accuracy": round(float(dt_acc), 4),
            "test_f1_score": round(float(dt_f1), 4),
            "cv_accuracy_mean": round(float(cv_scores.mean()), 4),
            "cv_accuracy_std": round(float(cv_scores.std()), 4),
            "benchmark_rf_accuracy": round(float(rf_acc), 4),
            "benchmark_rf_f1": round(float(rf_f1), 4)
        },
        "feature_importances": feat_importance_dict,
        "description": "Decision Tree model trained to recommend suitable crops from soil NPK, temperature, humidity, pH, and rainfall."
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved model metadata -> {METADATA_PATH}")

    return metadata


if __name__ == "__main__":
    train_crop_model()
