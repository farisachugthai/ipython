.. _wrapperkernels:

====================================
Making simple Python wrapper kernels
====================================

.. module:: ipython_wrapper_kernels
   :synopsis: Summarize the IPython kernel and explain how to extend it.

.. versionadded:: 3.0

.. _ipykernel:

The IPython Kernel
------------------

All the other interfaces—the Notebook, the Qt console, ``ipython console`` in
the terminal, and third party interfaces—use the IPython Kernel. This is a
separate process which is responsible for running user code, and things like
computing possible completions. Frontends communicate with it using JSON
messages sent over `ZeroMQ <http://zeromq.org/>`_ sockets; the protocol they use is described in
:ref:`jupyterclient:messaging`.

The core execution machinery for the kernel is shared with terminal IPython:

.. image:: figs/ipy_kernel_and_terminal.png

A kernel process can be connected to more than one frontend simultaneously. In
this case, the different frontends will have access to the same variables.

.. TODO: Diagram illustrating this?

This design was intended to allow easy development of different frontends based
on the same kernel, but it also made it possible to support new languages in the
same frontends, by developing kernels in those languages, and we are refining
IPython to make that more practical.

Today, there are two ways to develop a kernel for another language. Wrapper
kernels reuse the communications machinery from IPython, and implement only the
core execution part. Native kernels implement execution and communications in
the target language:

.. image:: figs/other_kernels.png

Wrapper kernels are easier to write quickly for languages that have good Python
wrappers, like `octave_kernel <https://pypi.python.org/pypi/octave_kernel>`_, or
languages where it's impractical to implement the communications machinery, like
`bash_kernel <https://pypi.python.org/pypi/bash_kernel>`_. Native kernels are
likely to be better maintained by the community using them, like
`IJulia <https://github.com/JuliaLang/IJulia.jl>`_ or `IHaskell
<https://github.com/gibiansky/IHaskell>`_.

.. seealso::
   :ref:`jupyterclient:kernels`

   :doc:`wrapperkernels`

You can now re-use the kernel machinery in IPython to easily make new kernels.
This is useful for languages that have Python bindings, such as `Octave
<http://www.gnu.org/software/octave/>`_ (via `Oct2Py
<http://blink1073.github.io/oct2py/>`_), or languages where the REPL can be
controlled in a tty using `pexpect <http://pexpect.readthedocs.io/en/latest/>`_,
such as bash.

.. sorry to comment it out but there are 2 references to the bash kernel
   with different urls and sphinx doesn't like it.
.. .. seealso::
..    `bash_kernel <https://github.com/takluyver/bash_kernel>`_
..       A simple kernel for bash, written using this machinery.

Required steps
--------------

Subclass :class:`ipykernel.kernelbase.Kernel`, and implement the
following methods and attributes:

.. class:: MyKernel

   .. attribute:: implementation
                  implementation_version
                  language
                  language_version
                  banner

     Information for :ref:`msging_kernel_info` replies. 'Implementation' refers
     to the kernel (e.g. IPython), and 'language' refers to the language it
     interprets (e.g. Python). The 'banner' is displayed to the user in console
     UIs before the first prompt. All of these values are strings.

   .. attribute:: language_info

     Language information for :ref:`msging_kernel_info` replies, in a dictionary.
     This should contain the key ``mimetype`` with the mimetype of code in the
     target language (e.g. ``'text/x-python'``), and ``file_extension`` (e.g.
     ``'py'``).
     It may also contain keys ``codemirror_mode`` and ``pygments_lexer`` if they
     need to differ from :attr:`language`.

     Other keys may be added to this later.

   .. method:: do_execute(code, silent, store_history=True, user_expressions=None, allow_stdin=False)

     Execute user code.

     :param str code: The code to be executed.
     :param bool silent: Whether to display output.
     :param bool store_history: Whether to record this code in history and
         increase the execution count. If silent is True, this is implicitly
         False.
     :param dict user_expressions: Mapping of names to expressions to evaluate
         after the code has run. You can ignore this if you need to.
     :param bool allow_stdin: Whether the frontend can provide input on request
         (e.g. for Python's :func:`raw_input`).

     Your method should return a dict containing the fields described in
     :ref:`execution_results`. To display output, it can send messages
     using :meth:`~ipykernel.kernelbase.Kernel.send_response`.
     See :doc:`jupyterclient:messaging` for details of the different message types.

To launch your kernel, add this at the end of your module::

    if __name__ == '__main__':
        from ipykernel.kernelapp import IPKernelApp
        IPKernelApp.launch_instance(kernel_class=MyKernel)

Example
-------

``echokernel.py`` will simply echo any input it's given to stdout

.. code-block:: ipython

    from ipykernel.kernelbase import Kernel

    class EchoKernel(Kernel):
        implementation = 'Echo'
        implementation_version = '1.0'
        language = 'no-op'
        language_version = '0.1'
        language_info = {'mimetype': 'text/plain'}
        banner = "Echo kernel - as useful as a parrot"

        def do_execute(self, code, silent, store_history=True, user_expressions=None,
                       allow_stdin=False):
            if not silent:
                stream_content = {'name': 'stdout', 'text': code}
                self.send_response(self.iopub_socket, 'stream', stream_content)

            return {'status': 'ok',
                    # The base class increments the execution count
                    'execution_count': self.execution_count,
                    'payload': [],
                    'user_expressions': {},
                   }

    if __name__ == '__main__':
        from ipykernel.kernelapp import IPKernelApp
        IPKernelApp.launch_instance(kernel_class=EchoKernel)

Here's the Kernel spec ``kernel.json`` file for this.::

    {"argv":["python","-m","echokernel", "-f", "{connection_file}"],
     "display_name":"Echo"
    }


Optional steps
--------------

You can override a number of other methods to improve the functionality of your
kernel. All of these methods should return a dictionary as described in the
relevant section of the :ref:`messaging spec <jupyterclient:messaging>`.

.. class:: MyKernel

   .. method:: do_complete(code, cusor_pos)

     Code completion

     :param str code: The code already present
     :param int cursor_pos: The position in the code where completion is requested

     .. seealso::

        :ref:`msging_completion` messages

   .. method:: do_inspect(code, cusor_pos, detail_level=0)

     Object introspection

     :param str code: The code
     :param int cursor_pos: The position in the code where introspection is requested
     :param int detail_level: 0 or 1 for more or less detail. In IPython, 1 gets
         the source code.

     .. seealso::

        :ref:`msging_inspection` messages

   .. method:: do_history(hist_access_type, output, raw, session=None, start=None, stop=None, n=None, pattern=None, unique=False)

     History access. Only the relevant parameters for the type of history
     request concerned will be passed, so your method definition must have defaults
     for all the arguments shown with defaults here.

     .. seealso::

        :ref:`msging_history` messages

   .. method:: do_is_complete(code)

     Is code entered in a console-like interface complete and ready to execute,
     or should a continuation prompt be shown?

     :param str code: The code entered so far - possibly multiple lines

     .. seealso::

        :ref:`msging_is_complete` messages

   .. method:: do_shutdown(restart)

     Shutdown the kernel. You only need to handle your own clean up - the kernel
     machinery will take care of cleaning up its own things before stopping.

     :param bool restart: Whether the kernel will be started again afterwards

     .. seealso::

        :ref:`msging_shutdown` messages
