Myriagon
========

Myriagon is a time tracking application for macOS and Linux.

It takes the reverse approach to apps such as Toggl, in that you enter how much time you would like to spend on a task.
Myriagon will then count that time down for you, and tell you how much time you will need to spend per day/week/month to hit that target.
As such, it is a motivational tool as much as a time tracker, keeping you in the know about where you are at your goals.
It also allows you to export your time spent in ``.ics`` (iCal) format, for putting into a calendar or otherwise externally consuming your data.

It is written in Python 3, using Toga, Twisted, and lots of love.
MIT licensed, with recorded information available in open/easily readable formats, meaning your data is yours.


Installation
------------

Python 3.4+ only.


macOS Installation
~~~~~~~~~~~~~~~~~~

For macOS 10.12 and later, you can use the ``.app``: <coming soon>

Or, you can install from PyPI (XCode is required):

.. code-block:: sh

   python3 -m pip install pipsi
   python3 -m pipsi install myriagon


Linux Installation
~~~~~~~~~~~~~~~~~~

For Debian-based distributions, you can install from PyPI:

.. code-block:: sh

   apt-get install python3-gi # Or similar for your distro
   python3 -m pip install pipsi
   python3 -m pipsi install myriagon

Running
-------

``myriagon``


Where Data Is Kept
------------------

If you would like to back up/restore your Myriagon data, you can find it in:

* macOS: ``~/Library/Application Support/myriagon/``
* Linux: ``~/.local/myriagon/``
