"""Oh so I'm just gonna go ahead and not do this....The shims are silly."""
import sys
import warnings

# from IPython.utils.shimmodule import ShimWarning


# def test_shim_warning():
#     sys.modules.pop('IPython.config', None)
#     with warnings.catch_warnings(record=True) as w:
#         warnings.simplefilter("always")
#         import IPython.config
#     assert len(w) == 1
#     assert issubclass(w[-1].category, ShimWarning)
