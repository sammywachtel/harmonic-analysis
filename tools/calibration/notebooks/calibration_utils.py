#!/usr/bin/env python3
"""
Calibration Utilities for Harmonic Analysis

This module contains all the helper functions for the advanced 4-stage calibration pipeline.
Follows the music-alg-3a-calibration.md specification.

Stages:
1. Platt scaling (logistic) - global bias correction
2. Isotonic regression - non-linear shape correction
3. Per-category bucket models - variance control
4. Uncertainty-aware adjustment - confidence down-weighting
"""

import pandas as pd
import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import log_loss
from scipy.optimize import minimize_scalar
import sys
import os
import warnings

# Suppress sklearn warnings about small sample sizes in calibration context
warnings.filterwarnings("ignore", "The least populated class in y has only")
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(project_root)

from src.harmonic_analysis.services.calibration_service import CalibrationService


def stage0_data_hygiene(df):
    """Stage 0: Data hygiene and preparation."""
    print("🧹 Stage 0: Data Hygiene")

    # Deduplication by (name, category) - simple approach
    initial_count = len(df)
    df_clean = df.drop_duplicates(subset=['name', 'category'], keep='first')
    dedupe_count = len(df_clean)
    print(f"  ✅ Deduplication: {initial_count} → {dedupe_count} rows ({initial_count - dedupe_count} duplicates removed)")

    # Minimum evidence filter
    # For harmony: at least 2 chords, for melody: at least 6 notes
    before_filter = len(df_clean)

    def meets_evidence_threshold(row):
        if row.get('routing_features', {}).get('is_melody', False):
            return row.get('routing_features', {}).get('note_count', 0) >= 6
        else:
            return row.get('routing_features', {}).get('chord_count', 0) >= 2

    df_clean = df_clean[df_clean.apply(meets_evidence_threshold, axis=1)]
    after_filter = len(df_clean)
    print(f"  ✅ Evidence filter: {before_filter} → {after_filter} rows ({before_filter - after_filter} too sparse)")

    # Winsorize targets and clip model outputs
    for col in ['expected_functional_confidence', 'expected_modal_confidence']:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].clip(0, 1)

    for col in ['functional_confidence', 'modal_confidence']:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].clip(1e-4, 1-1e-4)

    print(f"  ✅ Value clamping: confidences in [1e-4, 1-1e-4]")

    # Create stratified folds by category
    df_clean = df_clean.copy()
    df_clean['fold'] = -1

    categories = df_clean['category'].fillna('unknown')

    # Check category counts to determine appropriate number of folds
    category_counts = categories.value_counts()
    min_category_count = category_counts.min()

    # Adjust n_splits based on minimum category count
    if min_category_count < 5:
        n_splits = max(2, min_category_count)  # At least 2 folds if possible
        print(f"  ⚠️ Small category detected (min count: {min_category_count}), using {n_splits} folds instead of 5")
    else:
        n_splits = 5

    if n_splits > 1:
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

        for fold_idx, (_, test_idx) in enumerate(skf.split(df_clean, categories)):
            df_clean.iloc[test_idx, df_clean.columns.get_loc('fold')] = fold_idx
    else:
        # If only 1 sample in smallest category, assign random folds
        print(f"  ⚠️ Using random fold assignment due to singleton categories")
        np.random.seed(42)
        df_clean['fold'] = np.random.randint(0, 5, size=len(df_clean))

    print(f"  ✅ Stratified {n_splits if n_splits > 1 else 'random'}-folds created by category")
    print(f"  📊 Final dataset: {len(df_clean)} rows")

    return df_clean


def stage1_platt_scaling(df, track='functional', bucket='GLOBAL'):
    """Stage 1: Platt scaling (logistic calibration) for bias correction."""
    print(f"⚖️ Stage 1: Platt Scaling - {track} {bucket}")

    # Get data for this track
    if track == 'functional':
        expected_col = 'expected_functional_confidence'
        actual_col = 'functional_confidence'
    elif track == 'modal':
        expected_col = 'expected_modal_confidence'
        actual_col = 'modal_confidence'
    else:
        print(f"  ⚠️ Skipping {track} - not implemented")
        return {'a': 1.0, 'b': 0.0}

    # Filter data
    if bucket != 'GLOBAL':
        mask = (df['bucket'] == bucket) & df[expected_col].notnull() & df[actual_col].notnull()
    else:
        mask = df[expected_col].notnull() & df[actual_col].notnull()

    if mask.sum() < 10:
        print(f"  ⚠️ Insufficient data ({mask.sum()} rows), using identity")
        return {'a': 1.0, 'b': 0.0}

    df_subset = df[mask].copy()

    # Prepare data for logistic regression (Platt scaling)
    y_true = df_subset[expected_col].values
    y_prob = df_subset[actual_col].values

    # Convert to binary problem for multiple attempts
    # We'll try different quantile splits and pick the most stable
    best_params = {'a': 1.0, 'b': 0.0}
    best_loss = float('inf')

    # Suppress sklearn warnings for small sample sizes in Platt scaling
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", "The least populated class in y has only")

        for threshold in [0.3, 0.5, 0.7]:
            try:
                y_binary = (y_true > threshold).astype(int)
                if y_binary.sum() < 2 or (1 - y_binary).sum() < 2:
                    continue  # Skip if too imbalanced (need at least 2 per class)

                # Create feature matrix (logit of probabilities)
                epsilon = 1e-6
                y_prob_clipped = np.clip(y_prob, epsilon, 1 - epsilon)
                X = np.log(y_prob_clipped / (1 - y_prob_clipped)).reshape(-1, 1)

                # Fit logistic regression
                lr = LogisticRegression(fit_intercept=True, random_state=42)
                lr.fit(X, y_binary)

                # Extract Platt scaling parameters
                a = lr.coef_[0][0]
                b = lr.intercept_[0]

                # Compute loss on continuous targets using MSE (more appropriate than Brier score for continuous)
                calibrated_probs = 1 / (1 + np.exp(-(a * X.ravel() + b)))
                loss = np.mean((y_true - calibrated_probs) ** 2)

                if loss < best_loss:
                    best_loss = loss
                    best_params = {'a': float(a), 'b': float(b)}

            except Exception as e:
                continue

    print(f"  ✅ Platt params: a={best_params['a']:.3f}, b={best_params['b']:.3f}, loss={best_loss:.4f}")
    return best_params


def stage2_isotonic_regression(df, track='functional', bucket='GLOBAL', platt_params=None):
    """Stage 2: Isotonic regression for shape correction."""
    print(f"📈 Stage 2: Isotonic Regression - {track} {bucket}")

    # Get data for this track
    if track == 'functional':
        expected_col = 'expected_functional_confidence'
        actual_col = 'functional_confidence'
    elif track == 'modal':
        expected_col = 'expected_modal_confidence'
        actual_col = 'modal_confidence'
    else:
        print(f"  ⚠️ Skipping {track} - not implemented")
        return {'x': [0.0, 1.0], 'y': [0.0, 1.0]}

    # Filter data
    if bucket != 'GLOBAL':
        mask = (df['bucket'] == bucket) & df[expected_col].notnull() & df[actual_col].notnull()
    else:
        mask = df[expected_col].notnull() & df[actual_col].notnull()

    if mask.sum() < 20:
        print(f"  ⚠️ Insufficient data ({mask.sum()} rows), using identity")
        return {'x': [0.0, 1.0], 'y': [0.0, 1.0]}

    df_subset = df[mask].copy()

    # Apply Stage 1 calibration first if provided
    y_prob = df_subset[actual_col].values
    if platt_params and platt_params.get('a', 1.0) != 1.0:
        a, b = platt_params['a'], platt_params['b']
        epsilon = 1e-6
        y_prob = np.clip(y_prob, epsilon, 1 - epsilon)
        logit = np.log(y_prob / (1 - y_prob))
        y_prob = 1 / (1 + np.exp(-(a * logit + b)))

    y_true = df_subset[expected_col].values

    # Fit isotonic regression
    iso_reg = IsotonicRegression(out_of_bounds='clip')
    iso_calibrated = iso_reg.fit_transform(y_prob, y_true)

    # Extract breakpoints (limit to reasonable number)
    unique_x = np.unique(y_prob)
    if len(unique_x) > 15:
        # Sample breakpoints to keep mapping compact
        indices = np.linspace(0, len(unique_x) - 1, 15, dtype=int)
        unique_x = unique_x[indices]

    # Get corresponding y values
    y_values = [iso_reg.transform([x])[0] for x in unique_x]

    # Ensure monotonicity and add boundary points
    x_points = [0.0] + list(unique_x) + [1.0]
    y_points = [y_values[0]] + y_values + [y_values[-1]]

    print(f"  ✅ Isotonic mapping: {len(x_points)} breakpoints")
    return {'x': x_points, 'y': y_points}


def stage4_uncertainty_learning(df, track='functional', bucket='GLOBAL'):
    """Stage 4: Learn uncertainty adjustment parameters."""
    print(f"🎯 Stage 4: Uncertainty Learning - {track} {bucket}")

    # Get data for this track
    if track == 'functional':
        expected_col = 'expected_functional_confidence'
        actual_col = 'functional_confidence'
    elif track == 'modal':
        expected_col = 'expected_modal_confidence'
        actual_col = 'modal_confidence'
    else:
        print(f"  ⚠️ Skipping {track} - not implemented")
        return {'alpha': 0.5, 'lambda_max': 0.25}

    # Filter data
    if bucket != 'GLOBAL':
        mask = (df['bucket'] == bucket) & df[expected_col].notnull() & df[actual_col].notnull()
    else:
        mask = df[expected_col].notnull() & df[actual_col].notnull()

    if mask.sum() < 30:
        print(f"  ⚠️ Insufficient data ({mask.sum()} rows), using defaults")
        return {'alpha': 0.5, 'lambda_max': 0.25}

    df_subset = df[mask].copy()

    # Compute uncertainty scores using the calibration service
    service = CalibrationService()
    uncertainties = []
    for _, row in df_subset.iterrows():
        features = row.get('routing_features', {})
        uncertainty = service.compute_uncertainty(track, features)
        uncertainties.append(uncertainty)

    uncertainties = np.array(uncertainties)
    y_true = df_subset[expected_col].values
    y_prob = df_subset[actual_col].values

    # Optimize alpha to minimize mean squared error (MSE) - more appropriate for continuous targets
    def objective(alpha):
        lambda_max = 0.25  # Fixed for now
        lambda_vals = np.minimum(alpha * uncertainties, lambda_max)
        adjusted_probs = (1 - lambda_vals) * y_prob + lambda_vals * 0.5
        return np.mean((y_true - adjusted_probs) ** 2)

    try:
        result = minimize_scalar(objective, bounds=(0.0, 2.0), method='bounded')
        best_alpha = result.x
        best_loss = result.fun
    except:
        best_alpha = 0.5
        best_loss = objective(0.5)

    print(f"  ✅ Uncertainty params: alpha={best_alpha:.3f}, lambda_max=0.25, loss={best_loss:.4f}")
    return {'alpha': float(best_alpha), 'lambda_max': 0.25}


def analyze_calibration_needs(df):
    """Analyze where calibration is most needed"""

    # Calculate errors
    func_mask = df['expected_functional_confidence'].notnull() & df['functional_confidence'].notnull()
    modal_mask = df['expected_modal_confidence'].notnull() & df['modal_confidence'].notnull()

    func_errors = df.loc[func_mask, 'functional_confidence'] - df.loc[func_mask, 'expected_functional_confidence']
    modal_errors = df.loc[modal_mask, 'modal_confidence'] - df.loc[modal_mask, 'expected_modal_confidence']

    # Statistics
    stats = {
        'functional': {
            'mean_error': func_errors.mean(),
            'mae': func_errors.abs().mean(),
            'std': func_errors.std(),
            'overconfident_pct': (func_errors > 0.1).mean() * 100,
            'underconfident_pct': (func_errors < -0.1).mean() * 100,
        },
        'modal': {
            'mean_error': modal_errors.mean(),
            'mae': modal_errors.abs().mean(),
            'std': modal_errors.std(),
            'overconfident_pct': (modal_errors > 0.1).mean() * 100,
            'underconfident_pct': (modal_errors < -0.1).mean() * 100,
        }
    }

    return stats, func_errors, modal_errors


def show_calibration_examples(df):
    """Show specific examples of good and bad calibration"""

    # Calculate errors for functional
    func_mask = df['expected_functional_confidence'].notnull() & df['functional_confidence'].notnull()
    df_func = df[func_mask].copy()
    df_func['error'] = (df_func['functional_confidence'] - df_func['expected_functional_confidence']).abs()

    # Calculate errors for modal
    modal_mask = df['expected_modal_confidence'].notnull() & df['modal_confidence'].notnull()
    df_modal = df[modal_mask].copy()
    df_modal['error'] = (df_modal['modal_confidence'] - df_modal['expected_modal_confidence']).abs()

    print('=' * 80)
    print('FUNCTIONAL ANALYSIS EXAMPLES')
    print('=' * 80)

    print('\n✅ GOOD CALIBRATION (error < 0.1):')
    good_func = df_func[df_func['error'] < 0.1].head(3)
    for _, row in good_func.iterrows():
        print(f"  Chords: {row['chords_str'][:30]}...")
        print(f"    Expected: {row['expected_functional_confidence']:.2f}, Actual: {row['functional_confidence']:.2f}, Error: {row['error']:.3f}")
        print()

    print('\n❌ BAD CALIBRATION (error > 0.2):')
    bad_func = df_func[df_func['error'] > 0.2].head(3)
    for _, row in bad_func.iterrows():
        print(f"  Chords: {row['chords_str'][:30]}...")
        print(f"    Expected: {row['expected_functional_confidence']:.2f}, Actual: {row['functional_confidence']:.2f}, Error: {row['error']:.3f}")
        direction = '📈 overconfident' if row['functional_confidence'] > row['expected_functional_confidence'] else '📉 underconfident'
        print(f"    Issue: {direction}")
        print()

    print('=' * 80)
    print('MODAL ANALYSIS EXAMPLES')
    print('=' * 80)

    print('\n✅ GOOD CALIBRATION (error < 0.1):')
    good_modal = df_modal[df_modal['error'] < 0.1].head(3)
    for _, row in good_modal.iterrows():
        print(f"  Chords: {row['chords_str'][:30]}...")
        print(f"    Expected: {row['expected_modal_confidence']:.2f}, Actual: {row['modal_confidence']:.2f}, Error: {row['error']:.3f}")
        print()

    print('\n❌ BAD CALIBRATION (error > 0.2):')
    bad_modal = df_modal[df_modal['error'] > 0.2].head(3)
    for _, row in bad_modal.iterrows():
        print(f"  Chords: {row['chords_str'][:30]}...")
        print(f"    Expected: {row['expected_modal_confidence']:.2f}, Actual: {row['modal_confidence']:.2f}, Error: {row['error']:.3f}")
        direction = '📈 overconfident' if row['modal_confidence'] > row['expected_modal_confidence'] else '📉 underconfident'
        print(f"    Issue: {direction}")
        print()
