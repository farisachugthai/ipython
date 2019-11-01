#!/usr/bin/env python
"""Script to auto-generate our API docs.

Is the module to download called apigen? I downloaded that and in
python3.7 on 10/05/2019, running this script failed because there's no
module named rpcrequest. Pip and conda can't
find it either so are we just not supposed to run this file directly?

If so, then I'm getting the feeling that this script isn't used at all.

No it definitely is and I just got the error message again.

GOT IT. apigen is  ./sphinxext/apigen.py

Jesus Christ that was tough.

"""
import logging
import os
from pathlib import Path
import sys

from sphinxext.apigen import ApiDocWriter


class SphinxDirectories:
    """Put all of the directories that the APIDocWriter and Sphinx need in 1 spot.

    Don't like the way it's set up? Okay. Subclass this and use your own!

    See isn't that a little nicer than globals EVERYWHERE?
    """

    def __init__(self):
        self.cwd = Path('.').absolute()
        self.source = self.cwd.joinpath('source')
        self.outdir = self.source.joinpath('api', 'generated')


def main():
    # You have to escape the . here because . is a special char for regexps.
    # You must do make clean if you change this!
    docwriter = ApiDocWriter('IPython', rst_extension='.rst')
    docwriter.package_skip_patterns += [r'\.external$',
                                        # Extensions are documented elsewhere.
                                        r'\.extensions',
                                        # Magics are documented separately
                                        r'\.core\.magics',
                                        # This isn't API
                                        # Wait why not ?
                                        # r'\.sphinxext',
                                        # Shims
                                        r'\.kernel',
                                        r'\.terminal\.pt_inputhooks',
                                        ]

    # The inputhook* modules often cause problems on import, such as trying to
    # load incompatible Qt bindings. It's easiest to leave them all out. The
    docwriter.module_skip_patterns += [r'\.lib\.inputhook.+',
                                       r'\.ipdoctest',
                                       r'\.testing\.plugin',
                                       # We document this manually.
                                       r'\.utils\.py3compat',
                                       # These are exposed in display
                                       r'\.core\.display',
                                       r'\.lib\.display',
                                       # Shims
                                       r'\.config',
                                       r'\.consoleapp',
                                       r'\.frontend$',
                                       r'\.html',
                                       r'\.nbconvert',
                                       r'\.nbformat',
                                       r'\.parallel',
                                       r'\.qt',
                                       # this is deprecated.
                                       r'\.utils\.warn',
                                       # Private APIs (there should be a lot more here)
                                       r'\.terminal\.ptutils',
                                       ]
    # main API is in the inputhook module, which is documented.

    # These modules import functions and classes from other places to expose
    # them as part of the public API. They must have __all__ defined. The
    # non-API modules they import from should be excluded by the skip patterns
    # above.
    docwriter.names_from__all__.update({
        'IPython.display',
    })

    # Now, generate the outputs
    # docwriter.write_api_docs(outdir)
    api_dirs = SphinxDirectories()
    docwriter.write_api_docs(api_dirs.outdir)
    # Write index with .txt extension - we can include it, but Sphinx won't try
    # to compile it

    # Don't actually know if we need the fspath but hey
    # TODO: change the filename to anything more descriptive and document it's
    # existence somewhere!!!
    docwriter.write_index(api_dirs.outdir.__fspath__(), 'gen.txt',)
    logging.info('%d files written' % len(docwriter.written_modules))


if __name__ == '__main__':
    main()
