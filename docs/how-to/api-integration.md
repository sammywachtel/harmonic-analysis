# How to Integrate the Harmonic Analysis API

This guide shows you how to integrate the Harmonic Analysis library into your application, whether you're building a web service, desktop app, or music analysis tool.

## Quick Integration

### Basic Synchronous Usage

```python
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

# Initialize once (expensive operation)
analyzer = PatternAnalysisService()

def analyze_progression(chords, key=None, style="classical"):
    """Analyze a chord progression."""
    try:
        result = analyzer.analyze_with_patterns(
            chord_symbols=chords,
            key_hint=key,
            profile=style
        )

        return {
            "success": True,
            "analysis": {
                "type": result.primary.type,
                "key": result.primary.key_signature,
                "roman_numerals": result.primary.roman_numerals,
                "confidence": result.primary.confidence,
                "reasoning": result.primary.reasoning
            },
            "alternatives": [
                {
                    "type": alt.type,
                    "confidence": alt.confidence,
                    "key": alt.key_signature
                }
                for alt in result.alternatives
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Usage
result = analyze_progression(["Am", "F", "C", "G"], "C major", "pop")
```

### Async Integration

For high-throughput applications:

```python
import asyncio
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

class AsyncHarmonicAnalyzer:
    def __init__(self):
        self.analyzer = PatternAnalysisService()

    async def analyze_batch(self, analyses):
        """Analyze multiple progressions concurrently."""
        tasks = []
        for analysis in analyses:
            task = self.analyzer.analyze_with_patterns_async(
                chord_symbols=analysis["chords"],
                key_hint=analysis.get("key"),
                profile=analysis.get("profile", "classical")
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

# Usage
analyzer = AsyncHarmonicAnalyzer()
batch = [
    {"chords": ["Am", "F", "C", "G"], "key": "C major", "profile": "pop"},
    {"chords": ["Dm", "G7", "C"], "key": "C major", "profile": "jazz"},
]
results = asyncio.run(analyzer.analyze_batch(batch))
```

## Web API Integration

### Flask Integration

```python
from flask import Flask, request, jsonify
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

app = Flask(__name__)

# Initialize analyzer once when the app starts
analyzer = PatternAnalysisService()

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()

    # Validate input
    if not data or 'chords' not in data:
        return jsonify({"error": "Missing 'chords' in request"}), 400

    try:
        result = analyzer.analyze_with_patterns(
            chord_symbols=data['chords'],
            key_hint=data.get('key'),
            profile=data.get('profile', 'classical')
        )

        # Convert to JSON-serializable format
        response = {
            "primary": {
                "type": result.primary.type,
                "key": result.primary.key_signature,
                "roman_numerals": result.primary.roman_numerals,
                "confidence": result.primary.confidence,
                "reasoning": result.primary.reasoning
            },
            "alternatives": [
                {
                    "type": alt.type,
                    "confidence": alt.confidence,
                    "key": alt.key_signature,
                    "roman_numerals": alt.roman_numerals
                }
                for alt in result.alternatives
            ],
            "analysis_time_ms": result.analysis_time_ms
        }

        return jsonify(response)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal analysis error"}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(debug=True)
```

**Usage:**
```bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"chords": ["Am", "F", "C", "G"], "key": "C major", "profile": "pop"}'
```

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

app = FastAPI(title="Harmonic Analysis API")

# Initialize analyzer
analyzer = PatternAnalysisService()

class AnalysisRequest(BaseModel):
    chords: Optional[List[str]] = None
    romans: Optional[List[str]] = None
    notes: Optional[List[str]] = None
    key: Optional[str] = None
    profile: str = "classical"

class AnalysisResponse(BaseModel):
    primary: dict
    alternatives: List[dict]
    analysis_time_ms: float

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    try:
        # Determine input type
        if request.chords:
            result = await analyzer.analyze_with_patterns_async(
                chord_symbols=request.chords,
                key_hint=request.key,
                profile=request.profile
            )
        elif request.romans:
            result = await analyzer.analyze_with_patterns_async(
                romans=request.romans,
                key_hint=request.key,
                profile=request.profile
            )
        elif request.notes:
            result = await analyzer.analyze_with_patterns_async(
                notes=request.notes,
                key_hint=request.key,
                profile=request.profile
            )
        else:
            raise HTTPException(status_code=400, detail="Must provide chords, romans, or notes")

        return AnalysisResponse(
            primary={
                "type": result.primary.type,
                "key": result.primary.key_signature,
                "roman_numerals": result.primary.roman_numerals,
                "confidence": result.primary.confidence,
                "reasoning": result.primary.reasoning
            },
            alternatives=[
                {
                    "type": alt.type,
                    "confidence": alt.confidence,
                    "key": alt.key_signature,
                    "roman_numerals": alt.roman_numerals
                }
                for alt in result.alternatives
            ],
            analysis_time_ms=result.analysis_time_ms
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal analysis error")

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

## Desktop Application Integration

### Tkinter Example

```python
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

class HarmonicAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Harmonic Analyzer")
        self.analyzer = PatternAnalysisService()

        self.setup_ui()

    def setup_ui(self):
        # Input frame
        input_frame = ttk.Frame(self.root, padding="10")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))

        ttk.Label(input_frame, text="Chord Progression:").grid(row=0, column=0, sticky=tk.W)
        self.chord_entry = ttk.Entry(input_frame, width=40)
        self.chord_entry.grid(row=0, column=1, padx=(5, 0))
        self.chord_entry.insert(0, "Am F C G")

        ttk.Label(input_frame, text="Key:").grid(row=1, column=0, sticky=tk.W)
        self.key_entry = ttk.Entry(input_frame, width=40)
        self.key_entry.grid(row=1, column=1, padx=(5, 0))
        self.key_entry.insert(0, "C major")

        ttk.Label(input_frame, text="Style:").grid(row=2, column=0, sticky=tk.W)
        self.style_var = tk.StringVar(value="pop")
        style_combo = ttk.Combobox(input_frame, textvariable=self.style_var,
                                   values=["classical", "jazz", "pop", "folk", "choral"])
        style_combo.grid(row=2, column=1, padx=(5, 0), sticky=(tk.W, tk.E))

        # Button
        ttk.Button(input_frame, text="Analyze", command=self.analyze).grid(row=3, column=1, pady=10)

        # Results frame
        results_frame = ttk.Frame(self.root, padding="10")
        results_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.results_text = tk.Text(results_frame, width=60, height=20)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)

        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

    def analyze(self):
        chords = self.chord_entry.get().split()
        key = self.key_entry.get() or None
        style = self.style_var.get()

        if not chords:
            messagebox.showerror("Error", "Please enter chord progression")
            return

        # Run analysis in background thread
        threading.Thread(target=self._run_analysis, args=(chords, key, style), daemon=True).start()

    def _run_analysis(self, chords, key, style):
        try:
            result = self.analyzer.analyze_with_patterns(
                chord_symbols=chords,
                key_hint=key,
                profile=style
            )

            # Update UI in main thread
            self.root.after(0, self._display_results, result)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Analysis Error", str(e)))

    def _display_results(self, result):
        self.results_text.delete(1.0, tk.END)

        output = f"Primary Analysis:\n"
        output += f"Type: {result.primary.type}\n"
        output += f"Key: {result.primary.key_signature}\n"
        output += f"Roman Numerals: {' '.join(result.primary.roman_numerals)}\n"
        output += f"Confidence: {result.primary.confidence:.2f}\n"
        output += f"Reasoning: {result.primary.reasoning}\n\n"

        if result.alternatives:
            output += "Alternative Interpretations:\n"
            for i, alt in enumerate(result.alternatives, 1):
                output += f"{i}. {alt.type} ({alt.confidence:.2f})\n"

        self.results_text.insert(1.0, output)

if __name__ == "__main__":
    root = tk.Tk()
    app = HarmonicAnalyzerGUI(root)
    root.mainloop()
```

## Performance Considerations

### Initialization Optimization

```python
# DO: Initialize once and reuse
analyzer = PatternAnalysisService()  # Expensive initialization

# DON'T: Initialize per request
def bad_example():
    analyzer = PatternAnalysisService()  # Very expensive!
    return analyzer.analyze_with_patterns(...)
```

### Caching Results

```python
from functools import lru_cache
import hashlib

class CachedAnalyzer:
    def __init__(self):
        self.analyzer = PatternAnalysisService()

    @lru_cache(maxsize=1000)
    def analyze_cached(self, chords_tuple, key, profile):
        """Cache analysis results for identical inputs."""
        return self.analyzer.analyze_with_patterns(
            chord_symbols=list(chords_tuple),
            key_hint=key,
            profile=profile
        )

    def analyze(self, chords, key=None, profile="classical"):
        # Convert to hashable types for caching
        chords_tuple = tuple(chords)
        return self.analyze_cached(chords_tuple, key, profile)
```

### Batch Processing

```python
async def process_music_library(songs):
    """Efficiently process large music libraries."""
    analyzer = PatternAnalysisService()

    # Process in batches to avoid memory issues
    batch_size = 100
    results = []

    for i in range(0, len(songs), batch_size):
        batch = songs[i:i + batch_size]
        batch_tasks = [
            analyzer.analyze_with_patterns_async(
                chord_symbols=song["chords"],
                key_hint=song.get("key"),
                profile=song.get("style", "pop")
            )
            for song in batch
        ]

        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        results.extend(batch_results)

        # Optional: Progress callback
        print(f"Processed {min(i + batch_size, len(songs))}/{len(songs)} songs")

    return results
```

## Error Handling

### Robust Error Handling

```python
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService
import logging

logger = logging.getLogger(__name__)

class RobustAnalyzer:
    def __init__(self):
        self.analyzer = PatternAnalysisService()

    def analyze_safely(self, chords, key=None, profile="classical"):
        """Analyze with comprehensive error handling."""
        try:
            # Validate inputs
            if not chords or not isinstance(chords, list):
                raise ValueError("Chords must be a non-empty list")

            if profile not in ["classical", "jazz", "pop", "folk", "choral"]:
                logger.warning(f"Unknown profile '{profile}', using 'classical'")
                profile = "classical"

            # Perform analysis
            result = self.analyzer.analyze_with_patterns(
                chord_symbols=chords,
                key_hint=key,
                profile=profile
            )

            # Validate results
            if not result.primary:
                raise RuntimeError("Analysis returned no primary result")

            return {
                "success": True,
                "result": result,
                "warnings": []
            }

        except ValueError as e:
            logger.error(f"Input validation error: {e}")
            return {
                "success": False,
                "error": f"Invalid input: {e}",
                "error_type": "validation"
            }

        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {
                "success": False,
                "error": f"Analysis failed: {e}",
                "error_type": "analysis"
            }
```

## Integration Testing

```python
import unittest
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer = PatternAnalysisService()

    def test_basic_analysis(self):
        """Test basic chord progression analysis."""
        result = self.analyzer.analyze_with_patterns(
            chord_symbols=["C", "Am", "F", "G"],
            key_hint="C major",
            profile="pop"
        )

        self.assertIsNotNone(result.primary)
        self.assertEqual(result.primary.key_signature, "C major")
        self.assertGreater(result.primary.confidence, 0.5)

    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        with self.assertRaises(ValueError):
            self.analyzer.analyze_with_patterns(
                chord_symbols=[],  # Empty list should raise error
                key_hint="C major"
            )

    def test_multiple_profiles(self):
        """Test that different profiles return different results."""
        chords = ["Am", "F", "C", "G"]
        key = "C major"

        pop_result = self.analyzer.analyze_with_patterns(
            chord_symbols=chords, key_hint=key, profile="pop"
        )
        jazz_result = self.analyzer.analyze_with_patterns(
            chord_symbols=chords, key_hint=key, profile="jazz"
        )

        # Results may differ in confidence or reasoning
        self.assertIsNotNone(pop_result.primary)
        self.assertIsNotNone(jazz_result.primary)

if __name__ == "__main__":
    unittest.main()
```

## Next Steps

- **Performance tuning**: See [Performance Optimization](performance-optimization.md)
- **Custom patterns**: Learn [Pattern Customization](pattern-customization.md)
- **Troubleshooting**: Check [Troubleshooting Guide](troubleshooting.md)
- **Advanced configuration**: Read [Configuration Options](../reference/configuration.md)

For specific framework integrations or deployment scenarios not covered here, please check our [GitHub Issues](https://github.com/your-repo/harmonic-analysis/issues) or open a new issue.
