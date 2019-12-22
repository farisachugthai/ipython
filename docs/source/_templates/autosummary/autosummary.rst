{{ fullname | escape | underline }}

.. currentmodule:: {{ module }}

{% if objtype in ['class'] %}

.. auto{{ objtype }}:: {{ objname }}
    :show-inheritance:

{% else %}

.. auto{{ objtype }}:: {{ objname }}

{% endif %}
