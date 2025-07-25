# Instructions for `emsipi` repository

## General instructions

- Use ultrathink as much as you can.

## Specification

The ultimate goal of this library is the following:

You want to build a MCP server using FastMCP. Maybe you want to build it _fast_,
so you can build multiple servers (e.g. one to interact with Google Sheets, one
for Todoist, one for Pinboard, etc.).

It's relatively easy these days to have a server running locally. Over the
internet, however, so you can use it, say, on your mobile phone? Nightmare
stuff.

The idea here is that you can have some relatively simple MCP server code,
and deploy it to a cloud provider (e.g. GCP, AWS, Azure) with a single command.

### Simple idea

Let's say you have this simple MCP server code:

```python
from fastmcp import FastMCP

mcp = FastMCP("Demo 🚀")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

if __name__ == "__main__":
    mcp.run()
```


You should be able to run it locally with:

```bash
# Assuming everything is installed correctly
python mcp_server.py
uv run mcp_server.py
fastmcp run mcp_server.py # Works as well
```

Now you should be able with emsipi to do this:

1. Have a `emsipi.yaml` (or `emsipi.private.yaml`, see [Configuration](#configuration)) file with config such as:

```json
providers:
  google:
    project: your-project-id
```

2. Run the following command to deploy your MCP server:

```bash
# Assuming you have emsipi installed and configured (or uvx)
emsipi deploy mcp_server.py
```

```txt
Deploying MCP server to Google Cloud Platform...
Succesfully deployed after 5 minutes 43 seconds.
You can now access your MCP server at: https://your-project-id.cloudfunctions.net/mcp
```

A more concrete example in this repository should be found with the
`examples/simple-server` directory. We should be able to run it as such:

```bash
cd examples/simple-server && emsipi deploy google server.py
```

#### What happens under the hood?

This command here should:

1. Read the configuration (see [Configuration](#configuration) below). In the
   case of `simple-server`, looking

1. Figure out the cloud provider you want to use (here, GCP, because it's
   the only one configured in `emsipi.private.yaml`). Check if the provider is
   configured correctly (e.g. if you have the right credentials, etc.).
2. Check that the MCP server code is valid (probably through `fastmcp inspect`).
3. Check whether the environment uses `uv` or `pip`. It does so this way:
   - If there is a `uv.lock` file, we will use `uv`.
   - If there is a `pyproject.toml` file with a `dependencies` section, we
     will use `uv`. If we detect a `requirements.txt` file, we will throw an
     warning.
   - Otherwise, if there is a `requirements.txt` file, we will use `pip`.
   - If there is neither, we throw an error.
4. Write a Dockerfile according to all of this, respecting the working directory
   and the package manager you have chosen.
5. Uses CDKTF to deploy the Dockerfile to the cloud provider. The idea is to use
   CDKTF for every cloud provider. (See [Internals](#internals).)

### Configuration

We use a configuration file of the form found in `emsipi.yaml`. Note that you
can have a private configuration file called `emsipi.private.yaml`, which
should not be tracked by git, and whose values will override the values in
`emsipi.yaml`.

Internally, we should parse these values with `pydantic` and use them to
configure the MCP server.

### Middlewares

We want to support two types of middlewares:

1. ASGI middlewares.
2. FastMCP middlewares.

Some of them are defined in the `emsipi.middlewares` module.

### Internals

#### Repo structure

The repo structure is the following:

- `examples/`: Examples of MCP servers. They should be self-contained and
  runnable with `emsipi deploy`.
- `src/emsipi/`: The source code of the emsipi library.
  - `deploy/`: The source code for the `deploy-internal` sub-command.
- `terraform/`: Old code, to be removed eventually. Keep it for now as reference.
- `tests/`: Tests for the emsipi library.

### CDKTF

One complication of CDKTF is that it's `deploy` command is weird. You cannot
trigger it through Python, but you have to use the CLI. You also have to pass
the command necessary to execute the `synth` command.

Because our synth script requires information about the location of the
entry point and the working directory, we need to pass these information to
the `synth` script. Probably the best way to do it is to have an internal
sub-command that will be used to trigger the `synth` command (e.g.
`emsipi synth-internal`).

### CLI reference

#### `emsipi deploy`

This command will deploy the MCP server to the cloud provider.

The syntax is:

```
emsipi deploy <provider> <server-file> [--directory <directory>] [--pkg-mgr <pkg-mgr>]
```

The arguments are:

- `<provider>`: The cloud provider you want to use. Mandatory. For now, only
  `google` is supported.
- `<server-file>`: The file containing the MCP server code. Mandatory.
- `--directory <directory>`: The directory of the MCP server. It is from which
  the MCP server will be run. This directory needs to contain the emsipi config
  file (e.g. `emsipi.yaml` or `emsipi.private.yaml`) as well as the Python
  dependencies. It does not need to be the directory where the server file is
  located. Optional. Defaults to the current directory.
- `--pkg-mgr <pkg-mgr>`: The package manager you want to use. Mandatory. Values
  include `uv`, `pip`, or `auto`. Defaults to `auto`. If `auto`, we will use
  the detection procedure outlined in the [Internals](#internals) section.

#### `emsipi synth-internal`

This command will trigger the `synth` command of CDKTF.

The syntax is:

```
emsipi synth-internal <provider> <server-file> [--directory <directory>] [--pkg-mgr <pkg-mgr>]
```

The arguments are:

- `<provider>`: The cloud provider you want to use. Mandatory. For now, only
  `google` is supported.
- `<server-file>`: The file containing the MCP server code. Mandatory.
- `--directory <directory>`: The directory of the MCP server. It is from which
  the MCP server will be run. This directory needs to contain the emsipi config
  file (e.g. `emsipi.yaml` or `emsipi.private.yaml`) as well as the Python
  dependencies. It does not need to be the directory where the server file is
  located. Optional. Defaults to the current directory.
- `--pkg-mgr <pkg-mgr>`: The package manager you want to use. Mandatory. Values
  include `uv`, `pip`, or `auto`. Defaults to `auto`. If `auto`, we will use
  the detection procedure outlined in the [Internals](#internals) section.

#### `emsipi internal-config`

This command will parse the same arguments as `emsipi deploy` and
`emsipi synth-internal`, and return the internal configuration that will be used
to deploy the MCP server. This is useful for debugging and testing purposes.


## References

- Model Context Protocol documentation: https://modelcontextprotocol.io/llms-full.txt
- FastMCP documentation: https://gofastmcp.com/llms.txt

## Good practices

- **Checking code**: Use `uv run ruff format . && uv run ruff check . --fix`, then `make check-strict-all` to check your code.
  - One quirk of `make check-strict-all` is that it will run `ruff`'s preview rules. If
    you want to comment such rule out, you cannot do it in the file; it will be
    removed by `ruff format`. Instead, you should update the `ruff-strict.toml` file
    where these exceptions are documented. YOU SHOULD DOCUMENT THE RULE PER FILE,
    NOT FOR THE ENTIRE CODEBASE. And every exception should be documented with a
    comment explaining why the rule is not applied in that file.
  - If you're wondering if a rule is in preview: if it appears during
    `make check-strict-all`, but not during `make check`, then it is a preview
    rule.

- **Code practices**:
  - We use Python >=3.11, so write constructs accordingly.
  - Don't use `print`; instead use the `logging` module and the `rich` library (`print` and `Console`.)
  - You can use `# type: ignore[error-code]` (mypy),
    `# pyright: ignore[ErrorCode]` (pyright), and `# noqa: ERRORCODE` (ruff).
    If multiple go on the same line, they should go with mypy first. Use them
    only as last resort, when no better solution is available. (An example where
    this is warranted is if `Any` is really the only type that works, or if you
    need to use a third-party library that is not typed.) Some pointers on which
    errors to just comment out are specified below.
  - IMPORTANT! Don't hesitate to over-document. Please ensure that when you modify a
    function, you also update the doc string. If you add a new parameter, please
    document it. Don't forget to put "args", "returns", and "raises" in the
    doc string. THIS IS ONE VERY COMMON LINTING MISTAKE!
  - The max line length is 80 characters. Yes, the formatter will sometime just
    reformat the code, but some lines (e.g. docstrings) will need to be modified
    accordingly.
  - The right way to pass a message to an exception is to define a `msg`
    variable, and then pass it to the exception.
  - Put `@final` whenever needed. Helps for type-checking.
  - Put `@override` whenever needed (and it's generally more often than you
    think). Helps for type-checking.
  - Any time you define an empty list, try to type-hint it (e.g.
    `my_list: list[str] = []`).
  - Be mindful of class methods that don't use the `self` parameter. If you
    don't use it, you should make it static.

- **Documentation practices**:
  - Whenever possible, any references to a file or library (or really any piece
    of code) should be surrounded with backticks. Don't say ("we detect uv.lock",
    say "we detect `uv.lock`").

- **Handling linting and type-checking errors** (these are misc notes):
  - In general, if we're dealing with operations that inherently deal with `Any`
    or `Unknown` (e.g. because you're parsing JSON, because you're dealing with
    a third-party library that is not typed, etc.), you can safely put ignore
    comments for: `reportUnknownArgumentType`, `reportUnknownMemberType`,
    `reportUnknownVariableType`, `reportUnknownParameterType`,
    `reportUnknownType`, `reportAny`, `reportExplicitAny`, etc. (`pyright`), and
    `ANN401` (`ruff`).
  - In some cases, you can put `object` as the type, but this is not
    recommended. If you do so, please document why you did it.
