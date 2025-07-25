# Test fixtures

## Overview

This directory contains reusable fixture files for configuration testing.
These files can be referenced in test cases using the `fixture:filename` syntax.

### Server Files

- `simple_server.py`: Basic FastMCP server without additional tools
- `server_with_tool.py`: FastMCP server with an example `add` tool
- `server_basic.js`: Basic MCP server in Node.js

### Configuration Files

- `emsipi_simple.yaml`: Basic emsipi configuration with Google provider
- `emsipi_simple_version.yaml`: Basic emsipi configuration with Google
  provider and Python version
- `emsipi_manual.yaml`: Configuration for manual test cases
- `emsipi_template.yaml`: Template configuration with variables:
  `{server_name}`, `{project_id}`, `{region}`
- `emsipi_simple_json.yaml`: Basic emsipi configuration with Google provider,
  Node.js runtime, and Node.js version

### Python Dependencies

- `pyproject_basic.toml`: Basic pyproject.toml with minimal dependencies
- `pyproject_with_version.toml`: pyproject.toml including version field
- `pyproject_template.toml`: Template pyproject.toml with variables:
  `{project_name}`, `{version}`, `{python_version}`, `{fastmcp_version}`
- `requirements_basic.txt`: Basic requirements.txt with common dependencies
- `uv_lock_basic.txt`: Basic uv.lock file for UV package manager

### Node.js Dependencies

- `package_basic.json`: Basic package.json for Node.js MCP server

### Legacy Fixtures (Original)

#### `package.json` variants

- `package.0.json`: Empty package.json
- `package.1.json`: Package.json with a name and a version
- `package.2.json`: Same as `package.1.json`, but with a `scripts` section and
 a `build` script

#### `requirements.txt` variants

- `requirements.0.txt`: Empty requirements.txt
- `requirements.1.txt`: Requirements.txt with a single dependency

#### `pyproject.toml` variants

- `pyproject.0.toml`: Empty pyproject.toml
- `pyproject.1.toml`: Pyproject.toml with a `project.requires-python` key
- `pyproject.2.toml`: Pyproject.toml with a `project.requires-python` key,
  but such Python is templated with `{python-version}`

## Template Variables

Template fixtures support variable substitution using Python's `str.format()`
method. Variables are specified in the test case using the `template_vars`
parameter.

Common template variables:

- `{server_name}`: Name of the MCP server
- `{project_id}`: Cloud provider project ID
- `{region}`: Cloud provider region
- `{project_name}`: Python project name
- `{version}`: Project version
- `{python_version}`: Required Python version
- `{fastmcp_version}`: FastMCP dependency version
