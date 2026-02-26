---
description: Strict coding standards and documentation rules
---

# WORKFLOW: Coding Standards

**1. File Headers**
Every python file MUST start with this header block:
```python
# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: <filename>
# Version: <version>
# Author: Antigravity
# Description: <Short description of what this file does>
# --------------------------------------------------------------------------------
```

**2. Docstrings (Google Style)**
All functions and classes must have docstrings.
```python
def my_function(param1: int, param2: str) -> bool:
    """
    Short summary of function.

    Args:
        param1 (int): Description of param1.
        param2 (str): Description of param2.

    Returns:
        bool: Description of return value.
    
    Raises:
        ValueError: If param1 is invalid.
    """
    pass
```

**3. Versioning**
- Maintain a `__version__ = "x.y.z"` variable in module `__init__.py` files or at the top of single scripts if applicable.
- When modifying a file significantly, bump the version in the header.

**4. Type Hints**
- Use `typing` module.
- All function signatures must have type hints.
