#Browse to the folder containing the Files
import easygui as eg
import os
from pdd_module import *
from datetime import date
from openpyxl import workbook, load_workbook
import csv
import pypyodbc
import random
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
operator = eg.choicebox(   'Who performed the measurements?',
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
    eg.msgbox('Offset Value required to run '
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
# CHECK REFERENCE DATA FOR BOTH TPS AND CURRENT Gantry
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
    eg.msgbox('Discrepancy in gantry specific reference data between QS and DB '
              'Data sizes do not match '
              'Code will terminate',
              'Reference Data Error')
    raise SystemExit

if not ref_props_tps_db.shape == ref_props_tps_qs.shape:
    eg.msgbox('Discrepancy in tps reference data between QS and DB '
              'Data sizes do not match'
              'Code will terminate',
              'Reference Data Error')
    raise SystemExit


gant_mismatch_map = (ref_props_gant_qs == ref_props_gant_db)
# gant_mismatch_map = gant_mismatch_map.insert(0,'gantry',
#                                              ref_props_gant_db['energy'],
#                                              )
tps_mismatch_map = (ref_props_tps_qs == ref_props_tps_db)

# tps_mismatch_map = tps_mismatch_map.insert(0,'gantry',
#                                            list(ref_props_tps_db['energy']),
#                                            )
print(tps_mismatch_map)
exit()

if not np.allclose(ref_props_gant_qs, ref_props_gant_db, atol=0.001):
    eg.msgbox('Discrepancy in gantry specific reference data between QS and DB '
              'Please check the datapoints listed in the terminal',
              'Reference Data Error')
    print(gant_mismatch_map)
    input('Press Enter To Close Window')
    raise SystemExit

if not np.allclose(ref_props_tps_qs, ref_props_tps_db, atol=0.0001):
    eg.msgbox('Discrepancy in tps reference data between QS and DB '
              'Please check the datapoints listed in the terminal',
              'Reference Data Error')
    print(tps_mismatch_map)
    input('Press Enter To Close Window')
    raise SystemExit


# ref_data_properties = pd.DataFrame.from_dict(ref_data_properties)
eg.msgbox('It Ran', 'Data OK')


exit()


# Do the same for the plan reference data (see coments above). Also find out
# what gantry contains the planing reference data (which will be useful for
# later)
cursor.execute('select * from [PDD Reference Data Current Plan Ref Query]')
PlanRefGantry = cursor.fetchall()
PlanRefGantry = PlanRefGantry[0][1]
ref_props_tps_db = pd.read_sql(  'select  [Gantry], [Energy], [Prox 80], ' \
                                    '[Prox 90], [Dist 90], [Dist 80], ' \
                                    '[Dist 20], [Dist 10], [Fall Off], ' \
                                    '[Halo Ratio], [PTPR] from [PDD ' \
                                    'Reference Data Current Plan Ref Query] '
                                    , conn  )
ref_props_tps_db.sort_values(by=['gantry', 'energy'], inplace=True)
ref_props_tps_db = ref_props_tps_db.reset_index(drop=True)
ref_props_tps_db = ref_props_tps_db.round(rounddata)

####################
# Major loop to extract data from reference files saved in the quality system
####################

QualSysRefData=[]
QualSysPlanRefData=[]
# Create a list to use in subsequent 'for' loop
GantryList = [[Gantry, 1], [PlanRefGantry, 2]]
# Loop through to pull out the gantry specific and the planning reference data
for x in GantryList:
    for filename in os.listdir(refdata_dir + '/' + str(x[0])):
        # Extract the filename
        file = os.path.basename(filename)
        # Extract filename without extension
        name = os.path.splitext(file)[0]
        # Go through file, check file type and extract data
        # Water tank files are saved as .mcc
        if filename.endswith('.mcc'):
            # This function is in the PDD module and reads MCC files.
            Data_Dict[name], E, D, GA = ReadTank(os.path.join(dir,filename))
        # Giraffe data files are saved as .csv
        if filename.endswith('.csv'):
            # This function is in the PDD module and reads CSV files
            Data_Dict[name], D = ReadGiraffe(os.path.join(dir,filename))
            # Giraffe files don't have energy in the header so take it from the
            # filename, which should be saved as the energy. Quickly check that
            # the 'name' is a number and then save as 'E'
            try:
                float(name)
            except ValueError:
                msgbox( 'Files must be labelled with the energy of the bragg ' \
                        'peak please rename files', title = 'File Name Error' )
                exit()
            E = float(name)
        # Checks title names against data names ########################################## IS THIS NECESSARY?!?! ################################################
        # (mainly for MCC files as for giraffe files, E is taken from name) #####################################################################################
        if float(name) != float(E): #############################################################################################################################
            # Creates list of files which are incorrectly labelled ##############################################################################################
            BadName.append([name,E]) ############################################################################################################################
            continue ##################################################################### IS THIS NECESSARY?!?! ################################################
        # Run the scripts to perform peak analysis and save as Data-Props
        (Data_Props) = OnePDD(Data_Dict[name], E)
        # Create a list using Data_Props for saving into database or creating
        # dataframe
        Subset = [  x[0],
                    E,
                    round(float(Data_Props.Prox80),(rounddata)),
                    round(float(Data_Props.Prox90),(rounddata)),
                    round(float(Data_Props.Dist90),(rounddata)),
                    round(float(Data_Props.Dist80),(rounddata)),
                    round(float(Data_Props.Dist20),(rounddata)),
                    round(float(Data_Props.Dist10),(rounddata)),
                    round(float(Data_Props.FallOff),(rounddata)),
                    round(float(Data_Props.HaloRat),(rounddata)),
                    round(float(Data_Props.PTPR),(rounddata))
                    ]
        # Append the list
        if float(x[1]) == 1:
            QualSysRefData.append(Subset)
        if float(x[1]) == 2:
            QualSysPlanRefData.append(Subset)
    # Now that all the files are analysed turn QualSysRefData and
    # QualSysPlanRefData into a DataFrame. Also re-order the dataframe
    # and then reset the index (to start at 0 in the new order).
    if float(x[1]) == 1:
        QualSysRefData = pd.DataFrame(  QualSysRefData,
                                        columns = [ 'gantry', 'energy',
                                                    'prox 80', 'prox 90',
                                                    'dist 90', 'dist 80',
                                                    'dist 20', 'dist 10',
                                                    'fall off', 'halo ratio',
                                                    'ptpr'  ]   )
        QualSysRefData.sort_values(by=['gantry', 'energy'], inplace=True)
        QualSysRefData = QualSysRefData.reset_index(drop=True)
    if float(x[1]) == 2:
        QualSysPlanRefData = pd.DataFrame( QualSysPlanRefData,
                                           columns = ['gantry', 'energy',
                                                      'prox 80', 'prox 90',
                                                      'dist 90', 'dist 80',
                                                      'dist 20', 'dist 10',
                                                      'fall off', 'halo ratio',
                                                      'ptpr'  ]   )
        QualSysPlanRefData.sort_values(by=['gantry', 'energy'], inplace=True)
        QualSysPlanRefData = QualSysPlanRefData.reset_index(drop=True)

# Check if the Database data is equal to the quality system data. If it isn't
# then run a bit of troubleshooting code which will run through element by
# element and print to the terminal any elements which do not match.

Array = [   [ref_props_gant_db, QualSysRefData],
            [ref_props_tps_db, QualSysPlanRefData]   ]
Dummy = [0, 1]
for i in Dummy:
    if not (Array[i][0].equals(Array[i][1])):
        # Check number of records is the same
        if Array[i][1].shape[0] != Array[i][0].shape[0]:
            print('\nDataframes are different sizes!')
            msgbox( 'WARNING! The reference data in the quality system does ' \
                    'not match with the reference data in the QA Database. ' \
                    'Contact MPE/QA Lead before proceeding'  )
            exit()
        # Find the number of rows and create an index from 0 to this number
        max_row = Array[i][1].shape[0]
        index = list(range(0, max_row))
        # Create a column list for the columns containing non-numerical data
        columns = ['gantry', 'energy']
        # BadRefData used as a dummy value to trigger a warning and exit
        BadRefData = 0
        # Use the index and column list to go element by element through the
        # labels
        for x in index:
            for y in columns:
                if (Array[i][0]).at[x, y] != (Array[i][1].at[x, y]):
                    print( '',
                           'Data mismatch!',
                           'Index = ' + str(x),
                           'Column = ' + str(y),
                           'Database Data = ' + str(Array[i][0].at[x, y]),
                           'Quality System Data = ' + str(Array[i][1].at[x, y]),
                           '',
                           sep='\n'  )
                    # Update dummy value to trigger warning and exit later
                    BadRefData = 1
        # Create a column list for the columns containing the numerical data
        columns = [ 'prox 80', 'prox 90', 'dist 90', 'dist 80', 'dist 20',
                    'dist 10', 'fall off', 'halo ratio', 'ptpr'  ]
        # Use the index and column list to go element by element through the
        # data
        for x in index:
            for y in columns:
                # This is basically to check that any errors are not just due
                # to a rounding error. Rounding to 3 decimal places so should
                # only flag up problems when the difference >= 0.002
                if (Array[i][0].at[x, y]) - (Array[i][1].at[x, y]) >= 0.002:
                    print( '',
                           'Data mismatch!',
                           'Index = ' + str(x),
                           'Column = ' + str(y),
                           'Database Data = ' + str(Array[i][0].at[x, y]),
                           'Quality System Data = ' + str(Array[i][1].at[x, y]),
                           '',
                           sep='\n'  )
                    # Update dummy value to trigger warning and exit later
                    BadRefData = 1
        if BadRefData != 0:
            # Warning and exit based off dummy value
            msgbox( 'WARNING! The reference data in the quality system does ' \
                    'not match with the reference data in the QA Database. ' \
                    'Contact MPE/QA Lead before proceeding'  )
            exit()

print('\nQuality system data check complete. All good :)')




################################################################################
######################### MEASUEMENT OF PDD CURVE ##############################

###################
# Once the reference data has been checked the actual comparison against the
# measured date can be completed.
####################

# First want to double check that the user has slected the correct opperator,
# gantry, etc. This data will be written straight into the database and, given
# the amount of it, it will be annoying/time conssuming to correct this once
# it's already in the database.
if not ynbox(msg =  'Please confirm that the following information is ' \
                    'correct... \n\nOperator = ' + Operator + '\nGantry = ' +
                    Gantry + '\nMeasurement Type = ' + MeasurementType +
                    '\nChamber/Device = ' + Device + '\nWET = ' + str(offset),
                    title = 'User Input Confirmation'):
    msgbox( 'User inputs not confirmed. Please re-run code and enter correct ' \
            'inputs')
    exit()

print('\n\nRunning main data analysis...')

####################
# In order to write to the database, two tables need to be filled. One table
# needs to be filled in first and it requires the date and gantry angle.
# Unfortunately it needs to happen before the following data extraction loop.
# It still has to test the filetype and extract all the data, but the code only
# needs the TD or "Test Date"
####################

if os.listdir(dir)[0].endswith('.mcc'):
    TEST_Dict['TEST'],TE,TD,GA = ReadTank(os.path.join(dir,os.listdir(dir)[0]))

if os.listdir(dir)[0].endswith('.csv'):
    TEST_Dict['TEST'],TD = ReadGiraffe(os.path.join(dir,os.listdir(dir)[0]))

    # The ReadGiraffe doesn't produce gantry angle because it's not in the
    # header. Therefore this requires a user input.
    GA = enterbox(  'Enter Measurement Gantry Angle',
                    'Gantry Angle during acquisition',
                    ('270')  )
    # Ensure entered GA value is a sensible entry
    try:
        float(GA)
    except ValueError:
        msgbox( 'Please re-run the program and enter an appropriate value ' \
                'for the Gantry Angle', title = 'Gantry Angle Value Error'  )
        exit()

####################
# Major loop to extract data from files
####################

# Loop through each file in the directory. This loop largely follows the loop
# in the quality system check above so comments will mainly be to detail the
# differences between this loop and the previous one.
for filename in os.listdir(dir):
    file = os.path.basename(filename)
    name = os.path.splitext(file)[0]

    if filename.endswith('.mcc'):
        Data_Dict[name], E, D, GA = ReadTank(os.path.join(dir,filename))

    if filename.endswith('.csv'):
        Data_Dict[name], D = ReadGiraffe(os.path.join(dir,filename))
        try:
            float(name)
        except ValueError:
            msgbox( 'Files must be labelled with the energy of the bragg ' \
                    'peak, please rename files', title = 'File Name Error'  )
            exit()
        E = float(name)

    # Checks title names against data names ########################################## IS THIS NECESSARY?!?! ################################################
    # (mainly for MCC files as for giraffe files, E is taken from name) #####################################################################################
    if float(name) != float(E): #############################################################################################################################
        # Creates list of files which are incorrectly labelled ##############################################################################################
        BadName.append([name,E]) ############################################################################################################################
        continue ##################################################################### IS THIS NECESSARY?!?! ################################################

    (Data_Props) = OnePDD(Data_Dict[name], E)

    ################################################## Section of code for inputting to the PDD Reference Data Table in the database
    # Subset = [  D,
    #             Gantry,
    #             E,
    #             round(float(Data_Props.Prox80),(rounddata)),
    #             round(float(Data_Props.Prox90),(rounddata)),
    #             round(float(Data_Props.Dist90),(rounddata)),
    #             round(float(Data_Props.Dist80),(rounddata)),
    #             round(float(Data_Props.Dist20),(rounddata)),
    #             round(float(Data_Props.Dist10),(rounddata)),
    #             round(float(Data_Props.HaloRat),(rounddata)),
    #             round(float(Data_Props.PTPR),(rounddata))
    #             ]
    #
    # sql = ( 'INSERT INTO [PDD Reference Data] ([ADate], [Gantry], [Energy], ' \
    #         '[Prox 80], [Prox 90], [Dist 90], [Dist 80], [Dist 20], ' \
    #         '[Dist 10], [Halo Ratio], [PTPR]) \nVALUES(?,?,?,?,?,?,?,?,?,?,?)'
    #         )
    # cursor.execute(sql, Subset)

    # Code to introduce some random noise to the data
    Data_Props.Prox80 = Data_Props.Prox80 + ((2.1 * random.random()) - 1.05)
    Data_Props.Prox90 = Data_Props.Prox90 + ((2.1 * random.random()) - 1.05)
    Data_Props.Dist90 = Data_Props.Dist90 + ((2.1 * random.random()) - 1.05)
    Data_Props.Dist80 = Data_Props.Dist80 + ((2.1 * random.random()) - 1.05)
    Data_Props.Dist20 = Data_Props.Dist20 + ((2.1 * random.random()) - 1.05)
    Data_Props.Dist10 = Data_Props.Dist10 + ((2.1 * random.random()) - 1.05)
    Data_Props.HaloRat = Data_Props.HaloRat + ((2.1 * random.random()) - 1.05)
    Data_Props.PTPR = Data_Props.PTPR + ((2.1 * random.random()) - 1.05)

    # Find the number of rows and create an index from 0 to this number
    max_row = QualSysRefData.shape[0]
    index = list(range(0, max_row))
    for x in index:
        if QualSysRefData.at[x, 'energy'] == E:
            EnergyIndex = x

    Subset = [  D,
                current_date,
                Operator,
                Device,
                Gantry,
                GA,
                E,
                round(  float(Data_Props.Prox80), (rounddata)),
                round(  float(Data_Props.Prox90), (rounddata)),
                round(  float(Data_Props.Dist90), (rounddata)),
                round(  float(Data_Props.Dist80), (rounddata)),
                round(  float(Data_Props.Dist20), (rounddata)),
                round(  float(Data_Props.Dist10), (rounddata)),
                round(  float(Data_Props.HaloRat), (rounddata)),
                round(  float(Data_Props.PTPR), (rounddata)),
                round(  (QualSysRefData.at[EnergyIndex, 'prox 80']
                        - float(Data_Props.Prox80)), (rounddata)),
                round(  (QualSysRefData.at[EnergyIndex, 'prox 90']
                        - float(Data_Props.Prox90)), (rounddata)),
                round(  (QualSysRefData.at[EnergyIndex, 'dist 90']
                        - float(Data_Props.Dist90)), (rounddata)),
                round(  (QualSysRefData.at[EnergyIndex, 'dist 80']
                        - float(Data_Props.Dist80)), (rounddata)),
                round(  (QualSysRefData.at[EnergyIndex, 'dist 20']
                        - float(Data_Props.Dist20)), (rounddata)),
                round(  (QualSysRefData.at[EnergyIndex, 'dist 10']
                        - float(Data_Props.Dist10)), (rounddata)),
                round(  (QualSysRefData.at[EnergyIndex, 'halo ratio']
                        - float(Data_Props.HaloRat)), (rounddata)),
                round(  (QualSysRefData.at[EnergyIndex, 'ptpr']
                        - float(Data_Props.PTPR)), (rounddata)),
                round(  (QualSysPlanRefData.at[EnergyIndex, 'prox 80']
                        - float(Data_Props.Prox80)), (rounddata)),
                round(  (QualSysPlanRefData.at[EnergyIndex, 'prox 90']
                        - float(Data_Props.Prox90)), (rounddata)),
                round(  (QualSysPlanRefData.at[EnergyIndex, 'dist 90']
                        - float(Data_Props.Dist90)), (rounddata)),
                round(  (QualSysPlanRefData.at[EnergyIndex, 'dist 80']
                        - float(Data_Props.Dist80)), (rounddata)),
                round(  (QualSysPlanRefData.at[EnergyIndex, 'dist 20']
                        - float(Data_Props.Dist20)), (rounddata)),
                round(  (QualSysPlanRefData.at[EnergyIndex, 'dist 10']
                        - float(Data_Props.Dist10)), (rounddata)),
                round(  (QualSysPlanRefData.at[EnergyIndex, 'halo ratio']
                        - float(Data_Props.HaloRat)), (rounddata)),
                round(  (QualSysPlanRefData.at[EnergyIndex, 'ptpr']
                        - float(Data_Props.PTPR)), (rounddata))
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

if BadName != []: ##################################################################### IS THIS NECESSARY?!?! ################################################
    msgbox( 'The following files were incorrectly labelled please correct the files and re-run. No data was written to the database:' + str(BadName)) ########
    exit() ############################################################################# IS THIS NECESSARY?!?! ###############################################

# Because the SQL statement above is changing the database (unlike the SELECT
# statements used earlier which were basically read-only) you have to 'commit'
# to these changes (i.e. save them) to the database.
conn.commit()

print('\nCompleted :)\n')

msgbox( 'Code has finished running. Please review results in QA Database',
        title = 'All Energies Completed'    )
