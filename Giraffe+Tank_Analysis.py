#Browse to the folder containing the Files
from tkinter import Tk, filedialog
import os
from PDD_Module2 import *
from easygui import multenterbox, buttonbox, enterbox, msgbox, choicebox, ynbox
# from pandas import ExcelWriter, DataFrame
import pandas as pd
from datetime import date
from openpyxl import workbook, load_workbook
import csv
import pypyodbc
import random





################################################################################
######################### FIND MEASUREMENT DATA ################################

####################
# This section is designed to find out where the files for analysis are located.
####################

# Open a dialog box to ask users where the file data is saved
msgbox( 'Please select the folder containing the data to be analysed',
        title = 'Data Selection')
root = Tk()
root.withdraw()
dir = filedialog.askdirectory()
# .askdirectory() returns an empty string if canceled so compare against ''
if dir == '':
    msgbox( 'Please re-run the code and select a folder containing the data ' \
            'to be analysed', title = 'Folder Selection Error')
    exit()





################################################################################
##################### PREPARE SOME EMPTY DATA FILES ############################

####################
# This part prepares the empty arrays etc. needed for later
####################

Data_Dict = {}      # Dictionary to insert X and Y data with Energy as the key
TEST_Dict = {}      # Dictionary to get the date for the database key
BadName = []        # Array for alert if filnames don't match the energy
Operators = []      # List to fetch names of operators from the databse
Machines = []       # List to fetch names of Gantries from the databse
Devices = []        # List to fetch names of Devices from the databse
Catagories = []     # List to fetch Catagories of devices from the databse
rounddata = 3       # For rounding the values to put into the database
CurrentDate = date.today()  # For the record later
DatabaseLocation = 'O:/protons/Work in Progress/Christian/Database/Proton/' \
                   'Test FE - CB.accdb'
QualSysDataLocation = 'O:/protons/Work in Progress/Christian/Python/' \
                      'PDD Analysis/Reference Tank Data'


################################################################################
############################### USER INPUTS ####################################

####################
# This part is for user-entry of measurement details This part accesses the QA
# Database. This will be used to pull data out of the database and also later to
# put the final results in. pypyodbc is a library allowing you to connect to an
# SQL database. Some of it is code that CG copied from google. (The important
# bit is the DBQ = bit where you put the location of the database) It appears to
# work with giving it the Front End which is needed for access to queries as
# well as tables.
####################

#Connect to the database
conn = pypyodbc.connect(
        r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};'
        r'DBQ=' + DatabaseLocation + ';'
        )
cursor = conn.cursor()

# Select Operator list from Database
# Add the "Operators" table to the cursor
cursor.execute('select * from [Operators]')
# Fetch the data from the cursor
for row in cursor.fetchall():
    # Fetch the names (2nd column) and append to the list.
    Operators.append(row[2])
# Use this new list to fill an input box (choicebox)
Operator = choicebox(   'Who performed the measurements?',
                        'Operator',
                        Operators   )
# This section ensures a button is selected
if Operator == None:
    msgbox('Please re-run the code and select an Operator')
    exit()
print('Operator = ' + Operator + '\n')

# Now that Operator has been saved can select Gantry
# (see comments from prev section)
cursor.execute('select * from [MachinesQuery]')
for row in cursor.fetchall():
    Machines.append(row[0])
Gantry = choicebox( 'Which room were the measurements performed in?',
                    'Gantry',
                    Machines    )
if Gantry == None:
    msgbox('Please re-run the code and select a room')
    exit()
print('Gantry = ' + Gantry + '\n')

# Now that Gantry has been saved can select Device
# First need to ask the user if they are performing a PDD or MLIC measurement
# to decide what database table to pull the data from.
MeasurementType = choicebox(    'Are you performing a PDD or MLIC measurement?',
                                'Measurement Type',
                                ['PDD', 'MLIC']     )
if MeasurementType == None:
    msgbox('Please re-run the code and select a Measurement Type')
    exit()
print('Measurement Type = ' + MeasurementType + '\n')

if MeasurementType == 'PDD':
    # If PDD then can select the PDD equipment (see comments from prev section)
    cursor.execute('select * from [PDD Equipment Query]')
    for row in cursor.fetchall():
        Devices.append(row[1])
        Catagories.append(row[2])
    Device = choicebox( 'Which Chamber/Device was used?',
                        'Device',
                        Devices     )
    if Device == None:
        msgbox('Please re-run the code and select a device')
        exit()
    print('Chamber/Device Used = ' + Device + '\n')
elif MeasurementType == 'MLIC':
    msgbox( 'MLIC code not complete as awaiting database module and queries ' \
            'to be written'  )
    exit()

# Run a check to make sure the device type matches the data type
# i.e. PDD Chamber matches '.mcc' files and MLIC matches '.csv' files
Catagory = Catagories[Devices.index(Device)]
if Catagory == 'MLIC':
    if os.listdir(dir)[0].endswith('.csv') != True:
        msgbox( 'Device does not match filetype. Please re run the code and ' \
                'select the correct device/folder', 'Device/File Type Error' )
        exit()
if Catagory == 'PDD Chamber':
    if os.listdir(dir)[0].endswith('.mcc') != True:
        msgbox( 'Device does not match filetype. Please re run the code and ' \
                'select the correct device/folder', 'Device/File Type Error' )
        exit()

# Enter the WET offset through a user entry box
OffSet = enterbox("Enter WET Offset (mm)", "WET Offset", ('0'))
# Ensure something was selected for WET thickness
if OffSet == None:
    msgbox( 'Please re-run the program and enter an offset, even if it\'s 0.0',
            title = 'WET box closed without entry'  )
    exit()
print('[0]\nWET = ' + str(OffSet) + '\n')
# Ensure entered WET value is a sensible entry (i.e. a number)
# Offset will be entered as a string so try turning it into a float. If Offset
# can't be turned into a float then a number wasn't entered by the user
try:
    float(OffSet)
except ValueError:
    msgbox( 'Please re-run the program and enter an appropriate \
            value for the WET offset', title='WET Value Error' )
    exit()
# Now that the check is done OffSet can actually be turned into a float
OffSet = float(OffSet)





################################################################################
######################### REFERENCE DATA CHECK #################################

# ###################
# Need to check that the reference data which is stored on the quality system
# drive still matches the reference data that is stored in the database. To do
# this the code needs to connect to and read out the data stored in the database
# To make this work a query is used which finds the 'current' database reference
# data.
# ####################

print('\nRunning the quality system data check...')

# Access the database and select the data from the PDD Reference Data saved
# there. Save the data into a DataFrame using Pandas
DatabaseRefData = pd.read_sql(  'select  [Gantry], [Energy], [Prox 80], ' \
                                '[Prox 90], [Dist 90], [Dist 80], [Dist 20], ' \
                                '[Dist 10], [Fall Off], [Halo Ratio], [PTPR] ' \
                                'from [PDD Reference Data Current Query] ' \
                                'where [Gantry]=\'' + str(Gantry) + '\'', conn)
# Order the dataframe and then reset the index (to start at 0 in the new order)
DatabaseRefData.sort_values(by=['gantry', 'energy'], inplace=True)
DatabaseRefData = DatabaseRefData.reset_index(drop=True)
# Also need to round the dataframe to a set value to match any calculated
# fields (e.g. fall off)
DatabaseRefData = DatabaseRefData.round(rounddata)

# Do the same for the plan reference data (see coments above). Also find out
# what gantry contains the planing reference data (which will be useful for
# later)
cursor.execute('select * from [PDD Reference Data Current Plan Ref Query]')
PlanRefGantry = cursor.fetchall()
PlanRefGantry = PlanRefGantry[0][1]
DatabasePlanRefData = pd.read_sql(  'select  [Gantry], [Energy], [Prox 80], ' \
                                    '[Prox 90], [Dist 90], [Dist 80], ' \
                                    '[Dist 20], [Dist 10], [Fall Off], ' \
                                    '[Halo Ratio], [PTPR] from [PDD ' \
                                    'Reference Data Current Plan Ref Query] '
                                    , conn  )
DatabasePlanRefData.sort_values(by=['gantry', 'energy'], inplace=True)
DatabasePlanRefData = DatabasePlanRefData.reset_index(drop=True)
DatabasePlanRefData = DatabasePlanRefData.round(rounddata)

####################
# Major loop to extract data from reference files saved in the quality system
####################

QualSysRefData=[]
QualSysPlanRefData=[]
# Create a list to use in subsequent 'for' loop
GantryList = [[Gantry, 1], [PlanRefGantry, 2]]
# Loop through to pull out the gantry specific and the planning reference data
for x in GantryList:
    for filename in os.listdir(QualSysDataLocation + '/' + str(x[0])):
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

Array = [   [DatabaseRefData, QualSysRefData],
            [DatabasePlanRefData, QualSysPlanRefData]   ]
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
                    '\nChamber/Device = ' + Device + '\nWET = ' + str(OffSet),
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
                CurrentDate,
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
