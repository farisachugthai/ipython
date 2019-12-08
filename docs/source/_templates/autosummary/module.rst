{{ fullname | escape | underline }}

.. automodule:: {{ fullname }}

   {% block classes %}
   {% if objtype in ['class'] %}
     {# Also could do
   {% if classes %}
     #}
   .. rubric:: Classes

   .. autosummary::
      :show-inheritance:
      :members:
   {% for item in classes %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block functions %}
   {% if functions %}
   .. rubric:: Functions

   .. autosummary::
   {% for item in functions %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block exceptions %}
   {% if exceptions %}
   .. rubric:: Exceptions

   .. autosummary::
   {% for item in exceptions %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}
  {{ objtype | escape | underline }}

.. auto{{ objtype }}:: {{ objname }}
    :members:

{% endif %}

.. raw:: html

    <div class="clearer"></div>

{# Vim: set ft=htmljinja.rst: #}
