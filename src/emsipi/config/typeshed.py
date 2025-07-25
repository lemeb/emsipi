"""Typeshed for the config module."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, override

from rich.prompt import Prompt
from typing_extensions import TypeVar

if TYPE_CHECKING:
    from rich.text import Text

DefaultType = TypeVar("DefaultType", default=str)


class CustomPrompt(Prompt):
    """Custom prompt class overriding `rich.prompt.Prompt`."""

    @override
    def make_prompt(self, default: DefaultType) -> Text:
        """Make prompt text.

        Args:
            default (DefaultType): Default value.

        Returns:
            Text: Text to display in prompt.
        """
        prompt = self.prompt.copy()
        prompt.end = ""

        if self.show_choices and self.choices:
            choices_text = "/".join(self.choices)
            choices = f"[{choices_text}]"
            _ = prompt.append("\n")
            _ = prompt.append(choices, "prompt.choices")

        if (
            default != ...
            and self.show_default
            and isinstance(default, (str, self.response_type))
        ):
            _ = prompt.append(" ")
            default_text = self.render_default(default)
            _ = prompt.append(default_text)

        _ = prompt.append(self.prompt_suffix)

        return prompt


class Runtime(StrEnum):
    """Inferred runtime."""

    python = "python"
    node = "node"


class CommandType(StrEnum):
    """How the server will be launched."""

    python = "python"
    node = "node"
    shell = "shell"


class PythonDepsFile(StrEnum):
    """Concrete Python dependency file type."""

    requirements = "requirements.txt"
    pyproject = "pyproject.toml"
    uvlock = "uv.lock"
