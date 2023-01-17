# pymp3gain
A frontend for mp3gain written in Python and Qt5.
![Screenshot from 2023-01-15 19-07-23](https://user-images.githubusercontent.com/121901328/212574947-b52a3b42-2bbb-4328-91af-979eeda6710d.png)
Basically a clone of the old MP3Gain app for Windows.

pymp3gain relies on an external mp3gain binary. Tested with the mp3gain binary (1.6.2) in the Ubuntu 22.04 repos. By default it looks for /usr/bin/mp3gain but you can change that in preferences.

## Running
pymp3gain needs Qt5 and scandir as well as an mp3gain binary. Just run pymp3gain.py and set your mp3gain location in 'Preferences'.

### Ubuntu 22.04
You'll probably have to install the Qt5 Python bindings from the repos:

``
sudo apt-get install python-pyqt5
``

You'll also need the scandir package for Python:

``
python3 -m pip install scandir
``

If you don't have Pip installed you'll need to install that:

``
sudo apt-get install python3-pip
``

And you'll need mp3gain as well:

``
sudo apt-get install mp3gain
``

Then just run pymp3gain:

``
python3 pymp3gain.py
``
## Contributing
If you find a bug, feel free to open an issue. Or feel free to fork and improve the code.

## Licensing
This code is licensed under the terms of the [MIT License](https://choosealicense.com/licenses/mit/).

