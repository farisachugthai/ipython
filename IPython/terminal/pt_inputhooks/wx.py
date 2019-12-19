"""Enable wxPython to be used interactively in prompt_toolkit.

There's so much repitition in this module I actually thought it
was the result of a failed merge I missed.

Then I noticed it was in master too...
"""
import functools
import sys
import signal
import time
from timeit import default_timer as clock


def ignore_keyboardinterrupts(func):
    """Ignore <C-c> during execution of the decorated function.

    Decorator which causes :exc:`KeyboardInterrupt` exceptions to be
    This is used by the inputhook functions to handle the event where the user
    presses :kbd:`CTRL-C` while IPython is idle, and the inputhook loop
    is running. In this case, we want to ignore interrupts.
    """

    @functools.wraps
    def wrapper(*args, **kwargs):
        """

        Parameters
        ----------
        args :
        kwargs :
        """
        try:
            func(*args, **kwargs)
        except KeyboardInterrupt:
            pass

    return wrapper


@ignore_keyboardinterrupts
def inputhook_wx1(context):
    """Run the wx event loop by processing pending events only.

    This approach seems to work, but its performance is not great as it
    relies on having PyOS_InputHook called regularly.

    Notes
    ------
    Make a temporary event loop and process system events until
    there are no more waiting, then allow idle events (which
    will also deal with pending or posted wx events.)

    """
    app = wx.GetApp()
    if app is not None:
        assert wx.Thread_IsMain()
        evtloop = wx.EventLoop()
        ea = wx.EventLoopActivator(evtloop)
        while evtloop.Pending():
            evtloop.Dispatch()
        app.ProcessIdle()
        del ea
    return 0


class EventLoopRunner:
    def Run(self, time, input_is_ready):
        """

        Parameters
        ----------
        time :
        input_is_ready :
        """
        self.input_is_ready = input_is_ready
        self.evtloop = wx.EventLoop()
        self.timer = EventLoopTimer(self.check_stdin)
        self.timer.Start(time)
        self.evtloop.Run()

    def check_stdin(self):
        """

        """
        if self.input_is_ready():
            self.timer.Stop()
            self.evtloop.Exit()


@ignore_keyboardinterrupts
def inputhook_wx2(context):
    """Run the wx event loop, polling for stdin.

    This version runs the wx eventloop for an undetermined amount of time,
    during which it periodically checks to see if anything is ready on
    stdin.  If anything is ready on stdin, the event loop exits.

    The argument to elr.Run controls how often the event loop looks at stdin.
    This determines the responsiveness at the keyboard.  A setting of 1000
    enables a user to type at most 1 char per second.  I have found that a
    setting of 10 gives good keyboard response.  We can shorten it further,
    but eventually performance would suffer from calling select/kbhit too
    often.
    """
    app = wx.GetApp()
    if app is not None:
        assert wx.Thread_IsMain()
        elr = EventLoopRunner()
        # As this time is made shorter, keyboard response improves, but idle
        # CPU load goes up.  10 ms seems like a good compromise.
        elr.Run(
            time=10,  # CHANGE time here to control polling interval
            input_is_ready=context.input_is_ready,
        )


@ignore_keyboardinterrupts
def inputhook_wx3(context):
    """Run the wx event loop by processing pending events only.

    This is like inputhook_wx1, but it keeps processing pending events
    until stdin is ready.  After processing all pending events, a call to
    time.sleep is inserted.  This is needed, otherwise, CPU usage is at 100%.
    This sleep time should be tuned though for best performance.

    After asserting that we're on the main thread, we begin cheking signals.
    The import of wx on Linux sets the handler for signal.SIGINT
    to 0.  This is a bug in wx or gtk.  We fix by just setting it
    back to the Python default.

    We need to sleep at this point to keep the idle CPU load
    low.  However, if sleep to long, GUI response is poor.  As
    a compromise, we watch how often GUI events are being processed
    and switch between a short and long sleep time.  Here are some
    stats useful in helping to tune this.:

        time    CPU load
        0.001   13%
        0.005   3%
        0.01    1.5%
        0.05    0.5%

    """
    app = wx.GetApp()
    if app is None:
        return
    assert wx.Thread_IsMain()
    if not callable(signal.getsignal(signal.SIGINT)):
        signal.signal(signal.SIGINT, signal.default_int_handler)
    evtloop = wx.EventLoop()
    ea = wx.EventLoopActivator(evtloop)
    t = clock()
    while not context.input_is_ready():
        while evtloop.Pending():
            t = clock()
            evtloop.Dispatch()
        app.ProcessIdle()
        used_time = clock() - t
        if used_time > 10.0:
            # print 'Sleep for 1 s'  # dbg
            time.sleep(1.0)
        elif used_time > 0.1:
            # Few GUI events coming in, so we can sleep longer
            # print 'Sleep for 0.05 s'  # dbg
            time.sleep(0.05)
        else:
            # Many GUI events coming in, so sleep only very little
            time.sleep(0.001)
    del ea


@ignore_keyboardinterrupts
def inputhook_wxphoenix(context):
    """Run the wx event loop until the user provides more input.

    This input hook is suitable for use with wxPython >= 4 (a.k.a. Phoenix).

    It uses the same approach to that used in
    ipykernel.eventloops.loop_wx. The wx.MainLoop is executed, and a wx.Timer
    is used to periodically poll the context for input. As soon as input is
    ready, the wx.MainLoop is stopped.
    """
    app = wx.GetApp()

    if app is None:
        return
    if context.input_is_ready():
        return
    assert wx.IsMainThread()

    # Wx uses milliseconds
    poll_interval = 100

    # Use a wx.Timer to periodically check whether input is ready - as soon as
    # it is, we exit the main loop
    def poll(ev):
        """

        Parameters
        ----------
        ev :
        """
        if context.input_is_ready():
            app.ExitMainLoop()

    timer = wx.Timer()
    timer.Start(poll_interval)
    timer.Bind(wx.EVT_TIMER, poll)

    # The import of wx on Linux sets the handler for signal.SIGINT to 0.  This
    # is a bug in wx or gtk.  We fix by just setting it back to the Python
    # default.
    if not callable(signal.getsignal(signal.SIGINT)):
        signal.signal(signal.SIGINT, signal.default_int_handler)

    # The SetExitOnFrameDelete call allows us to run the wx mainloop without
    # having a frame open.
    app.SetExitOnFrameDelete(False)
    app.MainLoop()


if __name__ == "__main__":
    import wx

    # Get the major wx version number to figure out what input hook we should use.
    major_version = 3

    try:
        major_version = int(wx.__version__[0])
    except Exception:
        pass

    # Use the phoenix hook on all platforms for wxpython >= 4
    if major_version >= 4:
        inputhook = inputhook_wxphoenix
    # On OSX, evtloop.Pending() always returns True, regardless of there being
    # any events pending. As such we can't use implementations 1 or 3 of the
    # inputhook as those depend on a pending/dispatch loop.
    elif sys.platform == "darwin":
        inputhook = inputhook_wx2
    else:
        inputhook = inputhook_wx3

    class EventLoopTimer(wx.Timer):
        """Forgot this one. Still haven't imported wx yet."""

        def __init__(self, func):
            self.func = func
            wx.Timer.__init__(self)

        def Notify(self):
            self.func()
