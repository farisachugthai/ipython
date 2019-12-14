import inspect
import keyword
import linecache
import os
import sys
import time
import tokenize
import traceback
from importlib._bootstrap_external import source_from_cache
from logging import debug, error, info
from shutil import get_terminal_size

import PyColorize
from core import get_ipython
from core.display_trap import DisplayTrap
from core.ultratb import TBTools, get_parts_of_chained_exception, INDENT_SIZE, eqrepr, nullrepr, generate_tokens, \
    _format_traceback_lines, find_recursion, _fixed_getinnerframes, inspect_error
from os import path as util_path

from data import uniq_stable


class VerboseTB(TBTools):
    """A port of Ka-Ping Yee's cgitb.py module that outputs color text instead
    of HTML.  Requires inspect and pydoc.  Crazy, man.

    Modified version which optionally strips the topmost entries from the
    traceback, to be used with alternate interpreters (because their own code
    would appear in the traceback).
    """

    def __init__(
        self,
        color_scheme="NoColor",
        call_pdb=False,
        ostream=None,
        tb_offset=0,
        long_header=False,
        include_vars=True,
        check_cache=None,
        debugger_cls=None,
        parent=None,
        config=None,
    ):
        """Specify traceback offset, headers and color scheme.

        Define how many frames to drop from the tracebacks. Calling it with
        tb_offset=1 allows use of this handler in interpreters which will have
        their own code at the top of the traceback (VerboseTB will first
        remove that frame before printing the traceback info).

        Parameters
        ----------
        check_cache
            By default we use linecache.checkcache, but the user can provide a
            different check_cache implementation.  This is used by the IPython
            kernel to provide tracebacks for interactive code that is cached,
            by a compiler instance that flushes the linecache but preserves its
            own code cache.
        ostream
            Required as by the method :meth:`get_records`.
        pdb : bool
            TODO: Amazingly we didn't cover everything. The :meth:`debugger`
            method invokes the call_pdb parameter and references it as pdb.

        """
        self.color_scheme = color_scheme
        self.call_pdb = call_pdb
        self.ostream = ostream
        self.parent = parent
        self.config = config
        # self.tb = etb
        self.tb_offset = tb_offset
        self.long_header = long_header
        self.include_vars = include_vars
        # TODO: refactored this out but bound it just in case
        self.get_parts_of_chained_exception = get_parts_of_chained_exception
        if check_cache is None:
            check_cache = linecache.checkcache
        self.check_cache = check_cache

        from IPython.core import debugger

        self.debugger_cls = debugger_cls or debugger.CorePdb

    def format_records(self, records, last_unique, recursion_repeat):
        """Format the stack frames of the traceback"""
        frames = []
        for r in records[: last_unique + recursion_repeat + 1]:
            # print '*** record:',file,lnum,func,lines,index  # dbg
            frames.append(self.format_record(*r))

        if recursion_repeat:
            frames.append(
                "... last %d frames repeated, from the frame below ...\n"
                % recursion_repeat
            )
            frames.append(
                self.format_record(*records[last_unique + recursion_repeat + 1])
            )

        return frames

    def format_record(self, frame, file, lnum, func, lines, index):
        """Format a single stack frame.

        TODO: Figure out what in traceback has a matching call signature because
        if you can replace this, the whole module gets that much simpler.

        Jesus Christ this is a hell of a method though.
        """
        col_scheme = self.color_scheme_table.active_scheme_name
        indent = " " * INDENT_SIZE
        em_normal = "{}".format(indent)
        undefined = "undefined"
        tpl_link = ""
        tpl_call = "in"
        tpl_call_fail = "in (***failed resolving arguments***)"
        tpl_local_var = ""
        tpl_global_var = "global"
        tpl_name_val = "="

        if not file:
            file = "?"
        elif file.startswith(str("<")) and file.endswith(str(">")):
            # Not a real filename, no problem...
            pass
        elif not os.path.isabs(file):
            # Try to make the filename absolute by trying all
            # sys.path entries (which is also what linecache does)
            for dirname in sys.path:
                try:
                    fullname = os.path.join(dirname, file)
                    if os.path.isfile(fullname):
                        file = os.path.abspath(fullname)
                        break
                except Exception:
                    # Just in case that sys.path contains very
                    # strange entries...
                    pass

        link = tpl_link % util_path.compress_user(file)
        args, varargs, varkw, locals_ = inspect.getargvalues(frame)

        if func == "?":
            call = ""
        elif func == "<module>":
            call = tpl_call % (func, "")
        else:
            # Decide whether to include variable details or not
            var_repr = eqrepr if self.include_vars else nullrepr
            try:
                call = tpl_call % (
                    func,
                    inspect.formatargvalues(
                        args, varargs, varkw, locals_, formatvalue=var_repr
                    ),
                )
            except KeyError:
                # This happens in situations like errors inside generator
                # expressions, where local variables are listed in the
                # line, but can't be extracted from the frame.  I'm not
                # 100% sure this isn't actually a bug in inspect itself,
                # but since there's no info for us to compute with, the
                # best we can do is report the failure and move on.  Here
                # we must *not* call any traceback construction again,
                # because that would mess up use of %debug later on.  So we
                # simply report the failure and move on.  The only
                # limitation will be that this frame won't have locals
                # listed in the call signature.  Quite subtle problem...
                # I can't think of a good way to validate this in a unit
                # test, but running a script consisting of:
                #  dict( (k,v.strip()) for (k,v) in range(10) )
                # will illustrate the error, if this exception catch is
                # disabled.
                call = tpl_call_fail % func

        # Don't attempt to tokenize binary files.
        if file.endswith((".so", ".pyd", ".dll")):
            return "%s %s\n" % (link, call)

        elif file.endswith((".pyc", ".pyo")):
            # Look up the corresponding source file.
            try:
                file = source_from_cache(file)
            except ValueError:
                # Failed to get the source file for some reason
                # E.g. https://github.com/ipython/ipython/issues/9486
                return "%s %s\n" % (link, call)

        def linereader(file=file, lnum=None, getline=linecache.getline):
            """

            Parameters
            ----------
            file :
            lnum :
            getline :

            Returns
            -------

            """
            if lnum is None:
                lnum = [lnum]
            line = getline(file, lnum[0])
            lnum[0] += 1
            return line

        # Build the list of names on this line of code where the exception
        # occurred.
        try:
            names = []
            name_cont = False

            for token_type, token, start, end, line in generate_tokens(linereader):
                # build composite names
                if token_type == tokenize.NAME and token not in keyword.kwlist:
                    if name_cont:
                        # Continuation of a dotted name
                        try:
                            names[-1].append(token)
                        except IndexError:
                            names.append([token])
                        name_cont = False
                    else:
                        # Regular new names.  We append everything, the caller
                        # will be responsible for pruning the list later.  It's
                        # very tricky to try to prune as we go, b/c composite
                        # names can fool us.  The pruning at the end is easy
                        # to do (or the caller can print a list with repeated
                        # names if so desired.
                        names.append([token])
                elif token == ".":
                    name_cont = True
                elif token_type == tokenize.NEWLINE:
                    break

        except (IndexError, UnicodeDecodeError, SyntaxError):
            # signals exit of tokenizer
            # SyntaxError can occur if the file is not actually Python
            #  - see gh-6300
            pass
        except tokenize.TokenError as msg:
            # Tokenizing may fail for various reasons, many of which are
            # harmless. (A good example is when the line in question is the
            # close of a triple-quoted string, cf gh-6864). We don't want to
            # show this to users, but want make it available for debugging
            # purposes.
            _m = (
                "An unexpected error occurred while tokenizing input\n"
                "The following traceback may be corrupted or invalid\n"
                "The error message is: %s\n" % msg
            )
            debug(_m)

        # Join composite names (e.g. "dict.fromkeys")
        names = [".".join(n) for n in names]
        # prune names list of duplicates, but keep the right order
        unique_names = uniq_stable(names)

        # Start loop over vars
        lvals = ""
        lvals_list = []
        if self.include_vars:
            for name_full in unique_names:
                name_base = name_full.split(".", 1)[0]
                if name_base in frame.f_code.co_varnames:
                    if name_base in locals_:
                        try:
                            value = repr(eval(name_full, locals_))
                        except BaseException:
                            value = undefined
                    else:
                        value = undefined
                    name = tpl_local_var % name_full
                else:
                    if name_base in frame.f_globals:
                        try:
                            value = repr(eval(name_full, frame.f_globals))
                        except BaseException:
                            value = undefined
                    else:
                        value = undefined
                    name = tpl_global_var % name_full
                lvals_list.append(tpl_name_val % (name, value))
        if lvals_list:
            lvals = "%s%s" % (indent, em_normal.join(lvals_list))

        level = "%s %s\n" % (link, call)

        if index is None:
            return level
        else:
            _line_format = PyColorize.Parser(style=col_scheme, parent=self).format2
            return "%s%s" % (
                level,
                "".join(
                    _format_traceback_lines(
                        lnum, index, lines, Colors, lvals, _line_format
                    )
                ),
            )

    def prepare_chained_exception_message(self, cause):
        """

        Parameters
        ----------
        cause :

        Returns
        -------

        """
        direct_cause = (
            "\nThe above exception was the direct cause of the following exception:\n"
        )
        exception_during_handling = (
            "\nDuring handling of the above exception, another exception occurred:\n"
        )

        if cause:
            message = [[direct_cause]]
        else:
            message = [[exception_during_handling]]
        return message

    def prepare_header(self, etype, long_version=False):
        """

        Parameters
        ----------
        etype :
        long_version :

        Returns
        -------

        """
        exc = "%s" % etype
        width = min(75, get_terminal_size()[0])
        if long_version:
            # Header with the exception type, python version, and date
            pyver = "Python " + sys.version.split()[0] + ": " + sys.executable
            date = time.ctime(time.time())

            head = "%s\n%s%s%s\n%s" % (
                "-" * width,
                exc,
                " " * (width - len(str(etype)) - len(pyver)),
                pyver,
                date.rjust(width),
            )

            head += (
                "\nA problem occurred executing Python code.  Here is the sequence of function"
                "\ncalls leading up to the error, with the most recent (innermost) call last."
            )
        else:
            # Simplified header
            head = "%s%s" % (
                exc,
                "Traceback (most recent call last)".rjust(width - len(str(etype))),
            )

        return head

    def format_exception(self, etype, evalue):
        """

        Parameters
        ----------
        etype :
        evalue :

        Returns
        -------

        """
        try:
            etype_str, evalue_str = map(str, (etype, evalue))
        except BaseException:
            # User exception is improperly defined.
            etype, evalue = str, sys.exc_info()[:2]
            etype_str, evalue_str = map(str, (etype, evalue))
        # ... and format it
        return ["%s: %s" % (etype_str, evalue_str)]

    def format_exception_as_a_whole(
        self, etype, evalue, etb, number_of_lines_of_context, tb_offset
    ):
        """Formats the header, traceback and exception message for a single exception.

        This may be called multiple times by Python 3 exception chaining
        (PEP 3134).
        """
        # some locals
        orig_etype = etype
        try:
            etype = etype.__name__
        except AttributeError:
            pass

        tb_offset = self.tb_offset if tb_offset is None else tb_offset
        head = self.prepare_header(etype, self.long_header)
        records = self.get_records(etb, number_of_lines_of_context, tb_offset)

        if records is None:
            return ""

        last_unique, recursion_repeat = find_recursion(orig_etype, evalue, records)

        frames = self.format_records(records, last_unique, recursion_repeat)

        formatted_exception = self.format_exception(etype, evalue)
        if records:
            filepath, lnum = records[-1][1:3]
            filepath = os.path.abspath(filepath)
            ipinst = get_ipython()
            if ipinst is not None:
                ipinst.hooks.synchronize_with_editor(filepath, lnum, 0)

        return [[head] + frames + ["".join(formatted_exception[0])]]

    def get_records(self, etb, number_of_lines_of_context, tb_offset):
        """

        Parameters
        ----------
        etb :
        number_of_lines_of_context :
        tb_offset :

        Returns
        -------

        """
        try:
            # Try the default getinnerframes and Alex's: Alex's fixes some
            # problems, but it generates empty tracebacks for console errors
            # (5 blanks lines) where none should be returned.
            return _fixed_getinnerframes(etb, number_of_lines_of_context, tb_offset)
        except UnicodeDecodeError:
            # This can occur if a file's encoding magic comment is wrong.
            # I can't see a way to recover without duplicating a bunch of code
            # from the stdlib traceback module. --TK
            error("\nUnicodeDecodeError while processing traceback.\n")
            return None
        except BaseException:
            # FIXME: I've been getting many crash reports from python 2.3
            # users, traceable to inspect.py.  If I can find a small test-case
            # to reproduce this, I should either write a better workaround or
            # file a bug report against inspect (if that's the real problem).
            # So far, I haven't been able to find an isolated example to
            # reproduce the problem.
            inspect_error()
            traceback.print_exc(file=self.ostream)
            info("\nUnfortunately, your original traceback can not be constructed.\n")
            return None

    def structured_traceback(
        self,
        etype=None,
        evalue=None,
        etb=None,
        tb_offset=None,
        number_of_lines_of_context=5,
        **kwargs,
    ):
        """Return a nice text document describing the traceback.

        Parameters
        ----------
        etype :
        number_of_lines_of_context :
        tb_offset :
        evalue :
        etb :
        kwargs : dict

        """
        formatted_exception = self.format_exception_as_a_whole(
            etype, evalue, etb, number_of_lines_of_context, tb_offset
        )

        head = "%s" % ("-" * min(75, get_terminal_size()[0]))
        structured_traceback_parts = [head]
        chained_exceptions_tb_offset = 0
        lines_of_context = 3
        formatted_exceptions = formatted_exception
        exception = get_parts_of_chained_exception(evalue)
        if exception:
            formatted_exceptions += self.prepare_chained_exception_message(
                evalue.__cause__
            )
            etype, evalue, etb = exception
        else:
            evalue = None
        chained_exc_ids = set()
        while evalue:
            formatted_exceptions += self.format_exception_as_a_whole(
                etype, evalue, etb, lines_of_context, chained_exceptions_tb_offset
            )
            exception = get_parts_of_chained_exception(evalue)

            if exception and not id(exception[1]) in chained_exc_ids:
                chained_exc_ids.add(
                    id(exception[1])
                )  # trace exception to avoid infinite 'cause' loop
                formatted_exceptions += self.prepare_chained_exception_message(
                    evalue.__cause__
                )
                etype, evalue, etb = exception
            else:
                evalue = None

        # we want to see exceptions in a reversed order:
        # the first exception should be on top
        for formatted_exception in reversed(formatted_exceptions):
            structured_traceback_parts += formatted_exception

        return structured_traceback_parts

    def debugger(self, force=False):
        """Call up the pdb debugger if desired, always clean up the tb
        reference.

        Keywords:

          - force(False): by default, this routine checks the instance call_pdb
            flag and does not actually invoke the debugger if the flag is false.
            The 'force' option forces the debugger to activate even if the flag
            is false.

        If the :param:`call_pdb` flag is set, the pdb interactive debugger is
        invoked. In all cases, the self.tb reference to the current traceback
        is deleted to prevent lingering references which hamper memory
        management.

        Note that each call to pdb() does an 'import readline', so if your app
        requires a special setup for the readline completers, you'll have to
        fix that by hand after invoking the exception handler.
        """

        if force or self.call_pdb:
            if self.pdb is None:
                self.pdb = self.debugger_cls()
            # the system displayhook may have changed, restore the original
            # for pdb
            display_trap = DisplayTrap(hook=sys.__displayhook__)
            with display_trap:
                self.pdb.reset()
                # Find the right frame so we don't pop up inside ipython itself
                if hasattr(self, "tb") and self.tb is not None:
                    etb = self.tb
                else:
                    etb = self.tb = sys.last_traceback
                while self.tb is not None and self.tb.tb_next is not None:
                    self.tb = self.tb.tb_next
                if etb and etb.tb_next:
                    etb = etb.tb_next
                self.pdb.botframe = etb.tb_frame
                self.pdb.interaction(None, etb)

        if hasattr(self, "tb"):
            del self.tb

    def handler(self, info=None):
        """

        Parameters
        ----------
        info :
        """
        (etype, evalue, etb) = info or sys.exc_info()
        self.tb = etb
        ostream = self.ostream
        ostream.flush()
        ostream.write(self.text(etype, evalue, etb))
        ostream.write("\n")
        ostream.flush()

    # Changed so an instance can just be called as VerboseTB_inst() and print
    # out the right info on its own.
    def __call__(self, etype=None, evalue=None, etb=None):
        """This hook can replace sys.excepthook (for Python 2.1 or higher)."""
        if etb is None:
            self.handler()
        else:
            self.handler((etype, evalue, etb))
        try:
            self.debugger()
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt")