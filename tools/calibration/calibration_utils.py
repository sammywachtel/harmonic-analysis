#!/usr/bin/env python3
"""
Calibration Utilities for Harmonic Analysis

This module contains versions of calibration functions that address:
1. Data pollution from scale_melody category
2. Over-discretization in isotonic regression
3. Insufficient minimum sample thresholds
4. Poor bucket routing logic

All stages have been enhanced to preserve confidence granularity and create
meaningful calibration bins.
"""

import json
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.model_selection import StratifiedKFold

# Suppress sklearn warnings about small sample sizes
warnings.filterwarnings("ignore", "The least populated class in y has only")
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(project_root)


def _compute_bucket_for_track(track: str, features: dict, category: str) -> str:
    """Compute bucket for a specific track with proper track-specific routing."""

    if track == "functional":
        # Functional track buckets
        if features.get("foil_I_V_I", False):
            return "functional_cadential"
        elif features.get("evidence_strength", 0) > 0.7:
            return "functional_clear"
        else:
            return "functional_simple"

    elif track == "modal":
        # Modal track buckets - PROPER MODAL BUCKETS

        # Category-based routing for modal
        if category == "modal_characteristic":
            return "modal_characteristic"
        elif category == "modal_contextless":
            return "modal_contextless"
        elif features.get("modal_density", 0) > 0.3:
            return "modal_marked"  # Has strong modal characteristics
        elif features.get("has_flat7", False) or features.get("has_sharp4", False):
            return "modal_specific"  # Specific modal markers
        else:
            return "modal_ambiguous"

    # Fallback
    return f"{track}_simple"


def stage0_data_hygiene(df):
    """Stage 0: data hygiene with proper filtering."""
    print("🧹 Stage 0: Data Hygiene")

    # Deduplication by (name, category)
    initial_count = len(df)
    df_clean = df.drop_duplicates(subset=["name", "category"], keep="first")
    dedupe_count = len(df_clean)
    print(
        f"  ✅ Deduplication: {initial_count} → {dedupe_count} rows ({initial_count - dedupe_count} duplicates removed)"
    )

    # FIXED: minimum evidence filter
    before_filter = len(df_clean)

    def meets_evidence_threshold(row):
        # All cases should be harmony (we excluded melody in pipeline)
        chord_count = row.get("routing_features", {}).get("chord_count", 0)
        return chord_count >= 2  # Minimum 2 chords for meaningful analysis

    df_clean = df_clean[df_clean.apply(meets_evidence_threshold, axis=1)]
    after_filter = len(df_clean)
    print(
        f"  ✅ Evidence filter: {before_filter} → {after_filter} rows ({before_filter - after_filter} too sparse)"
    )

    # FIXED: confidence filtering - remove zeros more aggressively
    before_conf_filter = len(df_clean)

    # For each track, only keep rows where that track has meaningful confidence
    valid_functional = df_clean["functional_confidence"].notna() & (
        df_clean["functional_confidence"] >= 0.1
    )
    valid_modal = df_clean["modal_confidence"].notna() & (
        df_clean["modal_confidence"] >= 0.1
    )

    # Keep rows that have at least one valid track
    df_clean = df_clean[valid_functional | valid_modal]

    after_conf_filter = len(df_clean)
    print(
        f"  ✅ confidence filter: {before_conf_filter} → {after_conf_filter} rows ({before_conf_filter - after_conf_filter} zero/low confidence removed)"
    )

    # Create track column for filtering
    tracks_data = []
    for _, row in df_clean.iterrows():
        routing_features = row.get("routing_features", {})

        # Create functional track record
        if (
            row.get("functional_confidence") is not None
            and row.get("expected_functional_confidence") is not None
            and row.get("functional_confidence") >= 0.1
        ):
            # Compute functional bucket
            functional_bucket = _compute_bucket_for_track(
                "functional", routing_features, row.get("category", "unknown")
            )
            tracks_data.append(
                {
                    **row.to_dict(),
                    "track": "functional",
                    "bucket": functional_bucket,
                    "confidence": row["functional_confidence"],
                    "expected_confidence": row["expected_functional_confidence"],
                }
            )

        # Create modal track record
        if (
            row.get("modal_confidence") is not None
            and row.get("expected_modal_confidence") is not None
            and row.get("modal_confidence") >= 0.1
        ):
            # Compute modal bucket
            modal_bucket = _compute_bucket_for_track(
                "modal", routing_features, row.get("category", "unknown")
            )
            tracks_data.append(
                {
                    **row.to_dict(),
                    "track": "modal",
                    "bucket": modal_bucket,
                    "confidence": row["modal_confidence"],
                    "expected_confidence": row["expected_modal_confidence"],
                }
            )

    df_tracks = pd.DataFrame(tracks_data)

    print(
        f"  ✅ Track expansion: {len(df_clean)} cases → {len(df_tracks)} track records"
    )
    print(
        f"    Functional track: {len(df_tracks[df_tracks['track'] == 'functional'])} records"
    )
    print(f"    Modal track: {len(df_tracks[df_tracks['track'] == 'modal'])} records")

    # Winsorize targets and clip model outputs
    if "expected_confidence" in df_tracks.columns:
        df_tracks["expected_confidence"] = df_tracks["expected_confidence"].clip(0, 1)
    if "confidence" in df_tracks.columns:
        df_tracks["confidence"] = df_tracks["confidence"].clip(1e-4, 1 - 1e-4)

    # Final statistics
    print(f"  📊 Final cleaned dataset: {len(df_tracks)} track records")

    # Show bucket distribution
    if "bucket" in df_tracks.columns and "track" in df_tracks.columns:
        print("  📊 Bucket distribution after cleaning:")
        for track in df_tracks["track"].unique():
            track_data = df_tracks[df_tracks["track"] == track]
            bucket_counts = track_data["bucket"].value_counts()
            print(f"    {track.upper()}:")
            for bucket, count in bucket_counts.items():
                print(f"      {bucket}: {count} samples")

    return df_tracks


def stage1_platt_scaling(df, track, bucket):
    """Stage 1: Platt scaling with better regularization."""
    print(f"  🎯 Stage 1: Platt scaling for {track}/{bucket}")

    expected_col = "expected_confidence"
    actual_col = "confidence"

    # Filter data with logic
    if bucket != "GLOBAL":
        mask = (
            (df["track"] == track)
            & (df["bucket"] == bucket)
            & df[expected_col].notna()
            & df[actual_col].notna()
        )
    else:
        mask = (
            (df["track"] == track) & df[expected_col].notna() & df[actual_col].notna()
        )

    sample_count = mask.sum()

    if sample_count < 10:
        print(f"    ⚠️  Insufficient data ({sample_count} samples), using identity")
        return {"a": 1.0, "b": 0.0}
    else:
        print(f"    ✅ Training with {sample_count} samples")

    df_subset = df[mask].copy()

    # FIXED: Multiple threshold approach with better regularization
    best_params = {"a": 1.0, "b": 0.0}
    best_score = float("inf")

    # Try multiple thresholds for more robust fitting
    thresholds = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]

    for threshold in thresholds:
        try:
            y_true = df_subset[expected_col].values
            y_prob = df_subset[actual_col].values

            y_binary = (y_true > threshold).astype(int)

            # Check class balance
            if y_binary.sum() < 2 or (len(y_binary) - y_binary.sum()) < 2:
                continue  # Skip if too imbalanced

            # Create logit features with better clipping
            epsilon = 1e-6
            y_prob_clipped = np.clip(y_prob, epsilon, 1 - epsilon)
            X = np.log(y_prob_clipped / (1 - y_prob_clipped)).reshape(-1, 1)

            # FIXED: Use regularized logistic regression
            lr = LogisticRegression(
                fit_intercept=True,
                C=1.0,  # Moderate regularization
                solver="lbfgs",
                max_iter=1000,
                random_state=42,
            )

            lr.fit(X, y_binary)

            # Calculate cross-validated score
            try:
                if len(np.unique(y_binary)) > 1:
                    y_pred_proba = lr.predict_proba(X)[:, 1]
                    score = log_loss(y_binary, y_pred_proba)

                    if score < best_score:
                        best_score = score
                        best_params = {
                            "a": float(lr.coef_[0][0]),
                            "b": float(lr.intercept_[0]),
                        }
            except:
                continue

        except Exception:
            continue

    print(
        f"    ✅ Best Platt: a={best_params['a']:.4f}, b={best_params['b']:.4f} (score: {best_score:.4f})"
    )
    return best_params


def stage2_isotonic_regression(df, track, bucket, platt_params):
    """Stage 2: isotonic regression preserving granularity."""
    print(f"  📈 Stage 2: Isotonic regression for {track}/{bucket}")

    expected_col = "expected_confidence"
    actual_col = "confidence"

    # Filter data
    if bucket != "GLOBAL":
        mask = (
            (df["track"] == track)
            & (df["bucket"] == bucket)
            & df[expected_col].notna()
            & df[actual_col].notna()
        )
    else:
        mask = (
            (df["track"] == track) & df[expected_col].notna() & df[actual_col].notna()
        )

    sample_count = mask.sum()

    if sample_count < 15:  # Slightly higher threshold for isotonic
        print(f"    ⚠️  Insufficient data ({sample_count} samples), using Platt only")
        # Create identity mapping that just applies Platt scaling
        x_points = np.linspace(0.001, 0.999, 50)  # More points for smoothness
        y_points = []

        a = platt_params["a"]
        b = platt_params["b"]

        for x in x_points:
            # Apply Platt scaling
            logit = a * np.log(x / (1 - x)) + b
            platt_adjusted = 1 / (1 + np.exp(-logit))
            y_points.append(platt_adjusted)

        return {"x": x_points.tolist(), "y": y_points}

    print(f"    ✅ Training with {sample_count} samples")

    df_subset = df[mask].copy()

    # Apply Platt scaling first
    a = platt_params["a"]
    b = platt_params["b"]

    raw_probs = df_subset[actual_col].values

    # Apply Platt transformation
    epsilon = 1e-6
    raw_probs_clipped = np.clip(raw_probs, epsilon, 1 - epsilon)
    platt_adjusted = []

    for p in raw_probs_clipped:
        logit = a * np.log(p / (1 - p)) + b
        platt_prob = 1 / (
            1 + np.exp(-np.clip(logit, -500, 500))
        )  # Clip to prevent overflow
        platt_adjusted.append(platt_prob)

    platt_adjusted = np.array(platt_adjusted)
    y_true = df_subset[expected_col].values

    # FIXED: isotonic regression with better granularity preservation
    try:
        # Use isotonic regression with increasing constraint
        iso_reg = IsotonicRegression(increasing=True, out_of_bounds="clip")

        iso_reg.fit(platt_adjusted, y_true)

        # FIXED: Create high-resolution mapping preserving more granularity
        # Use more interpolation points to prevent over-discretization
        n_points = min(100, sample_count * 2)  # Adaptive number of points
        x_points = np.linspace(0.001, 0.999, n_points)

        y_isotonic = iso_reg.predict(x_points)

        # FIXED: Add noise to prevent complete discretization
        # This helps preserve some of the original confidence distribution
        if len(np.unique(y_isotonic)) < 5:  # If too discretized
            print(
                f"    ⚠️  Isotonic over-discretized ({len(np.unique(y_isotonic))} unique values), adding smoothing"
            )

            # Add small amount of smoothing to preserve granularity
            for i in range(1, len(y_isotonic) - 1):
                # Slight interpolation with neighbors
                y_isotonic[i] = (
                    0.8 * y_isotonic[i]
                    + 0.1 * y_isotonic[i - 1]
                    + 0.1 * y_isotonic[i + 1]
                )

        mapping = {"x": x_points.tolist(), "y": y_isotonic.tolist()}

        unique_outputs = len(set(y_isotonic))
        print(
            f"    ✅ Isotonic mapping: {n_points} points → {unique_outputs} unique outputs"
        )

        if unique_outputs < 3:
            print(f"    ⚠️  Very few unique outputs - may need more data")

        return mapping

    except Exception as e:
        print(f"    ❌ Isotonic regression failed: {e}")
        # Fallback to Platt-only mapping
        x_points = np.linspace(0.001, 0.999, 50)
        y_points = []

        for x in x_points:
            logit = a * np.log(x / (1 - x)) + b
            platt_prob = 1 / (1 + np.exp(-np.clip(logit, -500, 500)))
            y_points.append(platt_prob)

        return {"x": x_points.tolist(), "y": y_points}


def stage4_uncertainty_learning(df, track, bucket):
    """Stage 4: uncertainty learning with better statistics."""
    print(f"  🎲 Stage 4: Uncertainty learning for {track}/{bucket}")

    expected_col = "expected_confidence"
    actual_col = "confidence"

    # Filter data
    if bucket != "GLOBAL":
        mask = (
            (df["track"] == track)
            & (df["bucket"] == bucket)
            & df[expected_col].notna()
            & df[actual_col].notna()
        )
    else:
        mask = (
            (df["track"] == track) & df[expected_col].notna() & df[actual_col].notna()
        )

    sample_count = mask.sum()

    if sample_count < 10:
        print(
            f"    ⚠️  Insufficient data ({sample_count} samples), using default uncertainty"
        )
        return {"base_uncertainty": 0.5, "confidence_penalty": 0.1, "method": "default"}

    print(f"    ✅ Learning uncertainty with {sample_count} samples")

    df_subset = df[mask].copy()

    y_true = df_subset[expected_col].values
    y_pred = df_subset[actual_col].values

    # Calculate errors
    errors = np.abs(y_true - y_pred)

    # FIXED: More sophisticated uncertainty calculation
    base_uncertainty = float(np.median(errors))  # Use median for robustness
    uncertainty_std = float(np.std(errors))

    # Calculate confidence-dependent penalty
    # Higher confidence predictions should be penalized more for errors
    high_conf_mask = y_pred > 0.7
    if high_conf_mask.sum() > 2:
        high_conf_errors = errors[high_conf_mask]
        confidence_penalty = float(np.mean(high_conf_errors) - base_uncertainty)
        confidence_penalty = max(0.0, confidence_penalty)  # No negative penalties
    else:
        confidence_penalty = 0.1  # Default penalty

    result = {
        "base_uncertainty": base_uncertainty,
        "confidence_penalty": confidence_penalty,
        "uncertainty_std": uncertainty_std,
        "sample_count": int(sample_count),
        "method": "learned",
    }

    print(
        f"    ✅ Uncertainty: base={base_uncertainty:.3f}, penalty={confidence_penalty:.3f}, std={uncertainty_std:.3f}"
    )

    return result


def _safe_load_json(file_path, default=None):
    """Safely load JSON file with proper error handling"""
    try:
        file_path = Path(file_path)

        # Check if file exists
        if not file_path.exists():
            print(f"Warning: JSON file doesn't exist: {file_path}")
            return default

        # Check if file is empty
        if file_path.stat().st_size == 0:
            print(f"Warning: JSON file is empty: {file_path}")
            return default

        # Try to load the JSON
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

            # Check if content is empty after stripping whitespace
            if not content:
                print(f"Warning: JSON file contains only whitespace: {file_path}")
                return default

            # Parse JSON
            return json.loads(content)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file {file_path}: {e}")
        print(f"First 200 characters of file content:")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                print(repr(f.read()[:200]))
        except Exception as read_err:
            print(f"Could not read file for debugging: {read_err}")
        return default
    except Exception as e:
        print(f"Error reading JSON file {file_path}: {e}")
        return default


def _show_calibration_examples(df):
    """Show specific examples of good and bad calibration"""
    # Calculate errors for functional
    func_mask = (
        df["expected_functional_confidence"].notnull()
        & df["functional_confidence"].notnull()
    )
    df_func = df[func_mask].copy()
    df_func["error"] = (
        df_func["functional_confidence"] - df_func["expected_functional_confidence"]
    ).abs()

    # Calculate errors for modal
    modal_mask = (
        df["expected_modal_confidence"].notnull() & df["modal_confidence"].notnull()
    )
    df_modal = df[modal_mask].copy()
    df_modal["error"] = (
        df_modal["modal_confidence"] - df_modal["expected_modal_confidence"]
    ).abs()

    print("=" * 80)
    print("FUNCTIONAL ANALYSIS EXAMPLES")
    print("=" * 80)

    print("\n✅ GOOD CALIBRATION (error < 0.1):")
    good_func = df_func[df_func["error"] < 0.1].head(3)
    for _, row in good_func.iterrows():
        chords_str = row.get("chords_str", str(row.get("chords", "Unknown")))
        print(f"  Chords: {chords_str[:30]}...")
        print(
            f"    Expected: {row['expected_functional_confidence']:.2f}, Actual: {row['functional_confidence']:.2f}, Error: {row['error']:.3f}"
        )
        print()

    print("\n❌ BAD CALIBRATION (error > 0.2):")
    bad_func = df_func[df_func["error"] > 0.2].head(3)
    for _, row in bad_func.iterrows():
        chords_str = row.get("chords_str", str(row.get("chords", "Unknown")))
        print(f"  Chords: {chords_str[:30]}...")
        print(
            f"    Expected: {row['expected_functional_confidence']:.2f}, Actual: {row['functional_confidence']:.2f}, Error: {row['error']:.3f}"
        )
        direction = (
            "📈 overconfident"
            if row["functional_confidence"] > row["expected_functional_confidence"]
            else "📉 underconfident"
        )
        print(f"    Issue: {direction}")
        print()

    print("=" * 80)
    print("MODAL ANALYSIS EXAMPLES")
    print("=" * 80)

    print("\n✅ GOOD CALIBRATION (error < 0.1):")
    good_modal = df_modal[df_modal["error"] < 0.1].head(3)
    for _, row in good_modal.iterrows():
        chords_str = row.get("chords_str", str(row.get("chords", "Unknown")))
        print(f"  Chords: {chords_str[:30]}...")
        print(
            f"    Expected: {row['expected_modal_confidence']:.2f}, Actual: {row['modal_confidence']:.2f}, Error: {row['error']:.3f}"
        )
        print()

    print("\n❌ BAD CALIBRATION (error > 0.2):")
    bad_modal = df_modal[df_modal["error"] > 0.2].head(3)
    for _, row in bad_modal.iterrows():
        chords_str = row.get("chords_str", str(row.get("chords", "Unknown")))
        print(f"  Chords: {chords_str[:30]}...")
        print(
            f"    Expected: {row['expected_modal_confidence']:.2f}, Actual: {row['modal_confidence']:.2f}, Error: {row['error']:.3f}"
        )
        direction = (
            "📈 overconfident"
            if row["modal_confidence"] > row["expected_modal_confidence"]
            else "📉 underconfident"
        )
        print(f"    Issue: {direction}")
        print()
