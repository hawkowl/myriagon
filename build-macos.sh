#!/bin/bash

rm -rf macOS/
python3 setup.py macos
python3 -m pip install -U ../toga-cocoa/ -t macOS/Myriagon.app/Contents/Resources/app_packages/
python3 -m pip install -U ../toga-core/ -t macOS/Myriagon.app/Contents/Resources/app_packages/
find macOS/Myriagon.app -iname \*.* | xargs rename -v "s/.cpython-35m-darwin//g"
gtar -C macOS -caf Myriagon-macOS-sierra.tar.bz2 Myriagon.app
