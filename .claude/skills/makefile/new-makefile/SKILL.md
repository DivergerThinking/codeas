---
name: makefile
description: >
  Professional Makefile creation, analysis, modification, and debugging for software projects.
  Use this skill when the user needs to: (1) Create new Makefiles from scratch for Python, Java,
  or multi-language projects, (2) Analyze or explain existing Makefiles (structure, targets,
  dependencies, variables), (3) Modify, optimize, or refactor Makefiles to follow best practices,
  (4) Debug Makefile issues (syntax errors, dependency problems, execution failures), or (5) Add
  new targets, improve build performance, or implement professional patterns. Triggers include
  mentions of Makefile, make, build automation, compilation workflows, or requests to improve
  project build systems.
---

# Makefile Skill

Professional skill for creating, analyzing, modifying, and debugging Makefiles in software projects.

## Quick Reference

**Core workflow:**
1. Understand the task (create/analyze/modify/debug)
2. For creation: Select appropriate template from references
3. For analysis: Use analyze_makefile.py script
4. For validation: Use validate_makefile.py script
5. Apply best practices from references/best_practices.md

## When to Use This Skill

This skill should be used whenever working with Makefiles, including:
- Creating new Makefiles for projects
- Analyzing existing Makefile structure
- Debugging Makefile syntax or execution issues
- Refactoring or optimizing Makefiles
- Adding new targets or improving existing ones
- Implementing professional build patterns

## Core Workflow

### 1. Creating New Makefiles

**Process:**
1. Identify project type (Python, Java, multi-language)
2. Determine complexity level and required features
3. Select appropriate template from references
4. Customize for specific project needs
5. Validate with scripts/validate_makefile.py

**For Python projects:**
- Read references/python_templates.md
- Choose template: Basic, Advanced (Docker/CI), Flask/FastAPI, or Data Science/ML
- Customize variables (project name, directories, dependencies)
- Add project-specific targets as needed

**For Java projects:**
- Read references/java_templates.md
- Choose template: Basic, Maven-style, Spring Boot, Multi-module, or Gradle
- Configure Java version, main class, and dependencies
- Adapt build tool integration (Maven/Gradle)

**Best practices to apply:**
- Always include .PHONY declarations
- Provide a help target with clear documentation
- Use variables for configuration
- Include clean target
- Support common workflows (build, test, install)

### 2. Analyzing Existing Makefiles

**Process:**
1. Run scripts/analyze_makefile.py to get structure overview
2. Examine targets, dependencies, and variables
3. Check for phony declarations
4. Review recipes for each target
5. Identify patterns and potential issues

**Analysis script usage:**
```bash
python3 scripts/analyze_makefile.py path/to/Makefile
```

The script provides:
- Statistics (total targets, variables, phony declarations)
- Default target identification
- Variable definitions
- Target dependencies and recipes
- Structural overview

**What to look for:**
- Missing .PHONY declarations for non-file targets
- Undefined or unused variables
- Circular dependencies
- Missing dependencies
- Inconsistent naming conventions

### 3. Modifying and Optimizing Makefiles

**Common modifications:**

**Adding new targets:**
```makefile
.PHONY: new-target
new-target: dependencies
	@echo "Running new target..."
	command1
	command2
```

**Optimizing variable usage:**
```makefile
# Before
build:
	python3 -m pytest tests/

# After (with variables)
PYTHON := python3
TEST_DIR := tests

.PHONY: test
test:
	$(PYTHON) -m pytest $(TEST_DIR)
```

**Improving dependency management:**
```makefile
# Ensure order and dependencies
build: install
	# Build commands

install: venv
	# Install commands

venv:
	# Create virtual environment
```

**Consult references/best_practices.md for:**
- Performance optimization patterns
- Conditional compilation
- Multi-platform support
- Parallel build configuration
- Advanced patterns and techniques

### 4. Debugging Makefiles

**Validation workflow:**
1. Run scripts/validate_makefile.py to identify syntax issues
2. Check validation output for specific problems
3. Fix issues systematically (tabs, variables, dependencies)
4. Re-validate after fixes

**Validation script usage:**
```bash
python3 scripts/validate_makefile.py path/to/Makefile
```

**Common issues detected:**
- Spaces instead of tabs in recipes (critical error)
- Automatic variables used outside recipes
- Missing .PHONY declarations for common targets
- Line continuation issues
- Syntax errors in target definitions

**Manual debugging techniques:**

**Check tab characters:**
```bash
# Verify tabs are present (not spaces)
cat -A Makefile | grep "^I"  # Should show ^I for tabs
```

**Test individual targets:**
```bash
make -n target-name  # Dry run to see what would execute
make target-name     # Actually run the target
```

**Debug variable expansion:**
```bash
make -p  # Print database of all rules and variables
```

**Common error patterns:**

**Error: "missing separator"**
- Cause: Spaces instead of tabs in recipe
- Fix: Replace leading spaces with single tab character

**Error: "No rule to make target"**
- Cause: Missing dependency or typo in target name
- Fix: Check target names and ensure all dependencies exist

**Error: Command not found**
- Cause: Variable not set or program not in PATH
- Fix: Set variables correctly or use full paths

### 5. Implementing Best Practices

Read references/best_practices.md for comprehensive guidance on:

**Essential practices:**
- Phony target declarations
- Variable usage and assignment
- Help target implementation
- Automatic variables
- Directory creation
- Error handling

**Common patterns:**
- Dependency management
- Conditional compilation
- Multi-platform support
- Parallel builds
- Testing integration
- Documentation generation

**Advanced techniques:**
- Function definitions
- Target-specific variables
- Include guards
- Performance optimization

## Reference Files

Load these as needed for detailed guidance:

- **references/python_templates.md** - Complete Python project templates (basic, advanced, web apps, ML/data science)
- **references/java_templates.md** - Complete Java project templates (basic, Maven, Spring Boot, multi-module, Gradle)
- **references/best_practices.md** - Professional patterns, common mistakes, performance tips, advanced techniques

## Scripts

Use these tools for analysis and validation:

- **scripts/analyze_makefile.py** - Analyze structure, targets, dependencies, and variables
- **scripts/validate_makefile.py** - Validate syntax and detect common issues

## Examples

### Example 1: Creating a Python Flask App Makefile

User request: "Create a Makefile for my Flask application"

**Workflow:**
1. Read references/python_templates.md (Flask/FastAPI section)
2. Customize project variables
3. Create Makefile with targets: install, dev, run, test, lint, format, migrate
4. Validate with scripts/validate_makefile.py

### Example 2: Debugging Tab Issues

User request: "My Makefile says 'missing separator' error"

**Workflow:**
1. Run scripts/validate_makefile.py on the file
2. Identify lines with space-indent instead of tabs
3. Replace spaces with tabs in recipe lines
4. Re-validate to confirm fix

### Example 3: Optimizing Existing Makefile

User request: "Make my Makefile more professional"

**Workflow:**
1. Run scripts/analyze_makefile.py to understand structure
2. Read references/best_practices.md
3. Add missing .PHONY declarations
4. Extract hardcoded values to variables
5. Add help target
6. Implement proper error handling
7. Validate final result

### Example 4: Creating Multi-module Java Project

User request: "Create a Makefile for my multi-module Java project with common, service-a, service-b modules"

**Workflow:**
1. Read references/java_templates.md (Multi-module section)
2. Customize module list
3. Set up recursive make or include pattern
4. Define module dependencies
5. Create convenience targets for each module
6. Validate with scripts/validate_makefile.py

## Tips for Success

1. **Always validate** - Run validate_makefile.py before delivering
2. **Use templates** - Start from references rather than from scratch
3. **Check tabs** - Recipe lines MUST use tabs, not spaces
4. **Test incrementally** - Test each target as you add it
5. **Document** - Include help target and comments
6. **Be consistent** - Follow naming conventions and patterns
7. **Handle errors** - Add error checking in complex recipes
8. **Think dependencies** - Ensure proper target dependency chains

## Common Pitfalls

1. Using spaces instead of tabs in recipes (most common error)
2. Forgetting .PHONY declarations
3. Circular dependencies between targets
4. Hardcoding paths and commands
5. Not handling missing dependencies gracefully
6. Incorrect variable expansion ($ vs $$)
7. Platform-specific assumptions

## Output Format

When creating or modifying Makefiles, always:
1. Include clear comments explaining sections
2. Group related targets together
3. Put configuration variables at the top
4. Include a help target
5. Follow the template structure from references
6. Ensure proper indentation (tabs for recipes)
7. Add .PHONY declarations where needed

The final Makefile should be production-ready, well-documented, and follow professional standards.
