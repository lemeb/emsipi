# `tests/config`

<!-- markdownlint-disable MD013 -->

In this directory, you can find various tests for configuring `emsipi`.

## `test_example_cases.py`

| Test name                 | Scenario                                                                                                                                            | Expected output                                                                                                                                                                                                                      |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `simple_existing_config`  | A minimal project, with a working `server.py`, an existing `emsipi.yaml`, and a clear Python dependency file with `pyproject_basic.toml`            | Does not ask for any information in the wizard; properly infers python version, runtime, name and dependency file                                                                                                                    |
| `templated_config_test`   | A minimal project similar to `simple_existing_config`, but using `emsipi_template.yaml` and `pyproject_template.toml`, along with various variables | Does not ask for any information in the wizard; properly infers python version, runtime, name and dependency file, and uses the template variables; the generated `pyproject.toml` and `emsipi.yaml` are correct given the variables |
| `python_server_with_deps` | Python server configuration with dependency management                                                                                              | Properly configures Python runtime with dependency detection                                                                                                                                                                         |
| `test_manual_config_case` | Manual configuration test case                                                                                                                      | Tests manual configuration setup process                                                                                                                                                                                             |

## `test_comprehensive_cases.py`

| Test name                               | Scenario                                                                                                          | Expected output                                                                                                                  |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `python_requirements_txt`               | A minimal project with a `requirements.txt` file                                                                  | Does not ask for any information in the wizard; properly infers python version, runtime, name and dependency file                |
| `python_requirements_txt_no_cli`        | A minimal project with a `requirements.txt` file, but the entrypoint is not the CLI but the actual Python command | Does not ask for any information in the wizard; properly infers python version, runtime, name and dependency file                |
| `node_server_detection`                 | A minimal Node.js project with a `server.js` file and `package.json`                                              | Does not ask for any information in the wizard; properly infers node runtime, node version (20), and sets run_npm_build to False |
| `node_server_detection_no_cli`          | Same as above but using non-interactive arguments instead of CLI                                                  | Same expected output as above                                                                                                    |
| `uv_lock_priority`                      | A project with both `uv.lock` and `requirements.txt` files present                                                | Does not ask for any information in the wizard; properly chooses uv.lock over requirements.txt for Python dependencies           |
| `server_command_test`                   | Uses a shell command instead of a server file                                                                     | Properly sets command_type to "shell" and stores the command in server_command                                                   |
| `complex_template_test`                 | Complex template test with multiple variable substitutions                                                        | Uses template variables to generate correct emsipi.yaml and pyproject.toml files                                                 |
| `private_config_override`               | Project with both public and private configuration files                                                          | Private config values properly override public config values                                                                     |
| `pydantic_validation_empty_server_name` | Configuration with empty server name                                                                              | Validation fails with appropriate error message about empty server name                                                          |
| `test_dockerfile_detection_logic`       | Tests Dockerfile detection and generation logic                                                                   | Properly detects existing Dockerfile(s) and determines whether to generate new ones                                              |
| `both_server_file_and_command`          | Configuration with both server_file and server_command set                                                        | Validation fails with mutually exclusive error                                                                                   |
| `neither_server_file_nor_command`       | Configuration without server_file or server_command                                                               | Validation fails with missing server target error                                                                                |

## `test_wizard_functionality.py`

| Test name                        | Scenario                                              | Expected output                                                                                                                    |
| -------------------------------- | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `test_simple_wizard_interaction` | Manual wizard test with server.py and uv.lock present | Wizard prompts for server_name and accepts defaults for other values; properly configures Python runtime with uv.lock dependencies |

## `test_missing_core_validation.py`

| Test name                         | Scenario                                                    | Expected output                                                                  |
| --------------------------------- | ----------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `invalid_server_name_format`      | Server name with invalid characters (spaces, special chars) | Validation fails with appropriate error message about invalid server name format |
| `server_file_outside_working_dir` | Server file path that is outside the working directory      | Validation fails with error about server file must be within working directory   |
| `server_file_invalid_extension`   | Server file with invalid extension (not .py or .js)         | Validation fails with error about invalid file extension                         |
| `both_server_file_and_command`    | Configuration with both server_file and server_command set  | Validation fails with mutually exclusive error                                   |
| `neither_server_file_nor_command` | Configuration without server_file or server_command         | Validation fails with missing server target error                                |

## `test_missing_runtime_detection.py`

| Test name                       | Scenario                                                 | Expected output                                                    |
| ------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------ |
| `no_dependency_files_present`   | Project with no Python or Node.js dependency files       | Validation fails with helpful error about missing dependency files |
| `python_and_node_deps_present`  | Project with both Python deps (uv.lock) and package.json | Validation fails asking user to specify runtime explicitly         |
| `runtime_auto_detection_python` | Project with only Python dependency files present        | Properly detects runtime as "python" and uses uv.lock              |
| `runtime_auto_detection_node`   | Project with only package.json present                   | Properly detects runtime as "node"                                 |

## `test_python_version_detection.py`

| Test name                               | Scenario                                                           | Expected output                                                 |
| --------------------------------------- | ------------------------------------------------------------------ | --------------------------------------------------------------- |
| `python_version_from_pyproject`         | Python version detection from pyproject.toml requires-python field | Properly extracts and sets python_version from pyproject.toml   |
| `python_version_from_uv_lock`           | Python version detection from uv.lock requires-python field        | Properly extracts and sets python_version from uv.lock          |
| `python_version_requirements_txt_error` | Python version detection with only requirements.txt                | Validation fails asking user to specify python_version manually |

## `test_dependency_warnings.py`

| Test name                             | Scenario                                                   | Expected output                                                            |
| ------------------------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------------- |
| `pyproject_with_uv_lock_warning`      | Project with both pyproject.toml deps and uv.lock          | Uses uv.lock but warns about ignoring pyproject.toml dependencies          |
| `requirements_with_pyproject_warning` | Project with both requirements.txt and pyproject.toml deps | Uses requirements.txt but warns about ignoring pyproject.toml dependencies |

## `test_node_cases.py`

| Test name                           | Scenario                                       | Expected output                                                       |
| ----------------------------------- | ---------------------------------------------- | --------------------------------------------------------------------- |
| `node_version_validation`           | Node.js project without node_version specified | Validation fails asking for node_version                              |
| `node_version_with_python_runtime`  | Node version specified but runtime is Python   | Validation fails with error about node_version only for node runtime  |
| `run_npm_build_with_python_runtime` | run_npm_build specified but runtime is Python  | Validation fails with error about run_npm_build only for node runtime |
| `node_server_with_npm_build`        | Node.js server with run_npm_build set to true  | Properly configures Node.js runtime with npm build enabled            |

## `test_dockerfile_detection.py`

| Test name                        | Scenario                                         | Expected output                                                |
| -------------------------------- | ------------------------------------------------ | -------------------------------------------------------------- |
| `dockerfile_exists_no_overwrite` | Existing Dockerfile without OVERWRITE:OK comment | Sets do_generate_dockerfile to False, uses existing Dockerfile |
| `dockerfile_custom_path`         | Custom Dockerfile path specified in config       | Uses specified Dockerfile path instead of default ./Dockerfile |
| `dockerfile_missing`             | No Dockerfile present in project                 | Sets do_generate_dockerfile to True, uses default path         |

## `test_config_file_handling.py`

| Test name                   | Scenario                                           | Expected output                                                      |
| --------------------------- | -------------------------------------------------- | -------------------------------------------------------------------- |
| `no_config_files_present`   | Project without emsipi.yaml or emsipi.private.yaml | Sets do_generate_config_files to True, triggers wizard mode          |
| `deep_merge_private_config` | Complex nested private config override             | Properly merges nested configuration values from private over public |
| `private_config_only`       | Project with only emsipi.private.yaml file         | Loads configuration from private file only                           |

## `test_google_provider_config.py`

| Test name                         | Scenario                                  | Expected output                                                          |
| --------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------ |
| `google_provider_missing_project` | Google provider config without project ID | Validation fails with error about missing project ID                     |
| `google_provider_default_values`  | Google provider with minimal config       | Properly sets default values for region, artifact_registry, service_name |
| `google_provider_custom_values`   | Google provider with all custom values    | Uses all specified custom values instead of defaults                     |
| `empty_project_id`                | Google provider with empty project ID     | Validation fails with error about empty project ID                       |

## `test_environment_variables.py`

| Test name                   | Scenario                                        | Expected output                                              |
| --------------------------- | ----------------------------------------------- | ------------------------------------------------------------ |
| `environment_variables_set` | Configuration with custom environment variables | Environment variables are properly included in configuration |
