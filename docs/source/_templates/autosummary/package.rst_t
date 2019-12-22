{# Override Sphinx's default template and use the module template in place #}
{%- if show_headings %}
{%- if show_headings %}
{{- [basename, "module"] | join(' ') | e | heading }}

{% endif -%}
.. automodule:: {{ qualname }}
{%- for option in automodule_options %}
   :{{ option }}:
{%- endfor %}

{{- [basename, "module"] | join(' ') | e | heading }}

{% endif -%}
.. automodule:: {{ qualname }}
{%- for option in automodule_options %}
   :{{ option }}:
{%- endfor %}

