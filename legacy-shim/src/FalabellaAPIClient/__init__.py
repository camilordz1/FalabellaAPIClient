"""Deprecated name of falabella-sdk.

This package only exists so that ``pip install FalabellaAPIClient`` points users to the new
distribution. Install ``falabella-sdk`` and import ``falabella_sdk`` instead.
"""

import warnings

from falabella_sdk import *  # noqa: F401,F403
from falabella_sdk import __all__  # noqa: F401

warnings.warn(
    "FalabellaAPIClient was renamed to falabella-sdk. "
    "Run 'pip install falabella-sdk' and import 'falabella_sdk' instead. "
    "This package will not receive further updates.",
    FutureWarning,
    stacklevel=2,
)
