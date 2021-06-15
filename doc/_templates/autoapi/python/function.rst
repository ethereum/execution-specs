{% if obj.display %}

{{ obj.summary|prepare_docstring }}

.. function:: {{ obj.short_name }}({{ obj.args }}){% if obj.return_annotation is not none %} -> {{ obj.return_annotation }}{% endif %}

   :noindexentry:
{% for (args, return_annotation) in obj.overloads %}
              {{ obj.short_name }}({{ args }}){% if return_annotation is not none %} -> {{ return_annotation }}{% endif %}

{% endfor %}
   {% if sphinx_version >= (2, 1) %}
   {% for property in obj.properties %}
   :{{ property }}:
   {% endfor %}
   {% endif %}


{% endif %}

{% set suffix = 1 + obj.obj.name|length %}
{% set module_name = obj.obj.full_name[:-suffix] %}
{% set module = obj.app.env.autoapi_objects[module_name] %}

.. literalinclude:: /../src/{{ module.obj.relative_path }}
   :language: {{ module.language }}
   :lines: {{ obj.obj.from_line_no }}-{{ obj.obj.to_line_no }}
