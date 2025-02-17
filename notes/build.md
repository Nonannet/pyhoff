# Notes on building the package

```bash
# Get code
git clone https://github.com/Nonannet/pyhoff.git
cd pyhoff

# Setup venv
python -m venv ./.venv
source ./.venv/bin/activate  # On Windows use `.\.venv\Scripts\activate`

# Check code:
pip install -r requirements-dev.txt
flake8
pytest

# Build package:
pip install build
python3 -m build

# Upload
pip install twine
#python3 -m twine upload dist/*
python3 -m twine upload --repository testpypi dist/*  # Test repository: https://test.pypi.org/project/example_package_YOUR_USERNAME_HERE
```
