# Notes on building the package

```bash
# Get code
git clone https://github.com/Nonannet/pyhoff.git
cd pyhoff

# Setup venv
python -m venv ./.venv
source ./.venv/bin/activate  # On Windows use `.\.venv\Scripts\activate`

# Update version number in
# - pyproject.toml
# - CITATION.cff

# Check code:
pip install -r requirements-dev.txt
flake8
pytest

# Build package:
pip install build
python -m build

# Upload
pip install twine
#python3 -m twine upload dist/*
python -m twine upload dist/*
```
