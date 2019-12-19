import sys
from IPython.core.debugger import CorePdb as Pdb
from IPython.core.display_trap import DisplayTrap


class UltraDbg:
    """Refactoring things out of VerboseTB

    """
    def __init__(self, call_pdb=None, debugger_cls=None):
        self.call_pdb = call_pdb
        self.debugger_cls = debugger_cls or Pdb

        if self.pdb is None:
            self.pdb = self.debugger_cls()

    def calling_pdb(self):
        """Execute our pdb related commands.

        Returns
        -------
        object
        """
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

        This method in particular should be easy enough to refactor out.
        ostream is just sys.stdout, call_pdb and force are now keyword
        parameters, sys.exc_info() replaces the evalue nonsense.

        It'll probably be a cleaner implementation if we do it this way.
        Check that out!

        Parameters
        ----------
        force :

        Returns
        -------
        object
        """

        if force or self.call_pdb:
            # the system displayhook may have changed, restore the original
            # for pdb
            display_trap = DisplayTrap(hook=sys.__displayhook__)
            with display_trap:
                self.calling_pdb()

        if hasattr(self, "tb"):
            del self.tb


