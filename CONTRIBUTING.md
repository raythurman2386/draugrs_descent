# Contributing to Draugr's Descent

Thank you for your interest in contributing to Draugr's Descent! This document provides guidelines and workflows to make the contribution process smooth and effective.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Branching Strategy](#branching-strategy)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

Please be respectful and inclusive when contributing to this project. Harassment or abusive behavior of any kind will not be tolerated.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork to your local machine
3. Set up the development environment (see below)
4. Create a new branch for your feature or bugfix
5. Make your changes
6. Submit a pull request

## Development Environment

### Prerequisites

- Python 3.8 or newer
- Pygame 2.x
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/draugrs_descent.git
cd draugrs_descent

# Create and activate a virtual environment
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Branching Strategy

- `main` - Production-ready code
- `dev` - Development branch for integration
- Feature branches - Branch from `dev` with the naming convention: 
  - `feature/short-description` for new features
  - `bugfix/issue-number-description` for bug fixes
  - `docs/what-is-being-documented` for documentation updates

## Coding Standards

This project follows the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code.

We use Black for automatic code formatting. Before submitting a PR, format your code:

```bash
black .
```

Or install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

### Docstrings

Use Google-style docstrings for functions and classes:

```python
def function(arg1, arg2):
    """Description of the function.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When and why this exception is raised
    """
    pass
```

## Testing

We use pytest for testing. Write tests for new features and ensure all tests pass before submitting a PR:

```bash
pytest
```

## Pull Request Process

1. Update the README.md or documentation with details of your changes if appropriate
2. Format your code using Black
3. Run tests to ensure they all pass
4. Update the CHANGELOG.md file with details of your changes
5. Submit the pull request to the `dev` branch

Pull requests require approval from at least one maintainer before being merged.

## Issue Reporting

When reporting issues, please use one of the provided templates. If none of them fit your needs, provide the following information:

- A clear and descriptive title
- A detailed description of the issue
- Steps to reproduce the behavior
- Expected behavior
- Screenshots if applicable
- Environment details (OS, Python version, etc.)

## Feature Requests

Feature requests are welcome. Please use the feature request template and clearly describe the functionality you'd like to see, why it's valuable, and how it should work.

---

Thank you for contributing to Draugr's Descent! Your efforts help make this game better for everyone. 