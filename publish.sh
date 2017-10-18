# Clean old dists
rm -r dist

# Create new packege
python setup.py sdist

# Upload to pypi
twine upload dist/*