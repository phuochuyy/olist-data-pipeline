{#
  Use the configured schema name as-is (staging, marts, analytics) instead of dbt's
  default "<target schema>_<custom schema>" (public_staging, public_marts, ...),
  so dbt models live next to the Spark tables of the same layer.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
