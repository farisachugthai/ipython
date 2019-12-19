"""Utility function for finding modules.

`find_module` returns a path to module or None, given certain conditions.

absolute or relative? path object or str?

WHAT CONDITIONS????

"""
import importlib


def find_mod(module_name):
    """
    Find module `module_name` on sys.path, and return the path to module `module_name`.

      - If `module_name` refers to a module directory, then return path to __init__ file.
        - If `module_name` is a directory without an __init__file, return None.
      - If module is missing or does not have a `.py` or `.pyw` extension, return None.
        - Note that we are not interested in running bytecode.
      - Otherwise, return the fill path of the module.

    Parameters
    ----------
    module_name : str

    Returns
    -------
    module_path : str
        Path to module `module_name`, its __init__.py, or None,
        depending on above conditions.
    """
    loader = importlib.util.find_spec(module_name)
    module_path = loader.origin
    if module_path is None:
        return None
    else:
        split_path = module_path.split(".")
        if split_path[-1] in ["py", "pyw"]:
            return module_path
        else:
            return None
