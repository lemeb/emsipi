# Testing the configuration

We should use `pytest` to test the configuration. We'll use
`pytest.mark.parameterize` to run many similar tests

## Config generation tests

Each test should have the following parameters:

1. **`emsipi.yaml`/`emsipi.private.yaml`**: This should define the content of
   the `emsipi.yaml` and `emsipi.private.yaml` files. They should be stored in
   two dictionaries (`public_config` and `private_config`). They do not have to
   be present; if so, this means the files are not present.

2. **Files**: This should define, in the working directory, what files should be
   present and with what content. This should be a dictionary with the key being
   the file path and the value being the content. To simplify processing of
   `emsipi.yaml` files, the dictionary should not contain the raw YAML, but a
   piece of code like `yaml.dumps(public_config)`. Otherwise, the dictionary
   should contain things like `{"Dockerfile": "..."}`.
   - It's fine to have a key with a directory `dir/file.txt`. We will create the
     directories automatically.
   - All the files will be created in a virtual directory, so every path should
     be relative.
   - Re-usable file contents are totally OK, even encouraged. We can find the
     re-usable files in the `tests/fixtures` directory, and they should be
     properly documented in `tests/fixtures/README.md`.
   - These re-usable files can be templates with `{variable}` in them. In this
     case, they should be formatted with the `format` method of the `str` class.

3. **CLI arguments**: This should define was is passed to the CLI. It should be
   the raw text passed to the command line (e.g.
   `emsipi internal-config google --arg val`). If some operations should be
   performed before (e.g. `cd`), they should be mentioned in this command.

4. **Environment variables**: This should be the environment variables passed to
   the CLI.

5. **Wizard behavior**: This should define the expected flow of the wizard. It
   should be a list of tuples of two. Each tuple represents a step: the first
   string should be some text the terminal should have displayed since the last
   step, and the second is the input in the terminal (omitting "/n", which
   should be automatically added). If the check with the first string in the
   tuple fails, this should be considered an error.

6. **Expected configuration**: This should define a dictionary of a subset of
   the generated configuration. It's not necessary to define all expected keys
   and values, just the ones that are relevant to the test. The value should be
   exact, if not, this should be considered an error.

7. **Expected files**: This should be a dictionary of a subset of the generated
   files. The key should be the path, and the value should be a regex or a list
   of regex. Each regex should be an exact match; if not, this should be
   considered an error.

## Running the tests

In order to reduce I/O load, we should pre-load the files (especially the files
in `tests/fixtures` that are meant to be re-used) in memory, instead of doing
this every time we load the data related to one specific test.

After this, we should do the following operations to execute each test:

1. We should work in a virtual directory (`tests/tmp`). It should be completely
   empty at the start of each test.

2. Parse the YAML of `public_config` and `private_config` (if available) and
   write them to `emsipi.yaml` and `emsipi.private.yaml`.

3. Write the files in the virtual directory according to the files parameters.

4. We execute the CLI with the arguments and environment variables that have
   been set.

5. We surveil the output of the CLI so that, if it asks for input, we check
   what's been displayed to stdout and compare it to the strings present in the
   wizard behavior parameters. If the check passes, we fill the input defined in
   these parameters, and move on.

6. At the end of the process, we should get a JSON in the stdout. This should be
   parsed and compared to the expected configuration parameter.

7. Then we check the files that were created during the execution of the CLI.

8. We clean the virtual directory and move on.
