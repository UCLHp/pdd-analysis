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







from os.path import join

import xlrd
import datetime
import pandas as pd
from easygui import fileopenbox, diropenbox



#  input spreadsheet with all the IDD data
file = fileopenbox(title='select pdd commissioning spreadsheet', msg=None,
                      default='*', filetypes='*.xlsx')

#  directory to save the output .w2cad files
oDir = diropenbox(title='Select where to save the .w2cad file', \
                  msg=None, default='*')

if not file:
    print('\nNo input file provided')
    raise SystemExit()

xls = pd.ExcelFile(file)

###  copied from pbtMod/w2cadFiles on 2020-11-24
class W2CADdata:
    def __init__(self):
        self.type = ''
        self.head = []
        self.params = []
        self.x = []
        self.y = []
        self.z = []
        self.d = []

for st in range(len(xls.sheet_names)):

    df = pd.read_excel(xls, xls.sheet_names[st])

    data = [W2CADdata()]  #  list so can have option for many entries

    data[0].type = 'MeasuredDepthDose'
    data[0].head.append('created from spreadsheet data')
    data[0].head.append('spreadsheet created by programme commissioning_pdds.py')
    data[0].params.extend([' VERSION 02', \
                           ' DATE '+str(datetime.datetime.now().strftime('%Y-%m-%d')), \
                           ' TYPE '+str(data[0].type), \
                           ' AXIS Z'
                            ])
    data[0].x = [0.0 for _ in range(len(df[df.columns[0]].to_list()))]
    data[0].y = [0.0 for _ in range(len(df[df.columns[0]].to_list()))]
    data[0].z = df[df.columns[0]].to_list()  #  depths
    data[0].d = df[df.columns[1]].to_list()  #  doses

    ###  writing function a subset of pbtMod/w2cadFiles/W2CADwrite.py
    oFile = join( oDir, str(xls.sheet_names[st])+'MeV.w2cad' )

    with open(oFile, 'w') as of:
        of.write('$ NUMS {:03d}\n'.format(len(data)))
        of.write('#\n# created by w2cadWrite.py\n# creation date: ' \
                  + str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')) \
                  + '\n#\n')

        #  for each entry in data, create an entry in the file
        for dt in data:
            of.write('$ STOM\n')
            for hd in dt.head:
                of.write('# '+str(hd)+'\n')
            for pm in dt.params:
                of.write('% '+str(pm)+'\n')
            for _ in range(len(dt.d)):
                of.write('< {x:+12.5f} {y:+12.5f} {z:+12.5f} {d:+12.5f} >\n'.format(x=dt.x[_], y=dt.y[_], z=dt.z[_], d=dt.d[_]))
            of.write('$ ENOM\n')
        of.write('$ ENOF\n')
