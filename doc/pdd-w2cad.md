# pdd-w2cad

## Scope

Convert the output of the PDD measurements and analysis into the `.w2cad` file format required by Eclipse for beam model creation.

## Plan design

- Request the location of the PDD spreadsheet
- read in the spreadsheet to a data frame
- identify the number of sheets within the spreadsheet
- for each sheet

  - Read in the depth and dose data
  - create a W2CADclass structure for the data
  - add in the required `w2cad` headers and parameters
  - write to a file location

## Elements

Single element `pdd-w2cad.py` that performs full task.

### Dependency

```console
xlrd            1.2.0
```

### pdd-w2cad.py

Use `easygui` to identify input file and locate output directory

Use `pandas` and `xlrd` to read in the excel file into a dataframe

Have baked in the `W2CADdata` class into the function from `pbtMod`

Read the excel data into appropriate lists and then parse into the `W2CADdata` class including adding headers and parameters.

## To Develop

Have not tested reading of `.w2cad` files into TPS so will have to confirm the formatting is correct.

Have not generated any testing routines.

## Testing

None developed so far but in the To Develop list.

## Issues

Nothing identified so far.

# Appendix: DEV NOTES

Developing interpreter to convert the final output of the PDD analysis into `W2CAD` format necessary to import into eclipse to build a TPS model.

Operating within a virtual environment using venv (Python 3.7.0)

```console
python -m venv envpddw2cad
envpddw2cad/Scripts/activate.bat
pip install -r requirements.txt
```

Going to hash out structure something like:

- read in the whole spreadsheet with pandas
- grab the relevant data for a given energy
- format for a function to create W2CAD files
- pass with whatever additional data needed.

Turns out need xlrd to read in the excel so installed with pip

```console
xlrd            1.2.0
```

Found a great way to be able to look through all the sheets in a file:

```python
file = fileopenbox(title='select pdd commissioning spreadsheet', msg=None,
                      default='*', filetypes='*.xlsx')
print(file)

xls = pd.ExcelFile(file)
print(xls.sheet_names)

df1 = pd.read_excel(xls, '70')
df2 = pd.read_excel(xls, xls.sheet_names[0])
print(df1)
print(df2)
```

this will output the same sheet for both options (presuming the sheet labelled 70 is the first energy PDD measured).
