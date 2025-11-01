#!/bin/bash
# Helper script to run cypher-shell queries easily

# Unset problematic Java options
unset JAVA_TOOL_OPTIONS

# Read credentials from .env
source .env

# Run cypher-shell with connection details
cypher-shell -a "$NEO4J_URI" -u "$NEO4J_USERNAME" -p "$NEO4J_PASSWORD" "$@"
