Just quickly firing off before going to work.

First word of advice to users of Sphinx
=======================================

TOC directives **always** come last.

Otherwise your sidebar will go.:

* Title of the current doc

   * Element in TOCTree

   * Element in TOCTree

   * Headers of the current doc


So they'll look at the sidebar and get understandably confused about the
ordering.


Second tip for any potential authors who want to help with the docs
===================================================================

Don't nest directories too deep. It renders certain docs unreachable from the
home page.

If someone has to go through a specific series of nested nodes to get to your
page, they're never going to remember how to get there.

If that specific series of nodes is the ONLY way to get to your page, *I mean
outside of just perusing the index but....literally who does that?*, then
people won't even notice that they aren't seeing it.

