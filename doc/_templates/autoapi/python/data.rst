{% if obj.display %}

{% set suffix = 1 + obj.obj.name|length %}
{% set module_name = obj.obj.full_name[:-suffix] %}
{% set module = obj.app.env.autoapi_objects[module_name]|default (None) %}

{% if module is none %}
.. py:{{ obj.type }}:: {{ obj.name }}
   {%+ if obj.value is not none or obj.annotation is not none -%}
   :annotation:
        {%- if obj.annotation %} :{{ obj.annotation }}
        {%- endif %}
        {%- if obj.value is not none %} = {%
            if obj.value is string and obj.value.splitlines()|count > 1 -%}
                Multiline-String

    .. raw:: html

        <details><summary>Show Value</summary>

    .. code-block:: text
        :linenos:

        {{ obj.value|indent(width=8) }}

    .. raw:: html

        </details>

            {%- else -%}
                {{ obj.value|string|truncate(100) }}
            {%- endif %}
        {%- endif %}
    {% endif %}


   {{ obj.docstring|indent(3) }}
{% else %}
.. py:{{ obj.type }}:: {{ obj.name }}

   {{ obj.docstring|indent(3) }}

.. undocinclude:: /../src/{{ module.obj.relative_path }}
   :language: {{ module.language }}
   :lines: {{ obj.obj.from_line_no }}-{{ obj.obj.to_line_no }}
{% endif %}
{% endif %}
