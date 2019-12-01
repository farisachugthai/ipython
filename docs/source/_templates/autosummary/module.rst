{{ fullname | escape | underline }}

{# All credit goes to Matplotlib for these templates #}

.. currentmodule:: {{ module }}


{% if objtype in ['class'] %}

  {{ objtype | escape | underline }}

.. auto{{ objtype }}:: {{ objname }}
    :show-inheritance:
    :members:

{% else %}

  {{ objtype | escape | underline }}

.. auto{{ objtype }}:: {{ objname }}
    :members:

{% endif %}

.. raw:: html

    <div class="clearer"></div>

{# Vim: set ft=htmljinja: #}
