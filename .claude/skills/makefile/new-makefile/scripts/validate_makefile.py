#!/usr/bin/env python3
"""
Validate Makefile syntax and detect common issues.
"""
import re
import sys
from typing import List, Tuple


def validate_makefile(filepath: str) -> Tuple[bool, List[str]]:
    """
    Validate a Makefile and return issues found.

    Returns:
        (is_valid, list_of_issues)
    """
    issues = []

    try:
        with open(filepath, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return False, [f"File not found: {filepath}"]
    except Exception as e:
        return False, [f"Error reading file: {e}"]

    # Track state
    in_recipe = False

    for line_num, line in enumerate(lines, 1):
        # Check for spaces instead of tabs in recipes
        if (
            in_recipe
            and line.strip()
            and not line.startswith("\t")
            and not line.startswith("#")
        ):
            if line.startswith("    "):  # Common mistake: spaces instead of tab
                issues.append(
                    f"Line {line_num}: Recipe commands must start with a TAB, not spaces"
                )
            in_recipe = False

        # Detect target definitions
        if ":" in line and not line.strip().startswith("#"):
            # Basic target pattern
            if re.match(r"^[^:]+:", line):
                in_recipe = True

        # Check for common syntax errors
        if "=" in line and not line.strip().startswith("#"):
            # Check for spaces around := or =
            if re.search(r"\w\s*:=\s*\w", line) or re.search(r"\w\s*=\s*\w", line):
                # This is actually fine, just documenting
                pass

        # Check for undefined variable references (basic check)
        var_refs = re.findall(r"\$\(([^)]+)\)", line)
        for var in var_refs:
            # Check for common undefined automatic variables used incorrectly
            if var in ["<", "@", "^", "?", "*", "+"] and not in_recipe:
                issues.append(
                    f"Line {line_num}: Automatic variable '$({var})' used outside recipe"
                )

        # Check for line continuations
        if line.rstrip().endswith("\\"):
            next_line_idx = line_num
            if next_line_idx < len(lines):
                next_line = lines[next_line_idx]
                if next_line.strip() and next_line.startswith("\t") and not in_recipe:
                    issues.append(
                        f"Line {line_num}: Line continuation followed by TAB (should be space)"
                    )

    # Check for .PHONY declarations for non-file targets
    phony_targets = set()
    defined_targets = set()

    for line in lines:
        if line.strip().startswith(".PHONY:"):
            phony_list = line.split(":", 1)[1]
            phony_targets.update(t.strip() for t in phony_list.split())
        elif ":" in line and not line.strip().startswith("#"):
            target = line.split(":")[0].strip()
            if target and not target.startswith("."):
                defined_targets.add(target)

    # Common targets that should be .PHONY
    common_phony = {
        "all",
        "clean",
        "test",
        "install",
        "build",
        "run",
        "help",
        "lint",
        "format",
    }
    missing_phony = (defined_targets & common_phony) - phony_targets

    if missing_phony:
        issues.append(
            f"Suggestion: Consider adding .PHONY declaration for: {', '.join(sorted(missing_phony))}"
        )

    is_valid = len([i for i in issues if not i.startswith("Suggestion")]) == 0
    return is_valid, issues


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 validate_makefile.py <path/to/Makefile>")
        sys.exit(1)

    filepath = sys.argv[1]
    is_valid, issues = validate_makefile(filepath)

    if is_valid:
        print(f"✅ {filepath} is valid!")
    else:
        print(f"❌ {filepath} has issues:")

    if issues:
        print("\nIssues found:")
        for issue in issues:
            print(f"  • {issue}")

    sys.exit(0 if is_valid else 1)
