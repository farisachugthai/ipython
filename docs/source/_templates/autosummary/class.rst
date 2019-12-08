{{ fullname | escape | underline}}

.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}
   :exclude-members:

   {% block methods %}
   .. automethod:: __init__

   {% if methods %}
   .. rubric:: Methods

   .. autosummary::
      :toctree: api/generated/

   {% for item in methods %}

   {%- if not item.startswith('_')  %}
      ~{{ name }}.{{ item }}
      {% endif %}

   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block attributes %}
   {% if attributes %}
   .. rubric:: Attributes

   .. autosummary::
      :toctree: api/generated/
   {% for item in attributes %}
   {%- if not item.startswith('_')  %}
      ~{{ name }}.{{ item }}
      {% endif %}
   {%- endfor %}
   {% endif %}
   {% endblock %}
{# Vim: set ft=jinja2.rst #}
