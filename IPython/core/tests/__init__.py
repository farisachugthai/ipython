import warning

try:
    import nose
except ImportError:
    warning.warning('Nose not installed!')
