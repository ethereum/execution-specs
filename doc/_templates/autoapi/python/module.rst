{#
   Modified from:
      https://github.com/readthedocs/sphinx-autoapi/blob/83b1260e67a69b5c844bcce412e448889223dea8/autoapi/templates/python/module.rst
#}
{% if not obj.display %}
:orphan:

{% endif %}
.. py:module:: {{ obj.name }}

{% if obj.docstring %}
{{ obj.docstring|prepare_docstring }}
{% endif %}

.. only:: stage1

   {% block subpackages %}
   {% set visible_subpackages = obj.subpackages|selectattr("display")|list %}
   {% if visible_subpackages %}
   Subpackages
   -----------
   .. toctree::
      :titlesonly:
      :maxdepth: 3

   {% for subpackage in visible_subpackages %}
      {{ subpackage.short_name }}/index.rst
   {% endfor %}


   {% endif %}
   {% endblock %}
   {% block submodules %}
   {% set visible_submodules = obj.submodules|selectattr("display")|list %}
   {% if visible_submodules %}
   Submodules
   ----------
   .. toctree::
      :titlesonly:
      :maxdepth: 1

   {% for submodule in visible_submodules %}
      {{ submodule.short_name }}/index.rst
   {% endfor %}


   {% endif %}
   {% endblock %}
{% block content %}
{% if obj.all is not none %}
{% set visible_children = obj.children|selectattr("short_name", "in", obj.all)|list %}
{% elif obj.type is equalto("package") %}
{% set visible_children = obj.children|selectattr("display")|list %}
{% else %}
{% set visible_children = obj.children|selectattr("display")|rejectattr("imported")|list %}
{% endif %}
{% if visible_children %}
{{ obj.type|title }} Contents
{{ "-" * obj.type|length }}---------

{% set visible_classes = visible_children|selectattr("type", "equalto", "class")|list %}
{% set visible_functions = visible_children|selectattr("type", "equalto", "function")|list %}
{% set visible_attributes = visible_children|selectattr("type", "equalto", "data")|list %}
{% if "show-module-summary" in autoapi_options and (visible_classes or visible_functions) %}
{% block classes scoped %}
{% if visible_classes %}
Classes
~~~~~~~

.. autoapisummary::

{% for klass in visible_classes %}
   {{ klass.id }}
{% endfor %}


{% endif %}
{% endblock %}

{% block functions scoped %}
{% if visible_functions %}
Functions
~~~~~~~~~

.. autoapisummary::
   :nosignatures:

{% for function in visible_functions %}
   {{ function.id }}
{% endfor %}


{% endif %}
{% endblock %}

{% block attributes scoped %}
{% if visible_attributes %}
Attributes
~~~~~~~~~~

.. autoapisummary::

{% for attribute in visible_attributes %}
{%+ if attribute.docstring != "autoapi_noindex" -%}
{{ attribute.id|indent(3, True) }}
{% endif %}
{% endfor %}


{% endif %}
{% endblock %}
{{ obj.type|title }} Details
{{ "-" * obj.type|length }}---------
{% endif %}
{% for obj_item in visible_children %}
{% if obj_item.display %}

{{ obj_item.short_name }}
{{ '~' * obj_item.short_name|length }}

{% endif %}
{{ obj_item.render()|indent(0) }}
{% endfor %}
{% endif %}
{% endblock %}
