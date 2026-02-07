#!/usr/bin/env python3
"""
Autonomous loop wrapper for /go-on skill.

Runs /go-on repeatedly until completion or circuit breaker triggers.
This script tracks LOOP metadata (iterations, circuit breaker state),
NOT workflow state — that lives in the tracker/git and is re-derived
by /go-on each invocation.

Usage:
    python .claude/scripts/go_on_loop.py SUN-199
    python .claude/scripts/go_on_loop.py SUN-199 --auto-approve
    python .claude/scripts/go_on_loop.py --max-no-progress 5
"""

from __future__ import annotations

import re
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Annotated

import typer

app = typer.Typer(
    name="go-on-loop",
    help="Autonomous loop wrapper for /go-on skill.",
    no_args_is_help=True,
)


class CircuitState(Enum):
    """Circuit breaker states following Nygard's Release It! pattern."""

    CLOSED = "closed"  # Normal operation
    HALF_OPEN = "half_open"  # Monitoring after issues detected
    OPEN = "open"  # Halted, requires intervention


# Terminal signals that should stop the loop
TERMINAL_SIGNALS = frozenset(
    {
        "<FEATURE_COMPLETE>",
        "<AWAITING_APPROVAL>",
        "<AWAITING_REVIEW>",
    }
)

# Signals that indicate we need user input (stop loop)
AWAITING_SIGNALS_PATTERN = re.compile(r"<AWAITING_INPUT[^>]*>")

# Signals that indicate a blocker (stop loop with error)
BLOCKED_SIGNAL_PATTERN = re.compile(r"<BLOCKED[^>]*>")

# Success signal (reset circuit breaker)
STEP_COMPLETE_SIGNAL = "<STEP_COMPLETE>"


@dataclass
class LoopState:
    """
    Meta-state about the LOOP itself, not the workflow.

    Workflow state (spec exists? plan approved? tasks done?) lives in
    tracker/git and is re-derived by /go-on each invocation.
    """

    iterations: int = 0
    no_progress_count: int = 0
    # Separate counter for BLOCKED signals (allows retries)
    blocked_count: int = 0
    last_signal: str = ""
    errors: list[str] = field(default_factory=list)


def extract_signal(output: str) -> str:
    """Extract the /go-on signal from output."""
    # Check for terminal signals first
    for signal in TERMINAL_SIGNALS:
        if signal in output:
            return signal

    # Check for AWAITING_INPUT with reason
    match = AWAITING_SIGNALS_PATTERN.search(output)
    if match:
        return match.group(0)

    # Check for BLOCKED with reason
    match = BLOCKED_SIGNAL_PATTERN.search(output)
    if match:
        return match.group(0)

    # Check for step complete
    if STEP_COMPLETE_SIGNAL in output:
        return STEP_COMPLETE_SIGNAL

    return ""


def run_go_on(
    issue_ref: str,
    *,
    headless: bool = True,
    auto_approve: bool = False,
) -> tuple[str, int]:
    """Run a single /go-on invocation and return (output, exit_code)."""
    cmd_parts = ["/go-on"]
    if headless:
        cmd_parts.append("--headless")
    if auto_approve:
        cmd_parts.append("--auto-approve")
    if issue_ref:
        cmd_parts.append(issue_ref)

    prompt = " ".join(cmd_parts)
    args = ["claude", "-p", prompt]

    try:
        result = subprocess.run(  # noqa: S603 (trusted input: claude CLI)
            args,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout per invocation
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "ERROR: Claude invocation timed out after 10 minutes", 1
    except FileNotFoundError:
        return "ERROR: 'claude' command not found. Is Claude Code installed?", 1
    else:
        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr
        return output, result.returncode


def print_status(
    state: LoopState,
    circuit: CircuitState,
    signal: str,
) -> None:
    """Print current loop status."""
    typer.echo(f"\n{'─' * 60}")
    typer.echo(
        f"Loop #{state.iterations} | "
        f"Circuit: {circuit.value} | "
        f"No-progress: {state.no_progress_count} | "
        f"Blocked: {state.blocked_count}"
    )
    if signal:
        if signal == STEP_COMPLETE_SIGNAL:
            typer.secho(f"Signal: {signal}", fg=typer.colors.GREEN)
        elif signal.startswith("<BLOCKED"):
            typer.secho(f"Signal: {signal}", fg=typer.colors.RED)
        elif signal.startswith("<AWAITING"):
            typer.secho(f"Signal: {signal}", fg=typer.colors.YELLOW)
        else:
            typer.secho(f"Signal: {signal}", fg=typer.colors.CYAN)
    typer.echo(f"{'─' * 60}\n")


@app.command()
def loop(  # noqa: C901, PLR0912, PLR0913, PLR0915 (CLI entry point)
    issue_ref: Annotated[
        str,
        typer.Argument(help="Issue reference (e.g., SUN-199, #42)"),
    ],
    auto_approve: Annotated[  # noqa: FBT002 (typer bool option)
        bool,
        typer.Option(
            "--auto-approve",
            "-a",
            help="Skip approval gates (use with caution)",
        ),
    ] = False,
    max_no_progress: Annotated[
        int,
        typer.Option(
            "--max-no-progress",
            "-m",
            help="Circuit breaker threshold for consecutive no-progress loops",
        ),
    ] = 3,
    max_blocked: Annotated[
        int,
        typer.Option(
            "--max-blocked",
            "-b",
            help="Max consecutive BLOCKED signals before stopping",
        ),
    ] = 3,
    delay: Annotated[
        float,
        typer.Option(
            "--delay",
            "-d",
            help="Delay in seconds between iterations",
        ),
    ] = 2.0,
    verbose: Annotated[  # noqa: FBT002 (typer bool option)
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show full Claude output",
        ),
    ] = True,
) -> None:
    """
    Run /go-on in an autonomous loop until completion or circuit breaker.

    The loop continues while /go-on outputs <STEP_COMPLETE>.
    It stops on terminal signals, blockers, or circuit breaker.

    Exit codes:
        0 - Feature complete or awaiting approval/review
        1 - Blocked or error
        2 - Circuit breaker triggered
    """
    state = LoopState()
    circuit = CircuitState.CLOSED

    typer.secho(
        f"\nStarting autonomous loop for {issue_ref}",
        fg=typer.colors.BLUE,
        bold=True,
    )
    if auto_approve:
        typer.secho(
            "⚠ Auto-approve enabled — skipping approval gates",
            fg=typer.colors.YELLOW,
        )
    typer.echo(
        f"Circuit breaker: {max_no_progress} no-progress, "
        f"{max_blocked} blocked"
    )
    typer.echo()

    while circuit != CircuitState.OPEN:
        state.iterations += 1

        # Run /go-on
        output, exit_code = run_go_on(
            issue_ref,
            headless=True,
            auto_approve=auto_approve,
        )

        if verbose:
            typer.echo(output)

        # Extract signal
        signal = extract_signal(output)
        state.last_signal = signal

        # Print status
        print_status(state, circuit, signal)

        # Handle terminal signals
        if signal == "<FEATURE_COMPLETE>":
            typer.secho(
                "Feature complete!",
                fg=typer.colors.GREEN,
                bold=True,
            )
            raise typer.Exit(0)

        if signal in {"<AWAITING_APPROVAL>", "<AWAITING_REVIEW>"}:
            typer.secho(
                f"Stopping: {signal}",
                fg=typer.colors.YELLOW,
                bold=True,
            )
            raise typer.Exit(0)

        if AWAITING_SIGNALS_PATTERN.match(signal or ""):
            typer.secho(
                f"Stopping: {signal}",
                fg=typer.colors.YELLOW,
                bold=True,
            )
            raise typer.Exit(0)

        if BLOCKED_SIGNAL_PATTERN.match(signal or ""):
            state.blocked_count += 1
            typer.secho(
                f"Blocked ({state.blocked_count}/{max_blocked}): {signal}",
                fg=typer.colors.RED,
            )
            if state.blocked_count >= max_blocked:
                typer.secho(
                    f"Reached max blocked count ({max_blocked}). Stopping.",
                    fg=typer.colors.RED,
                    bold=True,
                )
                raise typer.Exit(1)
            # Retry — sometimes a fresh invocation helps
            typer.echo("Retrying... (sometimes a fresh invocation helps)")
            time.sleep(5)
            continue

        # Reset blocked count on non-BLOCKED signals
        state.blocked_count = 0

        # Handle errors (non-zero exit with no signal)
        if exit_code != 0 and not signal:
            state.errors.append(output[:200])
            typer.secho(
                f"Error (exit code {exit_code}), no signal detected",
                fg=typer.colors.RED,
            )
            # Fall through to circuit breaker logic (counted as no progress)

        # Circuit breaker logic — increment once per iteration
        if signal == STEP_COMPLETE_SIGNAL:
            # Progress made — reset counter
            state.no_progress_count = 0
            circuit = CircuitState.CLOSED
        else:
            # No progress: either error, unrecognized signal, or no signal
            state.no_progress_count += 1

        # Check circuit breaker thresholds
        if state.no_progress_count >= max_no_progress - 1:
            circuit = CircuitState.HALF_OPEN
            typer.secho(
                f"Circuit breaker: HALF_OPEN "
                f"({state.no_progress_count}/{max_no_progress})",
                fg=typer.colors.YELLOW,
            )

        if state.no_progress_count >= max_no_progress:
            circuit = CircuitState.OPEN
            typer.secho(
                f"\nCircuit breaker OPEN: "
                f"{max_no_progress} consecutive loops with no progress",
                fg=typer.colors.RED,
                bold=True,
            )
            typer.echo("\nRecent state:")
            typer.echo(f"  Last signal: {state.last_signal or '(none)'}")
            typer.echo(f"  Total iterations: {state.iterations}")
            if state.errors:
                typer.echo(f"  Last error: {state.errors[-1][:100]}...")
            raise typer.Exit(2)

        # Delay before next iteration
        if delay > 0:
            time.sleep(delay)

    # Should not reach here, but just in case
    raise typer.Exit(2)


@app.command()
def single(
    issue_ref: Annotated[
        str,
        typer.Argument(help="Issue reference (e.g., SUN-199, #42)"),
    ],
    auto_approve: Annotated[  # noqa: FBT002 (typer bool option)
        bool,
        typer.Option(
            "--auto-approve",
            "-a",
            help="Skip approval gates",
        ),
    ] = False,
) -> None:
    """Run a single /go-on invocation (no loop)."""
    output, exit_code = run_go_on(
        issue_ref,
        headless=False,
        auto_approve=auto_approve,
    )
    typer.echo(output)
    signal = extract_signal(output)
    if signal:
        typer.echo(f"\nSignal: {signal}")
    raise typer.Exit(exit_code)


if __name__ == "__main__":
    app()
