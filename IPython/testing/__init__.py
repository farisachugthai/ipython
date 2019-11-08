"""Testing support (tools to test IPython itself)."""
import os


# We scale all timeouts via this factor, slow machines can increase it
IPYTHON_TESTING_TIMEOUT_SCALE = os.getenv('IPYTHON_TESTING_TIMEOUT_SCALE', 1.0)
