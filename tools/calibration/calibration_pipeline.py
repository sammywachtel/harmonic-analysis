#!/usr/bin/env python3
"""
Confidence Calibration Pipeline Script

This script provides non-notebook access to the enhanced confidence calibration system.
It separates the core functionality from visualization for easier maintenance and automation.

Key improvements:
- Filters invalid track/category combinations (e.g., modal confidence for functional_clear)
- Detects poor data quality and uses identity mappings when correlations are too low
- Prevents calibration degradation by ensuring meaningful calibration targets

Modes of operation:
1. generate - Create baseline and calibration mapping files
2. validate - Run validation and create validation dataframe
3. deploy - Move calibration files to production

Usage:
    python calibration_pipeline.py generate    # Create baseline and mapping
    python calibration_pipeline.py validate    # Validate calibration
    python calibration_pipeline.py deploy      # Deploy to production
    python calibration_pipeline.py all         # Run all stages

"""

import argparse
import datetime
import json
import shutil
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Add project paths
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root / "scripts"))
sys.path.append(str(Path(__file__).parent))

# Import project modules
from harmonic_analysis.dto import AnalysisEnvelope, AnalysisSummary, AnalysisType
from harmonic_analysis.services.calibration_service import CalibrationService
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

# Import calibration utilities
from calibration_utils import (
    stage0_data_hygiene,
    stage1_platt_scaling,
    stage2_isotonic_regression,
    stage4_uncertainty_learning,
)

# Import sklearn for correlation and variance checks
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss

warnings.filterwarnings("ignore", "The least populated class in y has only")


class CalibrationPipeline:
    """
    calibration pipeline that addresses all identified issues:
    - Proper data filtering (exclude problematic categories)
    - Correct bucket naming and routing
    - Improved isotonic regression with better granularity
    - Minimum confidence thresholds
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

        # File paths
        self.calibration_dir = Path(__file__).parent
        self.baseline_path = self.calibration_dir / "confidence_baseline.json"
        self.mapping_path = self.calibration_dir / "calibration_mapping.json"
        self.test_suite_path = (
            project_root / "tests" / "data" / "generated" / "comprehensive-multi-layer-tests.json"
        )
        self.validation_df_path = self.calibration_dir / "calibration_validation_df.json"

        # Define valid track/category combinations to prevent data contamination
        self.valid_combinations = {
            'functional': [
                'functional_cadential', 'functional_clear', 'functional_simple',
                'ambiguous'  # Include ambiguous for functional track
            ],
            'modal': [
                'modal_characteristic', 'modal_contextless', 'modal_marked'
                # Exclude functional_clear and ambiguous for modal track
            ]
        }

    def _log(self, message: str, emoji: str = "📝"):
        if self.verbose:
            print(f"{emoji} {message}")

    def _filter_valid_combinations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter out invalid track/category combinations to prevent data contamination."""
        # Simply filter the existing dataframe to keep only valid track/category combinations
        valid_mask = pd.Series(False, index=df.index)

        for _, row in df.iterrows():
            category = row.get('category', '')
            track = row.get('track', '')

            # Check if this track/category combination is valid
            if track in self.valid_combinations and category in self.valid_combinations[track]:
                valid_mask[row.name] = True

        return df[valid_mask].copy()

    def _check_calibration_viability(self, df: pd.DataFrame, track: str, bucket: str = None) -> bool:
        """Check if calibration is viable for given track/bucket combination."""
        # Filter data
        if bucket:
            mask = (df['track'] == track) & (df['bucket'] == bucket)
        else:
            mask = (df['track'] == track)

        mask = mask & df['expected_confidence'].notna() & df['confidence'].notna()
        df_subset = df[mask]

        if len(df_subset) < 10:
            self._log(f"    ⚠️  Insufficient data ({len(df_subset)} samples) for {track}" +
                     (f"/{bucket}" if bucket else ""))
            return False

        # Check variance
        conf_var = df_subset['confidence'].var()
        expected_var = df_subset['expected_confidence'].var()

        if conf_var < 0.001 or expected_var < 0.001:
            self._log(f"    ⚠️  Insufficient variance (conf: {conf_var:.4f}, expected: {expected_var:.4f}) for {track}" +
                     (f"/{bucket}" if bucket else ""))
            return False

        # Check correlation
        try:
            correlation = np.corrcoef(df_subset['confidence'], df_subset['expected_confidence'])[0, 1]
            self._log(f"    📊 Correlation: {correlation:.3f} for {track}" + (f"/{bucket}" if bucket else ""))

            if abs(correlation) < 0.1:
                self._log(f"    ⚠️  Low correlation ({correlation:.3f}) for {track}" +
                         (f"/{bucket}" if bucket else "") + " - will use identity mapping")
                return False

        except Exception:
            self._log(f"    ⚠️  Could not calculate correlation for {track}" +
                     (f"/{bucket}" if bucket else "") + " - will use identity mapping")
            return False

        return True

    def _run_case(self, service: PatternAnalysisService, case: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run a single test case and extract calibration data."""
        chords = case.get("chords", [])
        profile = case.get("profile", "classical")
        name = case.get("name", case.get("description", "Unnamed"))
        category = case.get("category", "unknown")

        # CRITICAL FIX #1: EXCLUDE PROBLEMATIC CATEGORIES
        excluded_categories = {
            "scale_melody",  # 68% of data, all zeros - pollutes calibration
            "edge_single",   # Too few samples, causes instability
            "edge_repeated", # Too few samples
            "edge_chromatic", # Too few samples
            "edge_enharmonic" # Too few samples
        }

        if category in excluded_categories:
            return None  # Skip these categories entirely

        # Get expectations
        modal_exp = case.get("expected_modal", {})
        func_exp = case.get("expected_functional", {})

        # CRITICAL FIX #2: MINIMUM CONFIDENCE FILTERING
        # Skip cases with zero confidence expectations (they pollute the data)
        expected_modal_conf = modal_exp.get("confidence", 0.0)
        expected_func_conf = func_exp.get("confidence", 0.0)

        # Skip if both expected confidences are below threshold
        MIN_CONFIDENCE = 0.1  # Exclude zero and very low confidence cases
        if expected_modal_conf < MIN_CONFIDENCE and expected_func_conf < MIN_CONFIDENCE:
            return None

        # Handle melody cases (shouldn't happen due to exclusion, but safety check)
        if not chords or len(chords) == 0:
            return None  # Skip melody cases

        # Run analysis
        try:
            result = service.analyze_with_patterns(chords, profile=profile)
        except Exception as e:
            return None

        if not result.primary:
            return None

        # CRITICAL FIX #3: IMPROVED BUCKET ROUTING
        routing_features = self._extract_routing_features_fixed(chords, result, case)

        # Proper track determination
        track = "functional" if result.primary.type.value == "functional" else "modal"

        # Note: Bucket will be computed per track record in data expansion

        # Find functional and modal analyses
        functional_analysis = None
        modal_analysis = None

        if result.primary.type.value == "functional":
            functional_analysis = result.primary
            # Look for modal in alternatives
            for alt in getattr(result, "alternatives", []):
                if alt.type.value == "modal":
                    modal_analysis = alt
                    break
        else:
            modal_analysis = result.primary
            # Look for functional in alternatives
            for alt in getattr(result, "alternatives", []):
                if alt.type.value == "functional":
                    functional_analysis = alt
                    break

        # Extract confidence values with ZERO FILTERING
        func_conf = functional_analysis.confidence if functional_analysis else 0.0
        modal_conf = modal_analysis.confidence if modal_analysis else 0.0

        # Additional zero confidence filtering at extraction level
        if func_conf < MIN_CONFIDENCE:
            func_conf = None
            expected_func_conf = None
        if modal_conf < MIN_CONFIDENCE:
            modal_conf = None
            expected_modal_conf = None

        # Skip if no valid confidences remain
        if func_conf is None and modal_conf is None:
            return None

        return {
            "name": name,
            "category": category,
            "chords": chords,
            "primary_track": track,  # Track of primary analysis
            "routing_features": routing_features,
            "functional_confidence": func_conf,
            "modal_confidence": modal_conf,
            "expected_functional_confidence": expected_func_conf if func_conf is not None else None,
            "expected_modal_confidence": expected_modal_conf if modal_conf is not None else None,
        }

    def _extract_routing_features_fixed(self, chords: List[str], result, case: Dict[str, Any]) -> Dict[str, Any]:
        """routing features extraction with better modal detection."""
        features = {
            "chord_count": len(chords),
            "is_melody": False,
            "evidence_strength": 0.6,
            "outside_key_ratio": 0.0,
            "foil_I_V_I": False,
            "has_flat7": False,
            "has_flat3": False,
            "has_flat6": False,
            "has_sharp4": False,
            "has_flat2": False,
            "has_flat5": False,
            "chord_density": 0.5,
            "category": case.get("category", "unknown"),  # Add category for bucket routing
        }

        # Enhanced modal characteristic detection
        modal_chord_count = 0
        for chord in chords:
            # Check for extended modal characteristics
            chord_lower = chord.lower()
            if any(marker in chord_lower for marker in ["b7", "♭7", "7"]):
                features["has_flat7"] = True
                modal_chord_count += 1
            if any(marker in chord_lower for marker in ["b3", "♭3", "m"]):
                features["has_flat3"] = True
                modal_chord_count += 1
            if any(marker in chord_lower for marker in ["b6", "♭6"]):
                features["has_flat6"] = True
                modal_chord_count += 1
            if any(marker in chord_lower for marker in ["#4", "♯4", "#11"]):
                features["has_sharp4"] = True
                modal_chord_count += 1
            if any(marker in chord_lower for marker in ["b2", "♭2", "b9"]):
                features["has_flat2"] = True
                modal_chord_count += 1

        # Calculate modal density
        features["modal_density"] = modal_chord_count / max(len(chords), 1)

        # Check for cadential patterns (functional indicators)
        if len(chords) >= 3:
            if chords[0] == chords[-1]:  # Same first and last
                features["foil_I_V_I"] = True

        # Extract confidence-based evidence strength
        if result.primary.confidence > 0.8:
            features["evidence_strength"] = 0.8
        elif result.primary.confidence > 0.6:
            features["evidence_strength"] = 0.6
        else:
            features["evidence_strength"] = 0.4

        return features

    def _compute_bucket_fixed(self, track: str, features: Dict[str, Any], case: Dict[str, Any]) -> str:
        """bucket computation with proper modal buckets."""
        category = features.get("category", "unknown")

        if track == "functional":
            # Functional track buckets
            if features.get("foil_I_V_I", False):
                return "functional_cadential"
            elif features.get("evidence_strength", 0) > 0.7:
                return "functional_clear"
            else:
                return "functional_simple"

        elif track == "modal":
            # CRITICAL FIX #4: PROPER MODAL BUCKETS

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

    def generate_baseline_and_mapping(self) -> bool:
        """Generate baseline with data filtering and bucket routing."""
        self._log("🚀 Starting baseline generation and calibration training...")

        # Load test suite
        if not self.test_suite_path.exists():
            self._log(f"❌ Test suite not found: {self.test_suite_path}")
            return False

        with open(self.test_suite_path, "r") as f:
            data = json.load(f)
        test_cases = data.get("test_cases", data) if isinstance(data, dict) else data
        self._log(f"📂 Loaded {len(test_cases)} test cases")

        # Generate baseline with filtering
        self._log("🔄 Generating baseline with confidence filtering...")
        service = PatternAnalysisService(auto_calibrate=False)

        rows = []
        excluded_count = 0
        for i, case in enumerate(test_cases):
            if (i + 1) % 100 == 0:
                self._log(f"  Progress: {i+1}/{len(test_cases)} ({excluded_count} excluded)")

            try:
                row = self._run_case(service, case)
                if row:
                    rows.append(row)
                else:
                    excluded_count += 1
            except Exception as e:
                self._log(f"  ⚠️ Failed case {i}: {e}")
                excluded_count += 1
                continue

        self._log(f"✅ Generated {len(rows)} baseline rows ({excluded_count} excluded)")

        # ANALYSIS OF EXCLUSIONS
        category_counts = {}
        for case in test_cases:
            cat = case.get("category", "unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        self._log("📊 Category exclusion analysis:")
        excluded_categories = {"scale_melody", "edge_single", "edge_repeated", "edge_chromatic", "edge_enharmonic"}
        total_excluded = sum(category_counts.get(cat, 0) for cat in excluded_categories)
        self._log(f"  Total originally: {len(test_cases)}")
        self._log(f"  Excluded by category: {total_excluded}")
        self._log(f"  Excluded by confidence: {excluded_count - total_excluded}")
        self._log(f"  Final dataset: {len(rows)} ({len(rows)/len(test_cases)*100:.1f}%)")

        # Save baseline
        baseline_data = {
            "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            "method": "calibration_pipeline_fixed_v1",
            "exclusions": {
                "excluded_categories": list(excluded_categories),
                "min_confidence_threshold": 0.1,
                "total_excluded": excluded_count,
                "exclusion_rate": excluded_count / len(test_cases)
            },
            "rows": rows,
        }

        with open(self.baseline_path, "w") as f:
            json.dump(baseline_data, f, indent=2)
        self._log(f"💾 Saved baseline to {self.baseline_path}")

        # Create enhanced dataframe for calibration
        df_enhanced = pd.DataFrame(rows)
        self._log(f"✅ Enhanced baseline: {len(df_enhanced)} rows with proper bucket routing")

        # Note: Bucket distribution will be shown after data hygiene since buckets are computed per track there

        # Apply data hygiene
        self._log("🧹 Applying data hygiene...")
        df_clean = stage0_data_hygiene(df_enhanced)

        # Apply corrected filtering for valid track/category combinations
        df_clean = self._filter_valid_combinations(df_clean)
        self._log(f"✅ Filtered to {len(df_clean)} samples with valid track/category combinations")

        # Build calibration mapping with stages
        self._log("🎯 Training 4-stage calibration pipeline...")
        calibration_mapping = {
            "version": "2025-09-18-corrected",
            "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            "fixes_applied": [
                "excluded_scale_melody_category",
                "proper_modal_bucket_names",
                "minimum_confidence_filtering",
                "improved_isotonic_regression",
                "enhanced_bucket_routing",
                "filtered_invalid_track_category_combinations",
                "correlation_and_variance_quality_checks",
                "identity_mapping_for_poor_quality_data"
            ],
            "tracks": {},
        }

        # Process each track with pipeline
        for track in ["functional", "modal"]:
            self._log(f"📊 Training calibration for {track.upper()} track")

            track_mapping = {
                "GLOBAL": {},
                "buckets": {},
            }

            # Stage 1-4 for GLOBAL bucket with viability check
            self._log(f"  Processing {track.upper()} GLOBAL with stages...")

            if self._check_calibration_viability(df_clean, track):
                # Calibration is viable - use full pipeline
                platt_global = stage1_platt_scaling(df_clean, track, "GLOBAL")
                isotonic_global = stage2_isotonic_regression(
                    df_clean, track, "GLOBAL", platt_global
                )
                uncertainty_global = stage4_uncertainty_learning(df_clean, track, "GLOBAL")
            else:
                # Use identity mapping to preserve original performance
                self._log(f"    🔄 Using identity mapping for {track.upper()} GLOBAL")
                platt_global = {"a": 1.0, "b": 0.0}
                isotonic_global = {
                    "x": [0.001, 0.999],
                    "y": [0.001, 0.999]
                }
                uncertainty_global = {
                    "base_uncertainty": 0.3,
                    "confidence_penalty": 0.0,
                    "uncertainty_std": 0.2,
                    "sample_count": len(df_clean[df_clean["track"] == track]),
                    "method": "identity"
                }

            track_mapping["GLOBAL"] = {
                "platt": platt_global,
                "isotonic": isotonic_global,
                "uncertainty": uncertainty_global,
            }

            # Find buckets with sufficient data (LOWERED threshold for modal)
            bucket_counts = df_clean[df_clean["track"] == track]["bucket"].value_counts()
            min_samples = 30 if track == "modal" else 60  # Lower threshold for modal
            viable_buckets = bucket_counts[bucket_counts >= min_samples].index.tolist()

            self._log(f"  Viable buckets for {track}: {viable_buckets} (min {min_samples} samples)")

            # Stage 1-4 for each viable bucket with viability check
            for bucket in viable_buckets:
                if bucket == "GLOBAL":
                    continue

                self._log(f"  Processing {track.upper()} {bucket} with stages...")
                try:
                    if self._check_calibration_viability(df_clean, track, bucket):
                        # Calibration is viable - use full pipeline
                        platt_bucket = stage1_platt_scaling(df_clean, track, bucket)
                        isotonic_bucket = stage2_isotonic_regression(
                            df_clean, track, bucket, platt_bucket
                        )
                        uncertainty_bucket = stage4_uncertainty_learning(
                            df_clean, track, bucket
                        )
                    else:
                        # Use identity mapping to preserve original performance
                        self._log(f"    🔄 Using identity mapping for {track.upper()} {bucket}")
                        bucket_samples = len(df_clean[(df_clean["track"] == track) & (df_clean["bucket"] == bucket)])
                        platt_bucket = {"a": 1.0, "b": 0.0}
                        isotonic_bucket = {
                            "x": [0.001, 0.999],
                            "y": [0.001, 0.999]
                        }
                        uncertainty_bucket = {
                            "base_uncertainty": 0.3,
                            "confidence_penalty": 0.0,
                            "uncertainty_std": 0.2,
                            "sample_count": bucket_samples,
                            "method": "identity"
                        }

                    track_mapping["buckets"][bucket] = {
                        "platt": platt_bucket,
                        "isotonic": isotonic_bucket,
                        "uncertainty": uncertainty_bucket,
                    }
                    self._log(f"    ✅ Successfully trained {bucket}")
                except Exception as e:
                    self._log(f"    ❌ Failed to train {bucket}: {e}")
                    continue

            calibration_mapping["tracks"][track] = track_mapping

        # Save calibration mapping
        with open(self.mapping_path, "w") as f:
            json.dump(calibration_mapping, f, indent=2)

        self._log(f"💾 Saved calibration mapping to {self.mapping_path}")
        self._log("✅ calibration training complete!")

        # Display summary
        self._log("📊 calibration summary:")
        for track, mapping in calibration_mapping["tracks"].items():
            buckets = list(mapping.get("buckets", {}).keys())
            self._log(f"  {track}: GLOBAL + {len(buckets)} buckets ({buckets})")

        return True

    def validate_calibration(self) -> bool:
        """Validate the calibration system and create validation dataframe."""
        self._log("🔍 Validating calibration system...")

        if not self.mapping_path.exists():
            self._log(f"❌ Calibration mapping not found: {self.mapping_path}")
            self._log("   Run 'generate' mode first")
            return False

        if not self.baseline_path.exists():
            self._log(f"❌ Baseline data not found: {self.baseline_path}")
            self._log("   Run 'generate' mode first")
            return False

        try:
            # Load calibration service
            service = CalibrationService(str(self.mapping_path))
            self._log("✅ Loaded calibration service")

            # Load baseline data
            with open(self.baseline_path, 'r') as f:
                baseline_data = json.load(f)
            baseline_df = pd.DataFrame(baseline_data.get('rows', []))
            self._log(f"✅ Loaded baseline: {len(baseline_df)} cases")

            # Create validation dataset
            validation_rows = []
            for _, row in baseline_df.iterrows():
                routing_features = row.get('routing_features', {})

                # Test functional track
                if (row.get('functional_confidence') is not None and
                    row.get('expected_functional_confidence') is not None):
                    try:
                        calibrated = service.calibrate_confidence(
                            row['functional_confidence'], 'functional', routing_features
                        )
                        validation_rows.append({
                            'name': row.get('name', 'unknown'),
                            'track': 'functional',
                            'raw_confidence': row['functional_confidence'],
                            'calibrated_confidence': calibrated,
                            'expected_confidence': row['expected_functional_confidence']
                        })
                    except Exception as e:
                        self._log(f"   ⚠️  Failed functional calibration: {e}")

                # Test modal track
                if (row.get('modal_confidence') is not None and
                    row.get('expected_modal_confidence') is not None):
                    try:
                        calibrated = service.calibrate_confidence(
                            row['modal_confidence'], 'modal', routing_features
                        )
                        validation_rows.append({
                            'name': row.get('name', 'unknown'),
                            'track': 'modal',
                            'raw_confidence': row['modal_confidence'],
                            'calibrated_confidence': calibrated,
                            'expected_confidence': row['expected_modal_confidence']
                        })
                    except Exception as e:
                        self._log(f"   ⚠️  Failed modal calibration: {e}")

            # Save validation dataframe
            validation_data = {
                'created_at': datetime.datetime.utcnow().isoformat() + 'Z',
                'method': 'calibration_validation_v1',
                'validation_rows': validation_rows
            }

            with open(self.validation_df_path, 'w') as f:
                json.dump(validation_data, f, indent=2)

            self._log(f"✅ Created validation dataset: {len(validation_rows)} records")
            self._log(f"💾 Saved validation data to {self.validation_df_path}")

            # Basic validation statistics
            validation_df = pd.DataFrame(validation_rows)
            for track in ['functional', 'modal']:
                track_data = validation_df[validation_df['track'] == track]
                if len(track_data) > 0:
                    mae = abs(track_data['calibrated_confidence'] - track_data['expected_confidence']).mean()
                    self._log(f"📊 {track.capitalize()} MAE: {mae:.4f}")

            return True

        except Exception as e:
            self._log(f"❌ Validation failed: {e}")
            return False

    def deploy_to_production(self) -> bool:
        """Deploy calibration files to production assets directory."""
        self._log("🚀 Deploying calibration to production...")

        # Production assets directory
        prod_assets = project_root / "src" / "harmonic_analysis" / "assets"
        prod_mapping = prod_assets / "calibration_mapping.json"

        if not prod_assets.exists():
            self._log(f"❌ Production assets directory not found: {prod_assets}")
            return False

        if not self.mapping_path.exists():
            self._log(f"❌ Calibration mapping not found: {self.mapping_path}")
            self._log("   Run 'generate' mode first")
            return False

        try:
            # Backup existing production file
            if prod_mapping.exists():
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = prod_assets / f"calibration_mapping_backup_{timestamp}.json"
                shutil.copy2(prod_mapping, backup_path)
                self._log(f"✅ Backed up production mapping to {backup_path.name}")

            # Copy new mapping to production
            shutil.copy2(self.mapping_path, prod_mapping)
            self._log(f"✅ Deployed calibration mapping to production")

            # Verify deployment
            service = CalibrationService(str(prod_mapping))
            self._log(f"✅ Verified production deployment")

            return True

        except Exception as e:
            self._log(f"❌ Deployment failed: {e}")
            return False


def main():
    """Main entry point for the calibration pipeline."""
    parser = argparse.ArgumentParser(
        description="Confidence Calibration Pipeline for Harmonic Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ENHANCEMENTS APPLIED:
1. Exclude scale_melody category (68% of data, all zeros)
2. Proper modal bucket naming (not 'functional_simple')
3. Minimum confidence filtering (exclude zeros)
4. Improved isotonic regression with better granularity
5. Enhanced bucket routing with modal characteristics

Examples:
  python calibration_pipeline.py generate    # Create baseline and mapping
  python calibration_pipeline.py validate    # Validate calibration
  python calibration_pipeline.py deploy      # Deploy to production
  python calibration_pipeline.py all         # Run all stages
"""
    )

    parser.add_argument(
        "mode",
        choices=["generate", "validate", "deploy", "all"],
        help="Pipeline mode: generate, validate, deploy, or all",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    pipeline = CalibrationPipeline(verbose=args.verbose)

    if args.mode in ["generate", "all"]:
        success = pipeline.generate_baseline_and_mapping()
        if not success:
            print("❌ Calibration generation failed")
            return 1

    if args.mode in ["validate", "all"]:
        success = pipeline.validate_calibration()
        if not success:
            print("❌ Calibration validation failed")
            return 1

    if args.mode in ["deploy", "all"]:
        success = pipeline.deploy_to_production()
        if not success:
            print("❌ Calibration deployment failed")
            return 1

    print("✅ Calibration pipeline completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())