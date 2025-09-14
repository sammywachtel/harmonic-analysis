"""
Modal Analysis Service

Thin façade over the enhanced modal analyzer to isolate modal engine implementation
from the rest of the codebase and provide a clean interface for multi-layer analysis.
"""

import asyncio
from typing import List, Optional

from ..analysis_types import ModalAnalysisResult, ModalCharacteristic
from ..core.enhanced_modal_analyzer import EnhancedModalAnalyzer


class ModalAnalysisService:
    """Service wrapper for modal analysis functionality."""

    def __init__(self) -> None:
        self._analyzer = EnhancedModalAnalyzer()

    async def analyze_async(
        self, chord_symbols: List[str], key_hint: Optional[str]
    ) -> ModalAnalysisResult:
        """Async modal analysis using standardized modal analyzer API.

        Args:
            chord_symbols: List of chord symbols to analyze
            key_hint: Optional key hint (e.g., "C major")

        Returns:
            ModalAnalysisResult with characteristics, confidence, and evidence
        """
        # Use the standardized async API
        modal_dict = await self._analyzer.analyze_modal(
            chords=chord_symbols, parent_key=key_hint
        )

        # Convert standardized dict output to ModalAnalysisResult
        characteristics = []

        # Extract mode name for characteristic labels
        mode_name = modal_dict.get("mode", "")
        confidence = modal_dict.get("confidence", 0.0)

        # Create characteristic labels based on mode
        if confidence > 0.0 and mode_name:
            if "Mixolydian" in mode_name:
                characteristics.append(
                    ModalCharacteristic(
                        label="mixolydian_color (bVII)",
                        evidence=["bVII chord present indicating Mixolydian mode"],
                    )
                )
            elif "Dorian" in mode_name:
                characteristics.append(
                    ModalCharacteristic(
                        label="dorian_color (iv in minor)",
                        evidence=[
                            "Major IV chord in minor context indicating Dorian mode"
                        ],
                    )
                )
            elif "Phrygian" in mode_name:
                characteristics.append(
                    ModalCharacteristic(
                        label="phrygian_color (bII)",
                        evidence=["bII chord present indicating Phrygian mode"],
                    )
                )
            elif "Lydian" in mode_name:
                characteristics.append(
                    ModalCharacteristic(
                        label="lydian_color (#IV)",
                        evidence=["#IV or II chord present indicating Lydian mode"],
                    )
                )
            elif "Aeolian" in mode_name:
                characteristics.append(
                    ModalCharacteristic(
                        label="aeolian_minor",
                        evidence=["Natural minor characteristics detected"],
                    )
                )

        # Determine parent key relationship
        parent_key_relationship = None
        if key_hint and mode_name:
            if "major" in key_hint.lower():
                # Major key context - Ionian aligns, others conflict
                if "Ionian" in mode_name:
                    parent_key_relationship = "aligns"
                else:
                    parent_key_relationship = "conflicts"
            else:
                # Minor key context - Aeolian aligns, others conflict
                if "Aeolian" in mode_name:
                    parent_key_relationship = "aligns"
                else:
                    parent_key_relationship = "conflicts"

        return ModalAnalysisResult(
            characteristics=characteristics,
            parent_key_relationship=parent_key_relationship,
            confidence=confidence,
            inferred_mode=mode_name,
            rationale=modal_dict.get("reasoning", "Modal analysis completed"),
        )

    def analyze(
        self, chord_symbols: List[str], key_hint: Optional[str]
    ) -> ModalAnalysisResult:
        """Synchronous wrapper for modal analysis.

        Args:
            chord_symbols: List of chord symbols to analyze
            key_hint: Optional key hint (e.g., "C major")

        Returns:
            ModalAnalysisResult with characteristics, confidence, and evidence
        """
        # Check if we're already in an event loop
        try:
            asyncio.get_running_loop()
            # If we're in a running loop, we need to schedule this differently
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                return executor.submit(
                    lambda: asyncio.run(self.analyze_async(chord_symbols, key_hint))
                ).result()
        except RuntimeError:
            # No running loop, can use asyncio.run directly
            return asyncio.run(self.analyze_async(chord_symbols, key_hint))
