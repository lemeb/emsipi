> [!WARNING]
> This spec is a little out of date, and should be updated to reflect the
> actual state of the codebase.

The configuration is made of three types of attributes:

* Internal attributes, which can never be set by the configuration files (see
  [Configuration files](#configuration-files)). An example of an internal
  attribute is `working_directory`.
* External, explicit attributes, which are either `None` (which can be
  converted or not into a default value) or are the value explicitly defined in
  the configuration files. Such attributes include `server_name` or
  `providers.google.project`.
* External, potential implicit attributes. These are attributes that can be
  defined by the configuration files or can be inferred by the program. In such
  cases, we need to make a distinction between the value that was passed in the
  configuration file and the value inferred by the program. In such case, we
  will store two configuration attribute: an internal one that tracks the "raw"
  value defined in the configuration file and the inferred one. For instance,
  the attribute `runtime` can be set, in the configuration file, to either
  `"auto"` (the default value), `None` (with the key being blank or not present,
  which should trigger the default value), or one of the possible runtime
  values (`uv`, `python-pip`, or `node`). This would translate to two
  attributes: `raw_runtime` and `runtime`, which would respectively be the raw
  and the inferred value. It is possible, thanks to the `alias` property of
  `pydantic.Field`, to execute this swap. Taking back the three scenarios laid
  out above, the raw and inferred attributes would be, respectively, `"auto"`
  and `"<inferred_value>"`, `"auto"` and `"<inferred_value>"`, and (for example)
  `"uv"` and `"uv"`.

## Configuration files

There are two `emsipi` configuration files: `emsipi.yaml` and
`emsipi.private.yaml`. They are functionally equivalent, with a few exceptions:

1. `emsipi.private.yaml` is meant to hold secrets, and therefore by convention
   should not be committed to source control.
2. Values of `emsipi.private.yaml` should override values in `emsipi.yaml`. The
   override happens at the lowest possible value of granularity. If the private
   file has a `key1.key2.key3` value, it should replace only `key1.key2.key3`,
   not the entire `key1` or `key1.key2`. For now, overrides of a key that
   expects a list value are complete overrides, and not extensions.
3. When automatically generating `emsipi.yaml` files (see below), some keys
   flagged as private will be written to `emsipi.private.yaml` instead of
   `emsipi.yaml`.

> [!NOTE]
> In configuration files, keys will use dashes as delimiters; in Python
> code, keys will use underscores. In this document, keys might use either
> convention: `server_name` and `server-name` are therefore equivalent.

## `emsipi deploy` flow

When a user uses `emsipi deploy`, the following happens:

### Definition of the working directory

The working directory of the script is defined by the `--directory` argument.
If such argument is not present, the current working directory becomes the
script's working directory, which will be present in our configuration under
the `working_directory` attribute.

### Detection of `empsipi` configuration files

The script should be looking for either configuration file in the
`working_directory`. If no file is found, then `do_generate_config_files`
should be set to `True`. In this case, a configuration wizard should appear.
Otherwise, the script should consider that the configuration needs to be parsed
and collect errors as it goes along.

### Parsing mechanism

If possible, the parsing should be done as much as possible with the context
of Pydantic. The validation modules, value inference mechanisms, and so forth,
should be done within `BaseModel`s if feasible. This makes it much easier to
reason about and maintain.

Normally, one advantage of Pydantic is that it returns _all_ the validation
errors instead of just the first one, which should be useful to display to the
user. Note that we should try as much as possible to validate as many fields as
possible, even if some errors were raised before. This is to ensure that
users can fix as many errors as possible in one go, instead of having to fix
one error, run the command again, and fix the next one.

### Configuration wizard

The configuration wizard should use the `rich` library to be as user-friendly
as possible. It should follow the general structure of this flow. We will
periodically give instructions about how the wizard should behave at each step
of this flow.

### (Step 1) Server name

One mandatory attribute in `emsipi` is `server_name`. It needs to be
explicitly defined by the user, either in the wizard or the configuration files.
It has to be a name that uses letters, digits, and dashes (to follow cloud
naming conventions).

### (Step 2) Server file or command

The other mandatory attribute is `server_file` (or `server_command`). Both
fields have exactly the same meaning, and are mutually exclusive. (They are
essentially aliases of each other.)

If the configuration file has values for both `server_file` and
`server_command`, the script should raise a validation error. If neither is
defined, the script should raise a validation error as well.

The `server_file` attribute is the path to the server file that will be run
when the server is started. It can be a relative or absolute path, but if the
path is above the working directory, it should be considered a validation
error. It can end with either `.py` or `.js`; if not, it should be considered
a validation error as well.

The `server_command` attribute is the command that will be run when the server
is started. It is a single string that can contain any command that can be used
to run the server.

The configuration wizard will ask the user to define either the `server_file`
or the `server_command` under a single prompt: "Please write either the path
to the server file or the command to run the server."

The result of parsing one of these two attributes should be stored in the
internal attributes `server_file_or_command` (the raw value) and
`is_server_file` (a boolean that is `True` if the value is a file path and
`False` if it is a command). In the `Pydantic` model, the `server_file`
and `server_command` should only return values if they are not `None` (in other
words, in any given object, only one of the two attributes should be
defined). Obviously, only `server_file` should work if `is_server_file`
is `True`, and only `server_command` should work if `is_server_file`
is `False`.

### (Step 3) `Dockerfile` detection

The attribute `dockerfile` allows the user to give the (relative or absolute)
path to a Dockerfile. The default value of `dockerfile` is `./Dockerfile`.

We obey the following conditions:

1. If the file at `dockerfile` doesn't exist, we set `do_generate_dockerfile` to
  `True.`
2. If the file at `dockerfile` exists, we look at its first line:
  1. If it contains `# OVERWRITE: OK`, it means it was automatically generated
    and can be overwritten. In this case, `do_generate_dockerfile` is set
    to `True`.
  2. If it does not, we consider that the `Dockerfile` is meant to be used as is,
    and we will not touch it. `do_generate_dockerfile` is set to `False`.
    **Skip to Step XXXXXX.**

> [!TIP]
> **What if I want to keep my `Dockerfile`, but want `emsipi` to generate
> another?** In this case, just set the value of `dockerfile` to the path where
> you want your generated `Dockerfile` to reside.

The configuration wizard follows the following logic:

1. If `./Dockerfile` exists, it asks "Do you want to use your existing
   Dockerfile?".
   1. If `"Yes"`, it sets `dockerfile` to `./Dockerfile`,
      `do_generate_dockerfile` to `False`, and **skips to Step XXXX**.
   2. If `"No"`, it sets `dockerfile` to `./emsipi/Dockerfile`,
     `do_generate_dockerfile` to `True`, and **skips to Step XXXX**.
2. If `./Dockerfile` does not exist, it asks "Where do you want your
   Dockerfile to be generated?", with the default value being
   `./Dockerfile`. It then **skips to Step XXXX**.

### (Step 4) Detect the command structure

The next few steps will be here to generate the `Dockerfile` properly. The
first order of business will be to detect how the server will be run. This will
be stored in the `command_type` attribute, which can take the following values:

1. **`python`**: Using `python <file>`;
2. **`node`**: Using `node <file>`;
3. **`shell`**: Using a shell command, such as `<cmd>`.

We use simply by detecting the server file extension:

1. If `is_server_file` is `False` (meaning that the server file is a
   command):
  1. we set `command_type` to `shell`.
  2. We set `raw_runtime` to `auto`.
  3. **Skip to Step 5A** to set `runtime`.
2. If `is_server_file` is `True` (meaning that the server file is a
   file path):
  1. If the server file extension is `.py`:
     1. we set `command_type` to `python`;
     2. we set `raw_runtime` to `python`;
     3. we skip to step 5A, which will set `runtime` to `python`;
     4. **we skip to step 5B**.
  2. If the server file extension is `.js`:
     1. we set `command_type` to `node`;
     2. we set `raw_runtime` to `node`;
     3. we skip to step 5A, which will set `runtime` to `node`;
     4. **we skip to step 5C**.

### (Step 5) Runtime options

In order for the command or file to execute properly, the `Dockerfile` might
need to have installed some dependencies (in the case of `node` or `python`),
and perhaps to have compiled some code (in the case of `node`). This means that
we need to know the following:

1. Whether we are in a `node` or `python` environment (which will be critical
   to determine the base image to use). This needs to be determined only if
   `command_type` is `shell`.
2. If `python`:
   1. which version of `python` we are using;
   2. whether to resolve the dependencies from `requirements.txt`, from
      `pyproject.toml`, or `uv.lock`.
3. If `node`:
   1. which version of `node` we are using;
   2. and whether to run `npm run build` (which is mandatory for TypeScript
      projects).

First, we run the following detection tests, stored in attributes:

1. `server_file_exists`: whether the server file exists or not.
2. `uv_lock_present`: whether the `uv.lock` file is present in the
  `working_directory`.
3. `deps_in_pyproject`: whether the `pyproject.toml` file is present in the
  `working_directory` and that it contains a `dependencies` key
  under the `project` section.
4. `requirements_txt_present`: whether the `requirements.txt` file is present
  in the `working_directory`.
5. `any_python_config_file_present`: should be set to `True` if any of
  `uv_lock_present`, `deps_in_pyproject`, or `requirements_txt_present`
  is `True`.
6. `package_json_present`: whether the `package.json` file is present in the
  `working_directory`.

(From a `Pydantic` perspective, you might want to check these attributes
earlier in the validation process.)

#### (Step 5A) Runtime detection

We need to set the `runtime` attribute. The
attribute `runtime` can be set explicitly through the CLI or the
configuration file, or it can set it to `"auto"`. The other possible values
are `python` and `node`. If `raw_runtime` is either of these two values,
we set `runtime` to the value of `raw_runtime`. If it is set to
`"auto"`, we will try to detect the runtime automatically. If the value is
not set, we will set it to `"auto"`.

1. If `any_python_config_file_present` is `True`:
  1. If `package_json_present` is `True`, we raise a validation error with
      a message asking the user to define the `runtime` attribute to either
      `python` or `node`. If the configuration wizard is active, though (e.g.
      `do_generate_config_files` is `True`), we will ask the user to define
      the `runtime` attribute.
  2. If `package_json_present` is `False`, we set `runtime` to `python`. We
     **skip to Step 5B**.
2. If `any_python_config_file_present` is `False`:
  1. If `package_json_present` is `True`, we set `runtime` to `node`. We
     **skip to Step 5C**.
  2. If `package_json_present` is `False`, we raise a validation error
     with a message telling the user that `emsipi` does not know how to run
     the server. We remind users that the working directory is `cwd` by
     default, that `emsipi` is meant to be run in the directory at the root of
     the project, and that they can use the `--directory` argument to change
     the working directory.

In the configuration wizard, we will ask the user to define the `runtime`
attribute, but we can use the inferred value to set the default value.

From a `Pydantic` perspective, it might be wise to run this step as the
default / validator of the `runtime` attribute, using only `raw_runtime`
as the input value.

#### (Step 5B) Python dependencies and version detection

The parameter `python_dependencies_file` is the path to the file that
contains the Python dependencies. It can be set in the configuration file or
through the CLI. It can be either `requirements.txt`,
`pyproject.toml`, `uv.lock`, or `auto`. The default value is `auto`, which
means that `emsipi` will try to detect the file automatically. If the `runtime`
is not `python`, a validation error is raised.

We run the following logic if `raw_python_dependencies_file` is
`auto`:

1. If `uv_lock_present` is `True`:
  1. If `requirements_txt_present` is `False`, we set
      `python_dependencies_file` to `uv.lock`.
  2. If `requirements_txt_present` is `True`, we raise a warning that
      `uv.lock` will be used, but that `requirements.txt` will not be used.
      We set `python_dependencies_file` to `uv.lock`.
2. Else if `requirements_txt_present` is `True`:
  1. If `deps_in_pyproject` is `True`, we raise a warning that
      `requirements.txt` will be used, but that `pyproject.toml` will not be
      used. We set `python_dependencies_file` to `requirements.txt`.
  2. If `deps_in_pyproject` is `False`, we set `python_dependencies_file` to
  `requirements.txt`.
3. Else if `deps_in_pyproject` is `True`, we set `python_dependencies_file` to
  `pyproject.toml`.
4. If `any_python_config_file_present` is `False`, we raise a validation error that
  tells the user that no Python dependencies file was found, and that they
  should either create one or set the `python_dependencies_file` attribute
  to a valid file.

For the configuration wizard, we will ask the user to define the
`python_dependencies_file` attribute, but we can use the inferred value to
set the default value.

For the Python version, we will use the `python_version` attribute. It can be
set in the configuration file or through the CLI. It should be a valid major
Python version (e.g. `3.10`, `3.11`, etc.). If not set, the default value
will be `auto`, which means that `emsipi` will try to detect the Python
version automatically. If the `runtime` is not `python`, a validation
error is raised.

We run the following logic if `raw_python_version` is `auto`:

1. If `python_dependencies_file` is `uv.lock`, we set
   `python_version` to the key `requires-python` in the `uv.lock`
   file. If the key is not present, we raise a validation error.
2. If `python_dependencies_file` is `pyproject.toml`, we set
   `python_version` to the key `project.requires-python` in the `pyproject.toml`
   file. If the key is not present, we raise a validation error.
3. If `python_dependencies_file` is `requirements.txt`, we raise a validation
   error that tells the user that `emsipi` does not know how to detect the
   Python version from `requirements.txt`. We ask the user to set the
   `python_version` attribute to a valid major Python version.

For the configuration wizard, we will ask the user to define the
`python_version` attribute, but we can use the inferred value to set the
default value. If no default value can be inferred, we will set the
default value to `3.11`.

#### (Step 5C) Node build and version

The parameter `run_npm_build` is a boolean that indicates whether to run the
`npm run build` command in the `Dockerfile`. The default value is `False`.
If the `runtime` is not `node` and the value is set, a validation error is
raised.

In the configuration wizard, we will ask the user whether they want to run
the `npm run build` command. If the user answers "Yes", we will set
`run_npm_build` to `True`. If the user answers "No", we will
set `run_npm_build` to `False`. Obviously, this question should be asked only
if the `runtime` is set to `node`.

We also try to detect the Node version. The parameter `node_version` is the
version of Node to use. It can be set in the configuration file or through the
CLI. It should be a valid major Node version (e.g. `18`, `20`, etc.). If
not set, a validation error is raised. If this value is set and `runtime` is
not `node`, a validation error is raised as well.

In the configuration wizard, we will ask the user to define the `node_version`
attribute, but we can use the inferred value to set the default value. If no
default value can be inferred, we will set the default value to `20`. Obviously,


###
