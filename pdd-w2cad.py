###  Copyright (C) 2020:  Andrew J. Gosling

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







###  convert measured PDD data into W2CAD format for import into Eclipse
  #  read in the whole spreadsheet with pandas
  #  grab the relevant data for a given energy
  #  format for a function to create W2CAD files
  #  pass with whatever additional data needed.







from easygui import fileopenbox
import xlrd
import pandas as pd


###  Try accessing the dataMod and pbtMod packages for most up to date
  #  versions of these software, otherwise use internal versions that may be
  #  outdated but are at least internally consistent.
try:
    from sys import path as sysPath
    from os import path as osPath
    sysPath.append(osPath.join(osPath.expanduser('~'),'coding','packages'))
    from dataMod.dataClass import W2CADdata
    from pbtMod import w2cad

else:
    ###  A W2CAD data class
      #  W2CAD is a Varian data format in a text file
      #  has a very specific structure
      #  Header details what is contained in the file
      #  parameters indicates what each entry contains
      #  for each line, is an x, y, z, and value (often dose)

    class W2CADdata:
        def __init__(self):
            self.type = ''
            self.head = []
            self.params = []
            self.x = []
            self.y = []
            self.z = []
            self.d = []



# file = fileopenbox(title='select pdd commissioning spreadsheet', msg=None,
#                       default='*', filetypes='*.xlsx')
file = "C:\\Users\\andrew\\coding\\pdd-analysis\\data\\PDD_results.xlsx"

# print(file)

xls = pd.ExcelFile(file)
# print(xls.sheet_names)

df = pd.read_excel(xls, xls.sheet_names[0])

# print(df)

depth = df[df.columns[0]].to_list()
dose = df[df.columns[1]].to_list()
