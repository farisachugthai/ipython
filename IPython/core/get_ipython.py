def get_ipython():
    """Get the global `InteractiveShell` instance.

    Returns `None` if no `InteractiveShell` instance is registered.
    """
    from IPython.core.interactiveshell import InteractiveShell  # noqa
    if InteractiveShell.initialized():
        return InteractiveShell.instance()
