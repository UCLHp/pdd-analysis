# pdd-w2cad

## Scope

A few sentences outlining the intention of the overall project

A list of intended outcomes/goals:

- outcome 1
- goal 2
- measurable 3

## Plan design

Breakdown of the project, with much more detail of each element to be included

- include lists
   - and even sub lists

## Elements

####  Dependency
```console
xlrd            1.2.0
```


### projectFileName.py

**functionNameOne**

The details of functionNameOne

**functionNameTwo**

The details of functionNameTwo

## To Develop

Things to be added into the programme.

## Testing

Any testing to be performed and/or files included to test the fucntions.

## Issues

Things that are a problem that need to be updated and/or fixed.

# Appendix:  DEV NOTES

Developing interpreter to convert the final output of the PDD analysis into
`W2CAD` format necessary to import into eclipse to build a TPS model.

Operating within a virtual environment using venv (Python 3.7.0)

```console
python -m venv pddw2cad
w2cad/Scripts/activate.bat
pip install -r requirements.txt
```

Going to hash out structure somethign like
 - read in the whole spreadsheet with pandas
 - grab the relevant data for a given energy
 - format for a function to create W2CAD files
 - pass with whatever additional data needed.

Turns out need xlrd to read in the excel so installed with pip

```console
xlrd            1.2.0
```
