#!/bin/bash

rm -rf macOS/
python3 setup.py macos
find macOS/Myriagon.app -iname \*.* | xargs rename -v "s/.cpython-35m-darwin//g"
gtar -C macOS -caf Myriagon-macOS-sierra.tar.bz2 Myriagon.app
