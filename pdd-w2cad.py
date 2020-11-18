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


file = fileopenbox(title='select pdd commissioning spreadsheet', msg=None,
                      default='*', filetypes='*.xlsx')

print(file)

df = pd.read_excel(file) #place "r" before the path string to address special character, such as '\'. Don't forget to put the file name at the end of the path + '.xlsx'

print (df)
