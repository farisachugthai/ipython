"""Infrastructure for registering and firing callbacks on application events.

Unlike :mod:`IPython.core.hooks`, which lets end users set single functions to
be called at specific times, or a collection of alternative methods to try,
callbacks are designed to be used by extension authors. A number of callbacks
can be registered for the same event without needing to be aware of one another.

The functions defined in this module are no-ops indicating the names of available
events and the arguments which will be passed to them.

...So those are abc methods right?


API
----

.. data:: available_events

   Dict of events.


Callback prototypes
------------------------------------------------------------------------------

No-op functions which describe the names of available events and the
signatures of callbacks for those events.

"""
from IPython.core.getipython import get_ipython

from backcall import callback_prototype


# event_name -> prototype mapping
available_events = {}


def _define_event(callback_function):
    callback_proto = callback_prototype(callback_function)
    available_events[callback_function.__name__] = callback_proto
    return callback_proto


class EventManager:
    """Manage a collection of events and a sequence of callbacks for each.

    This is attached to :class:`~IPython.core.interactiveshell.InteractiveShell`
    instances as an ``events`` attribute.

    The shell itself is also bound to the class as an :attr:`shell` attribute.

    """

    def __init__(self, shell=None, available_events=None):
        """Initialise the :class:`CallbackManager`.

        .. error:: lol whyyyy you renamed the class but not the docstring??

        Parameters
        ----------
        shell : :class:`~IPython.core.interactiveshell.InteractiveShell`, optional
            :class:`~IPython.core.interactiveshell.InteractiveShell` instance
        available_callbacks : iterable
            An iterable of names for callback events.

        """
        if available_events is None:
            available_events = {}
        self.shell = shell or get_ipython()
        self.callbacks = {n: [] for n in available_events}

    def __repr__(self):
        return ''.join(self.__class__.__name)

    def register(self, event, function):
        """Register a new event callback.

        Parameters
        ----------
        event : str
            The event for which to register this callback.
        function : callable
            A function to be called on the given event. It should take the same
            parameters as the appropriate callback prototype.

        Raises
        ------
        :exc:`TypeError`
            If ``function`` is not callable.
        :exc:`KeyError`
            If ``event`` is not one of the known events.

        """
        if not callable(function):
            raise TypeError('Need a callable, got %r' % function)
        callback_proto = available_events.get(event)
        self.callbacks[event].append(callback_proto.adapt(function))

    def unregister(self, event, function):
        """Remove a callback from the given event."""
        if function in self.callbacks[event]:
            return self.callbacks[event].remove(function)

        # Remove callback in case ``function`` was adapted by `backcall`.
        for callback in self.callbacks[event]:
            try:
                if callback.__wrapped__ is function:
                    return self.callbacks[event].remove(callback)
            except AttributeError:
                pass

        raise ValueError(
            'Function {!r} is not registered as a {} callback'.format(
                function, event))

    def trigger(self, event, *args, **kwargs):
        """Call callbacks for ``event``.

        Any additional arguments are passed to all callbacks registered for this
        event. Exceptions raised by callbacks are caught, and a message printed.
        """
        for func in self.callbacks[event][:]:
            try:
                func(*args, **kwargs)
            except (Exception, KeyboardInterrupt):
                print("Error in callback {} (for {}):".format(func, event))
                self.shell.showtraceback()


@_define_event
def pre_execute():
    """Fires before code is executed in response to user/frontend action.

    This includes comm and widget messages and silent execution, as well as user
    code cells.
    """
    pass


@_define_event
def pre_run_cell(info):
    """Fires before user-entered code runs.

    Parameters
    ----------
    info : :class:`~IPython.core.interactiveshell.ExecutionInfo`
        An object containing information used for the code execution.
    """
    pass


@_define_event
def post_execute():
    """Fires after code is executed in response to user/frontend action.

    This includes comm and widget messages and silent execution, as well as user
    code cells.
    """
    pass


@_define_event
def post_run_cell(result):
    """Fires after user-entered code runs.

    Parameters
    ----------
    result : :class:`~IPython.core.interactiveshell.ExecutionResult`
        The object which will be returned as the execution result.
    """
    pass


@_define_event
def shell_initialized(ip):
    """Fires after initialisation of :class:`~IPython.core.interactiveshell.InteractiveShell`.

    This is before extensions and startup scripts are loaded, so it can only be
    set by subclassing.

    Parameters
    ----------
    ip : :class:`~IPython.core.interactiveshell.InteractiveShell`
        The newly initialised shell.
    """
    pass
