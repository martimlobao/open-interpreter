"""
Shell Integration Setup for Open Interpreter

This script installs shell integration that:
1. Maintains a transcript of terminal interactions (commands and their outputs)
2. Captures both successful commands and their results
3. Routes unknown commands to the interpreter with full terminal history as context
4. Works with both zsh and bash shells

The history is stored in ~/.shell_history_with_output in a chat-like format:
user: <command>
computer: <output>
"""

import os
import re
from pathlib import Path


def get_shell_config():
    """Determine user's shell and return the appropriate config file path."""
    shell = os.environ.get("SHELL", "").lower()
    home = str(Path.home())

    if "zsh" in shell:
        return os.path.join(home, ".zshrc"), "zsh"
    elif "bash" in shell:
        bash_rc = os.path.join(home, ".bashrc")
        bash_profile = os.path.join(home, ".bash_profile")

        if os.path.exists(bash_rc):
            return bash_rc, "bash"
        elif os.path.exists(bash_profile):
            return bash_profile, "bash"

    return None, None


def get_shell_script(shell_type):
    """Return the appropriate shell script based on shell type."""
    base_script = """# Create log file if it doesn't exist
touch ~/.shell_history_with_output

# Function to capture terminal interaction
function capture_output() {
    local cmd=$1
    echo "user: $cmd" >> ~/.shell_history_with_output
    echo "computer:" >> ~/.shell_history_with_output
    eval "$cmd" >> ~/.shell_history_with_output 2>&1
}

# Command not found handler that pipes context to interpreter
command_not_found_handler() {
    cat ~/.shell_history_with_output | interpreter
    return 0
}

# Hook into preexec"""

    if shell_type == "zsh":
        return base_script + '\npreexec() {\n    capture_output "$1"\n}\n'
    elif shell_type == "bash":
        return (
            base_script
            + '\ntrap \'capture_output "$(HISTTIMEFORMAT= history 1 | sed "s/^[ ]*[0-9]*[ ]*//")" \' DEBUG\n'
        )
    return None


def main():
    """Install or reinstall the shell integration."""
    print("Starting installation...")
    config_path, shell_type = get_shell_config()

    if not config_path or not shell_type:
        print("Could not determine your shell configuration.")
        print(
            "Please visit docs.openinterpreter.com/shell for manual installation instructions."
        )
        return

    # Clean up history file
    history_file = os.path.expanduser("~/.shell_history_with_output")
    if os.path.exists(history_file):
        os.remove(history_file)

    # Create fresh history file
    with open(history_file, "w") as f:
        f.write("")

    # Read existing config
    try:
        with open(config_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        content = ""

    start_marker = "### <openinterpreter> ###"
    end_marker = "### </openinterpreter> ###"

    # Check if markers exist
    if start_marker in content:
        response = input(
            "Open Interpreter shell integration appears to be already installed. Would you like to reinstall? (y/n): "
        )
        if response.lower() != "y":
            print("Installation cancelled.")
            return

        # Remove existing installation
        pattern = f"{start_marker}.*?{end_marker}"
        content = re.sub(pattern, "", content, flags=re.DOTALL)

    # Get appropriate shell script
    shell_script = get_shell_script(shell_type)

    # Create new content
    new_content = (
        f"{content.rstrip()}\n\n{start_marker}\n{shell_script}\n{end_marker}\n"
    )

    # Write back to config file
    try:
        with open(config_path, "w") as f:
            f.write(new_content)
        print(
            f"Successfully installed Open Interpreter shell integration to {config_path}"
        )
        print("Please restart your shell or run 'source ~/.zshrc' to apply changes.")
    except Exception as e:
        print(f"Error writing to {config_path}: {e}")
        print(
            "Please visit docs.openinterpreter.com/shell for manual installation instructions."
        )


if __name__ == "__main__":
    main()
