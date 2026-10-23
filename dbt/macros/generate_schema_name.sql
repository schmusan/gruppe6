-- Schema-Namen exakt wie konfiguriert verwenden (raw, staging, marts),
-- statt dbt-Standard "<target>_<schema>".
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name if custom_schema_name is not none else target.schema }}
{%- endmacro %}
