import asyncio
import inspect
from typing import Any

import pytest


def pytest_configure(config: pytest.Config) -> None:
    # Ensure the asyncio marker is recognized even without pytest-asyncio installed
    config.addinivalue_line("markers", "asyncio: mark test as asyncio")

    # Register educational marker for optional educational tests
    config.addinivalue_line(
        "markers",
        "educational: marks tests requiring educational extra (skip if not installed)",
    )


# Check if educational features are available
try:
    from harmonic_analysis.educational import is_available

    EDUCATIONAL_AVAILABLE = is_available()
except ImportError:
    EDUCATIONAL_AVAILABLE = False


@pytest.fixture(autouse=True)
def skip_if_educational_not_available(request):
    """
    Auto-skip tests marked with 'educational' if extra not installed.

    This fixture runs automatically for all tests. When a test is marked
    with @pytest.mark.educational, it will be skipped with a helpful
    message if the educational features are not installed.
    """
    if request.node.get_closest_marker("educational"):
        if not EDUCATIONAL_AVAILABLE:
            pytest.skip(
                "Educational extra not installed. "
                "Install with: pip install harmonic-analysis[educational]"
            )


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
    """
    Minimal async test runner to support `async def` tests without requiring
    the pytest-asyncio plugin. If the test function is a coroutine function,
    run it using asyncio.run and signal that the call was handled by returning True.
    """
    test_func: Any = pyfuncitem.obj
    if inspect.iscoroutinefunction(test_func):
        kwargs = {
            arg: pyfuncitem.funcargs[arg] for arg in pyfuncitem._fixtureinfo.argnames
        }
        asyncio.run(test_func(**kwargs))
        return True
    return None
