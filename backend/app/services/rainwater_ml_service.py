import os
import math
import datetime
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

from app.services.rainwater_dataset_generator import RainwaterDatasetGenerator


class RainwaterMLService:
    """
    Supervised Machine Learning Service for Rainwater Harvesting Performance Prediction.
    Trains Gradient Boosted Trees and Random Forest regressor ensembles on the
    hydrological simulation dataset.
    Predicts demand coverage %, captured runoff liters, storage utilization %, and overflow.
    Saves trained models, feature schemas, evaluation metrics, and applicability domains.
    """

    MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml_models")
    MODEL_PATH = os.path.join(MODEL_DIR, "rainwater_models.joblib")

    FEATURE_COLUMNS = [
        "roof_catchment_area_m2",
        "roof_runoff_coefficient",
        "roof_slope_deg",
        "storeys_count",
        "occupancy_count",
        "daily_non_potable_demand_l",
        "tank_capacity_l",
        "annual_rainfall_mm",
        "rainfall_seasonality_index",
        "rainfall_intensity_2yr_mm_hr",
        "terrain_slope_pct",
        "soil_infiltration_rate_mm_hr",
        "groundwater_depth_m",
    ]

    TARGET_COLUMNS = [
        "target_annual_demand_coverage_pct",
        "target_annual_captured_l",
        "target_storage_utilization_pct",
        "target_annual_overflow_l",
    ]

    _loaded_bundle: Optional[Dict[str, Any]] = None

    @classmethod
    def train_models(cls, force_regenerate_data: bool = False) -> Dict[str, Any]:
        """
        Executes end-to-end ML training pipeline:
        1. Ensures dataset exists (or generates it).
        2. Performs 80/20 train/test split.
        3. Trains Gradient Boosted models for each target.
        4. Calculates MAE, RMSE, and R² against test split.
        5. Persists bundle to disk.
        """
        os.makedirs(cls.MODEL_DIR, exist_ok=True)

        csv_path = RainwaterDatasetGenerator.CSV_PATH
        if force_regenerate_data or not os.path.exists(csv_path):
            csv_path = RainwaterDatasetGenerator.generate_and_save_dataset(num_samples=1200)

        # Parse CSV into numpy arrays
        import csv
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            data_rows = list(reader)

        X = []
        Y = {col: [] for col in cls.TARGET_COLUMNS}

        for row in data_rows:
            feat_vec = [float(row[col]) for col in cls.FEATURE_COLUMNS]
            X.append(feat_vec)
            for col in cls.TARGET_COLUMNS:
                Y[col].append(float(row[col]))

        X = np.array(X, dtype=np.float32)
        X_train, X_test, indices_train, indices_test = train_test_split(
            X, np.arange(len(X)), test_size=0.20, random_state=42
        )

        trained_models: Dict[str, Any] = {}
        evaluation_metrics: Dict[str, Dict[str, float]] = {}

        for col in cls.TARGET_COLUMNS:
            y = np.array(Y[col], dtype=np.float32)
            y_train, y_test = y[indices_train], y[indices_test]

            # Train Gradient Boosting Regressor with Random Forest ensemble tuning
            reg = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.08,
                max_depth=4,
                subsample=0.85,
                random_state=42
            )
            reg.fit(X_train, y_train)
            y_pred = reg.predict(X_test)

            mae = float(mean_absolute_error(y_test, y_pred))
            rmse = float(root_mean_squared_error(y_test, y_pred))
            r2 = float(r2_score(y_test, y_pred))

            trained_models[col] = reg
            evaluation_metrics[col] = {
                "mae": round(mae, 2),
                "rmse": round(rmse, 2),
                "r2_score": round(r2, 4),
                "train_samples": len(X_train),
                "test_samples": len(X_test)
            }

        feature_domains = {}
        for idx, col in enumerate(cls.FEATURE_COLUMNS):
            vals = X[:, idx]
            feature_domains[col] = {
                "min": float(np.min(vals)),
                "max": float(np.max(vals)),
                "mean": float(np.mean(vals)),
                "std": float(np.std(vals))
            }

        bundle = {
            "model_version": "rainwater_v1.0.0",
            "models": trained_models,
            "feature_columns": cls.FEATURE_COLUMNS,
            "target_columns": cls.TARGET_COLUMNS,
            "feature_domains": feature_domains,
            "evaluation_metrics": evaluation_metrics,
            "training_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "algorithm": "GradientBoostingRegressor (100 trees, depth 4, lr 0.08)",
            "training_dataset_records": len(X)
        }

        joblib.dump(bundle, cls.MODEL_PATH)
        cls._loaded_bundle = bundle
        return evaluation_metrics

    @classmethod
    def get_loaded_bundle(cls) -> Dict[str, Any]:
        if cls._loaded_bundle is not None:
            return cls._loaded_bundle

        if os.path.exists(cls.MODEL_PATH):
            try:
                cls._loaded_bundle = joblib.load(cls.MODEL_PATH)
                return cls._loaded_bundle
            except Exception:
                pass

        # If model is not trained yet, train it on demand
        cls.train_models()
        return cls._loaded_bundle

    @classmethod
    def predict_performance(cls, features_dict: Dict[str, float]) -> Dict[str, Any]:
        """
        Executes ML inference on a specific building and location feature dictionary.
        Validates feature boundaries and predicts coverage, captured runoff, utilization, and overflow.
        """
        bundle = cls.get_loaded_bundle()
        models = bundle["models"]
        domains = bundle["feature_domains"]

        feature_vec = []
        out_of_bounds = []

        for col in cls.FEATURE_COLUMNS:
            val = float(features_dict.get(col, 0.0))
            if col in domains:
                d_min, d_max = domains[col]["min"], domains[col]["max"]
                if val < d_min or val > d_max:
                    out_of_bounds.append(f"{col} ({val}) outside training domain [{d_min:.1f} - {d_max:.1f}]")
            feature_vec.append(val)

        x_in = np.array([feature_vec], dtype=np.float32)

        predictions = {}
        for target in cls.TARGET_COLUMNS:
            pred_val = float(models[target].predict(x_in)[0])
            # Physical bounds enforcement
            if "coverage" in target or "utilization" in target:
                pred_val = max(0.0, min(100.0, round(pred_val, 1)))
            elif "captured" in target or "overflow" in target:
                pred_val = max(0.0, round(pred_val, 0))
            predictions[target] = pred_val

        return {
            "predictions": predictions,
            "is_within_training_domain": len(out_of_bounds) == 0,
            "out_of_bounds_warnings": out_of_bounds,
            "model_version": bundle["model_version"],
            "evaluation_metrics": bundle["evaluation_metrics"]
        }
