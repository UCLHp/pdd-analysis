#Browse to the folder containing the Files
import easygui as eg
import os
from pdd_module import *
from datetime import date
import pypyodbc
import pandas as pd

###############################################################################
# SELECT DATA AND LOAD REFERENCE DIRECTORIES
###############################################################################

dir = eg.diropenbox(title='Please select folder containing pdd data')

if not dir:
    eg.msgbox('Please re-run the code and select a folder containing the data' \
              ' to be analysed', title = 'Folder Selection Error')
    exit()

database_dir = ('\\\\krypton\\rtp-share$\\protons\\Work in Progress\\Christian'
                '\\Database\\Proton\\Test FE - CB.accdb')
refdata_dir = ('\\\\krypton\\rtp-share$\\protons\\Work in Progress\\Christian'
               '\\Python\\PDD Analysis\\Reference Tank Data')
current_date = date.today()  #  For the record later
rounddata = 3    #  For rounding so significant figures match between qs and db

###############################################################################
# CONNECT TO DB AND SELECT USER DEFINED VARIABLES (GANTRY ETC.)
###############################################################################

conn = pypyodbc.connect(
        r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};'
        r'DBQ=' + database_dir + ';'
        )
cursor = conn.cursor()

# Select Operator
cursor.execute('select * from [Operators]')
operators = [row[2] for row in cursor.fetchall()]
operator = eg.choicebox('Who performed the measurements?',
                        'Operator',
                        operators   )
if not operator:
    eg.msgbox('Please re-run the code and select an Operator')
    raise SystemExit
print(f'Operator = {operator}\n')

# Select Gantry
cursor.execute('select * from [MachinesQuery]')
machines = [row[0] for row in cursor.fetchall()]
gantry = eg.choicebox( 'Which room were the measurements performed in?',
                       'Gantry',
                       machines    )
if not gantry:
    eg.msgbox('Please re-run the code and select a room')
    raise SystemExit
print(f'Gantry = {gantry}\n')

# Select Measurement Type
measurement_type = eg.choicebox('Are you performing a PDD or MLIC measurement?',
                                'Measurement Type',
                                ['PDD', 'MLIC']     )
if not measurement_type:
    eg.msgbox('Please re-run the code and select a Measurement Type')
    raise SystemExit
print(f'Measurement Type = {measurement_type}\n')


if measurement_type == 'PDD':
    cursor.execute('select * from [PDD Equipment Query]')
    # Using list comprehension requires zip function and is less readable
    devices = []
    categories = []
    for row in cursor.fetchall():
        devices.append(row[1])
        categories.append(row[2])

    device = eg.choicebox( 'Which Chamber/Device was used?',
                           'Device',
                           devices     )
    if not device:
        eg.msgbox('Please re-run the code and select a device')
        raise SystemExit
    print(f'Chamber/Device Used = {device}\n')
elif measurement_type == 'MLIC':
    eg.msgbox('MLIC code not complete as awaiting database module and queries '
              'to be written')
    raise SystemExit

# Run a check to make sure the device type matches the data type
# i.e. PDD Chamber matches '.mcc' files and MLIC matches '.csv' files
category = categories[devices.index(device)]
if category == 'MLIC':
    if os.listdir(dir)[0].endswith('.csv') != True:
        eg.msgbox('Device does not match filetype. Please re run the code and '
                  'select the correct device/folder', 'Device/File Type Error')
        raise SystemExit
if category == 'PDD Chamber':
    if os.listdir(dir)[0].endswith('.mcc') != True:
        eg.msgbox('Device does not match filetype. Please re run the code and '
                  'select the correct device/folder', 'Device/File Type Error')
        raise SystemExit

# Enter the WET offset through a user entry box
offset = eg.enterbox("Enter WET Offset (mm)", "WET Offset", ('0'))
if not offset:
    eg.msgbox('Offset Value required to run \n'
              'Code will terminate',
              title = 'No WET value entered'  )
    raise SystemExit
try:
    offset = float(offset)
except (ValueError, TypeError) as e:
    eg.msgbox( 'Please re-run the program and enter an appropriate '
               'value for the WET offset', title='WET Value Error' )
    raise SystemExit
print(f'[0]\nWET = {str(offset)} \n')

print('\nRunning the quality system data check...')

###############################################################################
# CHECK REFERENCE DATA FOR BOTH TPS AND CURRENT GANTRY
###############################################################################

### Gantry specific reference data from DataBase
ref_props_gant_db = pd.read_sql('select  [Energy], [Prox 80], ' \
                                '[Prox 90], [Dist 90], [Dist 80], [Dist 20], ' \
                                '[Dist 10], [Fall Off], [Halo Ratio], [PTPR] ' \
                                'from [PDD Reference Data Current Query] ' \
                                'where [Gantry]=\'' + str(gantry) + '\'', conn)

ref_props_gant_db.sort_values(by=['energy'], inplace=True)
ref_props_gant_db = ref_props_gant_db.reset_index(drop=True)
# Also need to round the dataframe to a set value to match any calculated
# fields (e.g. fall off)
ref_props_gant_db = ref_props_gant_db.round(rounddata)



### TPS Reference Data in DataBase
ref_props_tps_db = pd.read_sql('select  [Energy], [Prox 80], ' \
                               '[Prox 90], [Dist 90], [Dist 80], ' \
                               '[Dist 20], [Dist 10], [Fall Off], ' \
                               '[Halo Ratio], [PTPR] from [PDD ' \
                               'Reference Data Current Plan Ref Query]'
                               , conn
                               )
ref_props_tps_db.sort_values(by=['energy'], inplace=True)
ref_props_tps_db = ref_props_tps_db.reset_index(drop=True)
ref_props_tps_db = ref_props_tps_db.round(rounddata)

### Gantry specific reference data from QS
ref_data_gant_qs = directory_to_dictionary(os.path.join(refdata_dir, gantry))
ref_props_gant_qs = []
for key in sorted(ref_data_gant_qs.keys()):
    metrics = PeakProperties(ref_data_gant_qs[key], key)
    ref_props_gant_qs.append([key,
                        round(metrics.Prox80,rounddata),
                        round(metrics.Prox90,rounddata),
                        round(metrics.Dist90,rounddata),
                        round(metrics.Dist80,rounddata),
                        round(metrics.Dist20,rounddata),
                        round(metrics.Dist10,rounddata),
                        round(metrics.FallOff,rounddata),
                        round(metrics.HaloRat,rounddata),
                        round(metrics.PTPR,rounddata)
                        ])
ref_props_gant_qs = pd.DataFrame(ref_props_gant_qs,
                                      columns = ['energy',
                                                 'prox 80', 'prox 90',
                                                 'dist 90', 'dist 80',
                                                 'dist 20', 'dist 10',
                                                 'fall off', 'halo ratio',
                                                 'ptpr'
                                                 ]
                                 )

### TPS reference data from QS
ref_data_tps_qs = directory_to_dictionary(os.path.join(refdata_dir, gantry))
ref_props_tps_qs = []
for key in sorted(ref_data_tps_qs.keys()):
    metrics = PeakProperties(ref_data_tps_qs[key], key)
    ref_props_tps_qs.append([key,
                             round(metrics.Prox80,rounddata),
                             round(metrics.Prox90,rounddata),
                             round(metrics.Dist90,rounddata),
                             round(metrics.Dist80,rounddata),
                             round(metrics.Dist20,rounddata),
                             round(metrics.Dist10,rounddata),
                             round(metrics.FallOff,rounddata),
                             round(metrics.HaloRat,rounddata),
                             round(metrics.PTPR,rounddata)
                             ])
ref_props_tps_qs = pd.DataFrame(ref_props_tps_qs,
                                      columns = ['energy',
                                                 'prox 80', 'prox 90',
                                                 'dist 90', 'dist 80',
                                                 'dist 20', 'dist 10',
                                                 'fall off', 'halo ratio',
                                                 'ptpr'
                                                 ]
                                      )

if not ref_props_gant_db.shape == ref_props_gant_qs.shape:
    eg.msgbox('Discrepancy in gantry reference data between QS and DB \n'
              'Data sizes do not match \n'
              'Code will terminate',
              'Reference Data Error')
    raise SystemExit

if not ref_props_tps_db.shape == ref_props_tps_qs.shape:
    eg.msgbox('Discrepancy in tps reference data between QS and DB \n'
              'Data sizes do not match \n'
              'Code will terminate',
              'Reference Data Error')
    raise SystemExit

if not np.allclose(ref_props_gant_qs, ref_props_gant_db, atol=0.001):
    eg.msgbox('Discrepancy in gantry specific reference data between QS and DB'
              'Please check the values printed in the terminal',
              'Reference Data Error')
    print("Data Base Values \n")
    print(ref_props_gant_db)
    print("Quality System Values \n")
    print(ref_props_gant_qs)
    print("Difference \n")
    Difference = ref_props_gant_db - ref_props_gant_qs
    Difference['energy'] = ref_props_gant_qs['energy']
    print(Difference)
    input('Press Enter To Close Window')
    raise SystemExit

if not np.allclose(ref_props_tps_qs, ref_props_tps_db, atol=0.001):
    eg.msgbox('Discrepancy in tps reference data between QS and DB'
              'Please check the values printed in the terminal',
              'Reference Data Error')
    print("Data Base Values \n")
    print(ref_props_tps_db)
    print("Quality System Values \n")
    print(ref_props_tps_qs)
    print("Difference \n")
    Difference = ref_props_tps_db - ref_props_tps_qs
    Difference['energy'] = ref_props_tps_qs['energy']
    print(Difference)
    input('Press Enter To Close Window')
    raise SystemExit

print('\nQuality System Data Matches Database')

# Check that the user has slected the correct opperator, gantry, etc.
# This data will be written straight into the database and, given
# the amount of it, it will be annoying/time conssuming to correct this once
# it's already in the database.
if not eg.ynbox(msg = 'Please confirm that the following information is ' \
                      'correct... \n\nOperator = ' + operator + '\nGantry = ' +
                      gantry + '\nMeasurement Type = ' + measurement_type +
                      '\nChamber/Device = ' + device + '\nWET = ' + str(offset),
                      title = 'User Input Confirmation'):
    eg.msgbox('User inputs not confirmed. Please re-run code', 'Input Error')

    raise SystemExit

print('\n\nRunning main data analysis...')

################################################################################
######################### MEASUEMENT OF PDD CURVE ##############################

measured_data = directory_to_dictionary(dir)

if measurement_type == 'MLIC':
    GA = eg.enterbox('Enter Measurement Gantry Angle',
                     'Gantry Angle during acquisition',
                     ('270')
                     )
    try:
        float(GA)
    except (ValueError, TypeError) as e:
        eg.msgbox('Please re-run the program and enter an appropriate value ' \
                  'for the Gantry Angle', title = 'Gantry Angle Value Error'  )
        raise SystemExit

file_date = {}
file_GA = {}
for key in sorted(measured_data.keys()):
    metrics = PeakProperties(ref_data_tps_qs[key], key)
    location = os.path.join(dir, str(int(key)))+'.mcc'
    if measurement_type == 'PDD':
        # temp1&2 are unrequired outputs from the readmcc function
        temp1, temp2, file_date[key], file_GA[key] = readmcc(location)
    elif measurement_type == 'MLIC':
        # temp1 is an unrequired output from the readgiraffe function
        temp1, file_date[key] = readgiraffe(location)
        file_GA[key] = GA
    else:
        eg.msgbox('Only measurement types PDD or MLIC will work' \
                  'Please re-run the code', title = 'Measurement type error')

    Subset = [file_date[key], current_date, operator, device, gantry,
              file_GA[key], int(key),
              round(metrics.Prox80, rounddata),
              round(metrics.Prox90, rounddata),
              round(metrics.Dist90, rounddata),
              round(metrics.Dist80, rounddata),
              round(metrics.Dist20, rounddata),
              round(metrics.Dist10, rounddata),
              round(metrics.HaloRat, rounddata),
              round(metrics.PTPR, rounddata),
              round(ref_props_gant_qs.query(f'energy =={key}')['prox 80'].item()
                    - metrics.Prox80, rounddata),
              round(ref_props_gant_qs.query(f'energy =={key}')['prox 90'].item()
                    - metrics.Prox90, rounddata),
              round(ref_props_gant_qs.query(f'energy =={key}')['dist 90'].item()
                    - metrics.Dist90, rounddata),
              round(ref_props_gant_qs.query(f'energy =={key}')['dist 80'].item()
                    - metrics.Dist80, rounddata),
              round(ref_props_gant_qs.query(f'energy =={key}')['dist 20'].item()
                    - metrics.Dist20, rounddata),
              round(ref_props_gant_qs.query(f'energy =={key}')['dist 10'].item()
                    - metrics.Dist10, rounddata),
              round(ref_props_gant_qs.query(f'energy =={key}')['halo ratio'].item()
                    - metrics.HaloRat, rounddata),
              round(ref_props_gant_qs.query(f'energy =={key}')['ptpr'].item()
                    - metrics.PTPR, rounddata),
              round(ref_props_tps_qs.query(f'energy =={key}')['prox 80'].item()
                    - metrics.Prox80, rounddata),
              round(ref_props_tps_qs.query(f'energy =={key}')['prox 90'].item()
                    - metrics.Prox90, rounddata),
              round(ref_props_tps_qs.query(f'energy =={key}')['dist 90'].item()
                    - metrics.Dist90, rounddata),
              round(ref_props_tps_qs.query(f'energy =={key}')['dist 80'].item()
                    - metrics.Dist80, rounddata),
              round(ref_props_tps_qs.query(f'energy =={key}')['dist 20'].item()
                    - metrics.Dist20, rounddata),
              round(ref_props_tps_qs.query(f'energy =={key}')['dist 10'].item()
                    - metrics.Dist10, rounddata),
              round(ref_props_tps_qs.query(f'energy =={key}')['halo ratio'].item()
                    - metrics.HaloRat, rounddata),
              round(ref_props_tps_qs.query(f'energy =={key}')['ptpr'].item()
                    - metrics.PTPR, rounddata)
             ]


    sql = (     'INSERT INTO [PDD Results] ([ADate], [Record Date], ' \
                '[Operator], [Equipment], [MachineName], [GantryAngle], ' \
                '[Energy], [Prox 80], [Prox 90], [Dist 90], [Dist 80], ' \
                '[Dist 20], [Dist 10], [Halo Ratio], [PTPR], ' \
                '[Prox 80 Gantry Diff], [Prox 90 Gantry Diff], ' \
                '[Dist 90 Gantry Diff], [Dist 80 Gantry Diff], ' \
                '[Dist 20 Gantry Diff], [Dist 10 Gantry Diff], ' \
                '[Halo Ratio Gantry Diff], [PTPR Gantry Diff], ' \
                '[Prox 80 Plan Diff], [Prox 90 Plan Diff], ' \
                '[Dist 90 Plan Diff], [Dist 80 Plan Diff], ' \
                '[Dist 20 Plan Diff], [Dist 10 Plan Diff], ' \
                '[Halo Ratio Plan Diff], [PTPR Plan Diff]) \n' \
                'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,' \
                '?,?,?,?,?)'
                )
    cursor.execute(sql,Subset)


conn.commit()

print('\nCompleted :)\n')

eg.msgbox('Code has finished running. Please review results in QA Database',
          title = 'All Energies Completed')
