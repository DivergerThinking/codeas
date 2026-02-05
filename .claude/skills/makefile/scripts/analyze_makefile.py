#!/usr/bin/env python3
"""
Analyze Makefile structure, targets, dependencies, and variables.
"""
import re
import sys
from typing import Dict


def analyze_makefile(filepath: str) -> Dict:
    """
    Analyze a Makefile and return its structure.

    Returns:
        Dictionary with targets, variables, phony targets, and dependency graph
    """
    try:
        with open(filepath, "r") as f:
            content = f.read()
            lines = content.split("\n")
    except FileNotFoundError:
        return {"error": f"File not found: {filepath}"}
    except Exception as e:
        return {"error": f"Error reading file: {e}"}

    result = {
        "variables": {},
        "targets": {},
        "phony_targets": set(),
        "default_target": None,
        "statistics": {},
    }

    current_target = None
    in_recipe = False

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip comments and empty lines
        if not stripped or stripped.startswith("#"):
            continue

        # Extract variable definitions
        var_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*[:?]?=\s*(.*)$", stripped)
        if var_match and ":" not in var_match.group(1):
            var_name = var_match.group(1)
            var_value = var_match.group(2)
            result["variables"][var_name] = var_value.strip()
            continue

        # Extract .PHONY declarations
        if stripped.startswith(".PHONY:"):
            phony_list = stripped.split(":", 1)[1]
            result["phony_targets"].update(t.strip() for t in phony_list.split())
            continue

        # Extract target definitions
        target_match = re.match(
            r"^([^:]+):\s*(.*)$", line
        )  # Use full line to preserve tabs
        if target_match:
            target_name = target_match.group(1).strip()
            dependencies = target_match.group(2).strip()

            # Skip special targets
            if target_name.startswith(".") and target_name != ".DEFAULT":
                continue

            # Set default target (first non-special target)
            if result["default_target"] is None and not target_name.startswith("."):
                result["default_target"] = target_name

            dep_list = [d.strip() for d in dependencies.split() if d.strip()]

            result["targets"][target_name] = {
                "dependencies": dep_list,
                "recipe_lines": [],
                "line_number": line_num,
            }

            current_target = target_name
            in_recipe = True
            continue

        # Extract recipe lines (must start with tab)
        if in_recipe and line.startswith("\t"):
            recipe_line = line[1:].rstrip()  # Remove leading tab
            if current_target and recipe_line:
                result["targets"][current_target]["recipe_lines"].append(recipe_line)
        else:
            in_recipe = False
            current_target = None

    # Calculate statistics
    result["statistics"] = {
        "total_targets": len(result["targets"]),
        "phony_targets": len(result["phony_targets"]),
        "variables": len(result["variables"]),
        "targets_with_recipes": sum(
            1 for t in result["targets"].values() if t["recipe_lines"]
        ),
        "targets_without_recipes": sum(
            1 for t in result["targets"].values() if not t["recipe_lines"]
        ),
    }

    # Convert set to list for JSON serialization
    result["phony_targets"] = sorted(result["phony_targets"])

    return result


def print_analysis(analysis: Dict):
    """Pretty print the analysis results."""
    if "error" in analysis:
        print(f"❌ Error: {analysis['error']}")
        return

    print("=" * 60)
    print("MAKEFILE ANALYSIS")
    print("=" * 60)

    # Statistics
    stats = analysis["statistics"]
    print("\n📊 Statistics:")
    print(f"   Total targets: {stats['total_targets']}")
    print(f"   Phony targets: {stats['phony_targets']}")
    print(f"   Variables: {stats['variables']}")
    print(f"   Targets with recipes: {stats['targets_with_recipes']}")
    print(f"   Targets without recipes: {stats['targets_without_recipes']}")

    # Default target
    if analysis["default_target"]:
        print(f"\n🎯 Default target: {analysis['default_target']}")

    # Variables
    if analysis["variables"]:
        print(f"\n📝 Variables ({len(analysis['variables'])}):")
        for var, value in sorted(analysis["variables"].items()):
            print(f"   {var} = {value[:50]}{'...' if len(value) > 50 else ''}")

    # Phony targets
    if analysis["phony_targets"]:
        print(f"\n🏷️  Phony targets: {', '.join(analysis['phony_targets'])}")

    # Targets
    print(f"\n🎯 Targets ({len(analysis['targets'])}):")
    for target, info in sorted(analysis["targets"].items()):
        deps = ", ".join(info["dependencies"]) if info["dependencies"] else "none"
        recipe_count = len(info["recipe_lines"])
        print(f"\n   {target}:")
        print(f"      Dependencies: {deps}")
        print(f"      Recipe lines: {recipe_count}")
        if info["recipe_lines"]:
            for recipe_line in info["recipe_lines"][:3]:  # Show first 3 lines
                print(f"         {recipe_line}")
            if recipe_count > 3:
                print(f"         ... ({recipe_count - 3} more lines)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 analyze_makefile.py <path/to/Makefile>")
        sys.exit(1)

    filepath = sys.argv[1]
    analysis = analyze_makefile(filepath)
    print_analysis(analysis)
