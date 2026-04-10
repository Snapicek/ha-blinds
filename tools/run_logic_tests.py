from __future__ import annotations

import sys
import unittest


if __name__ == "__main__":
    # Add the project root to Python path for imports
    sys.path.insert(0, ".")
    suite = unittest.defaultTestLoader.discover("tests", pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
