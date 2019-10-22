
def conda():
    """Simpler re-implemented line magic."""
    conda = shutil.which('conda')
    if 'bat' in conda.lower():
        conda = 'call ' + conda
    %sx conda
