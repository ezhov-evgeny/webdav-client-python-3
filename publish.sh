# Clean old dists
rm -r dist

# Create package (sdist and wheel)
python -m build

# Upload to pypi
twine upload dist/*