"""Test wizard functionality for configuration generation.

This module tests the wizard interaction when no config files exist.
"""

from .params import ConfigTestParams, SuiteConfig, WizardStep
from .runner import ConfigTestRunner


def test_simple_wizard_interaction() -> None:
    """Test simple wizard interaction manually."""
    # Create a test case with just server file and expected wizard steps
    test_params = ConfigTestParams(
        test_id="simple_wizard_manual",
        description="Manual wizard test with minimal setup",
        cli_arguments="emsipi internal-config google server.py",
        files={
            "server.py": "fixture:simple_server.py",
            "uv.lock": "fixture:uv_lock_basic.txt",
        },
        wizard_behavior=[
            WizardStep("server_name", "simple-test"),
            WizardStep("runtime", ""),  # Python
            WizardStep("python_dependencies_file", ""),  # uv.lock
            WizardStep("python_version", ""),  # 3.11
        ],
        expected_configuration={
            "server_name": "simple-test",
            "runtime": "python",
            "python_version": "3.11.0",
            "python_dependencies_file": "uv.lock",
            "clean_server_file_or_command": "server.py",
            "server_file": "server.py",
            "server_command": None,
            "command_type": "python",
        },
    )

    # Run the test
    runner = ConfigTestRunner(SuiteConfig(verbose=True, timeout_seconds=10))
    result = runner.run_single_test(test_params)

    if result.cli_result:
        stdout = result.cli_result.stdout
        stderr = result.cli_result.stderr
    else:
        stdout = ""
        stderr = ""

    error_message = (
        f"Wizard test failed: {result.error_message}\n"
        f"CLI stdout: {stdout}\n"
        f"CLI stderr: {stderr}\n"
        f"Validation errors: {result.validation_errors}\n"
    )

    assert result.success, error_message


if __name__ == "__main__":
    # Run the manual test
    test_simple_wizard_interaction()
