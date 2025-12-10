# llm-patch

A tool for reliably applying LLM-generated unified diffs using fuzzy, context-based matching instead of line numbers. Designed to handle approximate, inconsistent, or misaligned patches and apply them safely to real code.

## Features

- **Fuzzy Matching**: Uses similarity-based matching instead of relying on exact line numbers
- **Context-Aware**: Intelligently finds the best location to apply patches based on surrounding code
- **Flexible Thresholds**: Configurable similarity thresholds for matching
- **Python API**: Easy-to-use Python interface for patch application
- **Well-Tested**: Comprehensive test suite with high code coverage
- **Type-Safe**: Type hints throughout for better IDE support

## Installation

```bash
pip install llm-patch
```

For development:

```bash
git clone https://github.com/trickl/llm-patch.git
cd llm-patch
pip install -e .
pip install -r requirements-dev.txt
```

## Usage

### Basic Usage

```python
from llm_patch import apply_patch

source_code = """
def hello():
    print("Hello, World!")
"""

patch = """
def hello():
    print("Hello, Universe!")
"""

result, success = apply_patch(source_code, patch)
if success:
    print("Patch applied successfully!")
    print(result)
else:
    print("Failed to apply patch")
```

### Using PatchApplier Class

```python
from llm_patch import PatchApplier

applier = PatchApplier(similarity_threshold=0.8)
result, success = applier.apply(source_code, patch)
```

### Using FuzzyMatcher

```python
from llm_patch import FuzzyMatcher

matcher = FuzzyMatcher(threshold=0.7)
source_lines = ["line1", "line2", "line3"]
pattern_lines = ["line1", "line2"]

# Find where the pattern best matches in the source
match_index = matcher.find_best_match(source_lines, pattern_lines)
if match_index is not None:
    print(f"Pattern found at line {match_index}")
```

## Development

### Running Tests

```bash
pytest tests/ -v --cov=llm_patch
```

### Running Linters

```bash
# Run pylint
pylint src/llm_patch

# Format code with black
black src/ tests/

# Type checking with mypy
mypy src/llm_patch
```

### Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality:

```bash
pre-commit install
pre-commit run --all-files
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests and linters (`pytest && pylint src/llm_patch`)
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the need to reliably apply LLM-generated code patches
- Built with modern Python best practices
