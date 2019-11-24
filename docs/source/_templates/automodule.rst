
{{ fullname | escape | underline }}

{# All credit goes to Matplotlib for these templates #}

.. currentmodule:: {{ module }}


{% if objtype in ['class'] %}

.. auto{{ objtype }}:: {{ objname }}
    :show-inheritance:

{% else %}

.. auto{{ objtype }}:: {{ objname }}

{% endif %}

.. raw:: html

    <div class="clearer"></div>

{# Vim: set ft=htmljinja: #}
