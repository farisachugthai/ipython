from ast import AST, Await, Expr, Return
import ast
import sys
import types

# -----------------------------------------------------------------------------
# Await Helpers
# -----------------------------------------------------------------------------


# we still need to run things using the asyncio eventloop, but there is no
# async integration


def _ast_asyncify(cell: str, wrapper_name: str) -> ast.Module:
    """
    Parse a cell with top-level await and modify the AST to be able to run it later.

    Parameters
    ----------
    cell : str
        The code cell to asyncronify
    wrapper_name : str
        The name of the function to be used to wrap the passed `cell`. It is
        advised to **not** use a python identifier in order to not pollute the
        global namespace in which the function will be ran.

    Returns
    -------
    A module object AST containing **one** function named `wrapper_name`.

    The given code is wrapped in a async-def function, parsed into an AST, and
    the resulting function definition AST is modified to return the last
    expression.

    The last expression or await node is moved into a return statement at the
    end of the function, and removed from its original location. If the last
    node is not Expr or Await nothing is done.

    The function `__code__` will need to be later modified  (by
    ``removed_co_newlocals``) in a subsequent step to not create new `locals()`
    meaning that the local and global scope are the same, ie as if the body of
    the function was at module level.

    Lastly a call to `locals()` is made just before the last expression of the
    function, or just after the last assignment or statement to make sure the
    global dict is updated as python function work with a local fast cache which
    is updated only on `local()` calls.
    """
    if sys.version_info >= (3, 8):
        return ast.parse(cell)
    tree = ast.parse(_asyncify(cell))

    function_def = tree.body[0]
    function_def.name = wrapper_name
    try_block = function_def.body[0]
    lastexpr = try_block.body[-1]
    if isinstance(lastexpr, (Expr, Await)):
        try_block.body[-1] = Return(lastexpr.value)
    ast.fix_missing_locations(tree)
    return tree

