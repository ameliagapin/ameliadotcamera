#!/bin/sh

echo "Installing requirements..."
pip3 install -r requirements.txt

rm static/photos/*

cd scripts

echo "Moving and resizing images..."
python3 resizeimages.py ../photos ../static/photos || exit 1

echo "Generating posts..."
python3 createpages.py ../static/photos || exit 1

cd ..

echo "Done"

exit 0
