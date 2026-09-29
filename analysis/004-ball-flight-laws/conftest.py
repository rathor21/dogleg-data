"""Puts the 004 package directory on sys.path so tests can `import flight`."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
