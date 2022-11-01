# PlasmaGun

The purpose of this repository is to contain code for automatic data acquisition for the Plasma Gun setup at GREMI at the University of Orleans.

The code is orgainzed with the following structure, as seen in this main folder of this repository:
```
PlasmaGun
  +-- data
  +-- misc
  +-- test
  +-- utils
  +-- venv
  oscilloscope_test.py
  pg_requirements.txt
  README.md
  run_gui.py
  run_manual.py
 ```
 
* The `data` folder contains the data that is saved/will be saved when running experiments with the plasma gun. See the README inside this folder to learn more about the files located in this folder.
* The `misc` folder contains `*.deb` files that would be used to set up PicoScope software for a Raspberry Pi setup. See the README inside this folder to learn more about the files located in this folder.
* The `test` folder contains test scripts to test each measurement device independently. See the README inside this folder to learn more about the files located in this folder.
* The `utils` folder contains custom utilities that are used to condense the main script into a smaller, more readable format. See the README inside this folder to learn more about the files located in this folder.
* The `venv` folder contains the virtual environment to run the Python code on a Unix system, if it desired to not install the necessary python libraries on a particular machine.
* `oscilloscope_test.py` is the test file for the oscilloscope; it is located here instead of the `test` folder due to a bug.
* `pg_requirements.txt` contains a list of Python libraries that should be installed for the setup of a computer or Raspberry Pi. It is used with the command `pip install -r pg_requirements.txt`. NOTE: This file works with Unix systems only.
* `README.md` is this file.
* `run_gui.py` is a testing file for creating a GUI.
* `run_manual.py` is the main file for collecting data using manual inputs.
