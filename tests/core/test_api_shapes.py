def test_api_available():
    """
    Smoke test: the DTO module should be importable in the project environment.
    """
    import harmonic_analysis.dto as dto  # noqa: F401
    from harmonic_analysis.dto import AnalysisEnvelope, AnalysisSummary  # noqa: F401

    assert True
