# pdd-analysis

This repo contains code that will automatically analyse depth dose data files.
It accepts data in both an mcc format as from the Giraffe Multi-Layer Ionisation Chmaber (MLIC),
and csv/xlsx format as from the water tank.   

![Current Version](https://img.shields.io/badge/version-0.1.0-green.svg)

## Components

### commissioning_pdds.py
For analysing one set of depth dose files.
Asks user to input the directory of the mcc or csv files and a save location,
outputs an excel file with each sheet corresponding to a beam energy.

### database_interaction.py
Contains functions that allow the user to connect to an access database
to pull information from tables or sort data into formats that
can easily be written into the database.

### pdd_module.py
Contains functions and classes that help the manipulation of pdd data, including
classes for working with pdd data and with bragg peak properties.

### pdd_qa.py
For ongoing QA measurements using either a water tank and chamber combination,
or the Giraffe MLIC. Will determing the relevant peak properties of the acquired PDDs and compare them
to reference values. Results are then stored in the database.

### pdd_vs_refdata.py
Script to produce an excel spreadsheet comparing two sets of pdds. Peak
properties are compared and a gamma analysis is performed. Results are stored
on sheets corresponding to the bragg peak energy.

## Installation - requires python v3 and git

Note: we currently use a 32-bit version of Access and so if you wish to run any
part of this code that communicates with the database (pdd_qa.py) you must use a 32-bit
version of Python. One way of doing this is through conda environments, for example.

Use the command line and navigate to where you would like to store the repo.
Clone the repo, navigate to the cloned folder and create a virtual environment
using the following commands (locations are examples only):

``` python
cd C:\Desktop\PutRepoInThisFile
git clone https://github.com/UCLHp/pdd-analysis.git
cd C:\Desktop\PutRepoInThisFile\pdd-analysis
python -m venv env
env\Scripts\activate.bat
```

Install the required libraries:
``` python
pip install -r requirements.txt
```

Copy the latest 40 digit git commit hash from the master branch at
https://github.com/UCLHp/pdd-analysis/commits/master and paste this
into the MASTER_HASH variable on line 5 of test.test_version.py.

### Requirements

Required libraries and versions can be found in requirements.txt and
can be installed into virtual environment as shown above.

### Tests

One test currently included that will run within commissioning_pdds, pdd_qa and
pdd_vs_refdata to check that the master branch hasn't been updated since the
repo was cloned.

## Usage

PDD files acquired in a given session should be stored in a single directory
with file names that correspond to the bragg peak energy e.g. 70.mcc or 70.csv

If more than one bragg peak is acquired at the same energy it should be stored
in a separate file.

Navigate to the folder where you cloned the repo and run from the command line
for example:

``` python
cd C:\Desktop\PutRepoInThisFile\pdd-analysis
python pdd_qa.py
```

## Limitations / Known Bugs

* Too many 'measurement types' are listed because they have not been differentiated in the access form yet
* Cannot accommodate non integer energies
* Normalisation currently set to Dmax - but this can be changed

## Contribute

Pull requests are welcome.
For major changes, please open a ticket first to discuss 
desired changes:  [pdd-analysis/issues](http://github.com/UCLHP/pdd-analysis/issues).

If making changes, please check all tests and add if required.

## Licence

All code within this package distributed under [GNU GPL-3.0 (or higher)](https://opensource.org/licenses/GPL-3.0).

Full license text contained within the file LICENCE.

###  (C) License for all programmes

```
###  Copyright (C) 2020:  Callum Stuart Main Gillies

  #  This program is free software: you can redistribute it and/or modify
  #  it under the terms of the GNU General Public License as published by
  #  the Free Software Foundation, either version 3 of the License, or
  #  (at your option) any later version.

  #  This program is distributed in the hope that it will be useful,
  #  but WITHOUT ANY WARRANTY; without even the implied warranty of
  #  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  #  GNU General Public License for more details.

  #  You should have received a copy of the GNU General Public License
  #  along with this program.  If not, see <http://www.gnu.org/licenses/>.
```
