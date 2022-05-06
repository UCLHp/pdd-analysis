'''
Reading and analysis of csv files outputted by the Giraffe.

This programme is capable of assessing both single shot and also movie mode
outputs. It is also capable of dealing with the duplicated curves that can
occur in movie mode (but it is not capable of dealing with triplicate curves
and higher.)

This programme uses Bortfeld fitting to determine the curve parameters.

'''


import os
from datetime import date, datetime, timedelta

import easygui as eg
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import PySimpleGUI as sg

import pdd_module as pm
import database_interaction as di
import pdf_report as pdf
import giraffe_gui as gg
import giraffe_config as gc


class ReferenceData:
    '''
    Pull reference data from csv
    '''

    def __init__(self, dirpath, gantry):
        filename_tps = 'Giraffe Reference Data - TPS.csv'
        filepath_tps = os.path.join(dirpath, filename_tps)
        filename_gantry = 'Giraffe Reference Data - ' + gantry + '.csv'
        filepath_gantry = os.path.join(dirpath, filename_gantry)
        self.df_gantry = pd.read_csv(filepath_gantry, index_col=0)
        self.df_tps = pd.read_csv(filepath_tps, index_col=0)


class GUI:
    '''
    Acquire user inputs.
    '''

    def __init__(self, database_dir, pswrd):
        # Select Operator
        operators = di.db_fetch(database_dir, 'Operators', pswrd=pswrd)
        operators = sorted([row[2] for row in operators])
        operators.append('')
        # Select Gantry
        machines = di.db_fetch(database_dir, 'Machines', pswrd=pswrd)
        machines = sorted([row[0] for row in machines if 'Gantry' in row[0]])
        # Select Gantry
        gantry_angles = ['270', '0', '90', '180']
        # Select Equipment
        # equipment_list = di.db_fetch(database_dir, 'Assets', pswrd=pswrd)
        # equipment_list = [row[1]
        #                   for row in equipment_list if 'Giraffe MLIC' in row[1]]
        equipment_list = di.db_fetch(
            database_dir, 'PDD Equipment Query', pswrd=pswrd)
        equipment_list = [row[0] for row in equipment_list]

        values = gg.giraffe_gui(operators=operators,
                                machines=machines,
                                gantry_angles=gantry_angles,
                                equipment_list=equipment_list)

        self.adate = None
        self.report_dirpath = values['REPORT_FOLDER']
        self.operator_1 = values['OPERATOR_1']
        if values['OPERATOR_2'] == '':
            values['OPERATOR_2'] = None
        self.operator_2 = values['OPERATOR_2']
        self.gantry = values['GANTRY']
        self.gantry_angle = values['GANTRY_ANGLE']
        self.equipment = values['EQUIPMENT']
        self.title = None
        self.dirname = None
        self.f1 = [values['F1'], measured_energies(values['F1_ENERGIES'])]
        self.f2 = [values['F2'], measured_energies(values['F2_ENERGIES'])]
        self.f3 = [values['F3'], measured_energies(values['F3_ENERGIES'])]
        self.f4 = [values['F4'], measured_energies(values['F4_ENERGIES'])]
        self.f5 = [values['F5'], measured_energies(values['F5_ENERGIES'])]


def measured_energies(selection):
    '''
    Get list of delivered energies (preset or custom)
    '''

    if selection == '':
        energies = None

    elif selection == '70-210MeV (every 10MeV)':
        energies = [210, 200, 190, 180, 170, 160,
                    150, 140, 130, 120, 110, 100, 90, 80, 70]

    elif selection == '220-245MeV (every 10MeV + 245MeV)':
        energies = [245, 240, 230, 220]

    elif selection == 'Custom':
        energies = gg.custom_energies()

    else:
        print('Unknown selection')
        os.system('pause')
        raise SystemExit

    return energies


def check_curve_list(pdd, energies):

    # Create an empty curve list searching for any duplicates
    curve_list = []

    # Search for duplicate curves
    if len(energies) > len(pdd.data):
        # Fewer curves than energies so exit
        print('Not enough curves for the number of energies supplied. '
              'Please try again')
        os.system('pause')
        raise SystemExit

    elif len(energies) < len(pdd.data):
        # More curves than energies so search for duplicates.
        # NB: only works for duplicates not triplicates etc.
        print('There are more curves than supplied energies. '
              'Searching for duplicate curves')
        for i in range(0, pdd.no_of_curves):
            # Use a dummy energy of 100MeV to run the code.
            props = pm.PeakProperties(pdd.data[i], 100, bortfeld_fit_bool=True)
            curve_list.append(props)
        pop_list = []
        for i in range(0, len(pdd.data)-1):
            # Check for curves with similar energies
            if curve_list[i].E0_fit - curve_list[i+1].E0_fit < 2:
                choice = gg.same_curve(i, curve_list)
                if choice is True:
                    # They are the same energy so add together etc.
                    data_join = pdd.data[i]
                    data_join[1] = np.add(pdd.data[i][1], pdd.data[i+1][1])
                    pdd.data[i] = data_join
                    pop_list.append(i+1)
        count = 0
        for i in pop_list:
            pdd.data.pop(i-count)
            count = count + 1

    return pdd


def create_curve_list(pdd, energies):
    # Double check that now there are the right number of curves and exit if
    # not, otherwise make a new curve_list.
    curve_list = []
    if len(energies) == len(pdd.data):
        # Same no. of energies as curves so create list of the curve properties
        for i in range(0, len(pdd.data)):
            props = pm.PeakProperties(
                pdd.data[i], energies[i], bortfeld_fit_bool=True)
            curve_list.append(props)
    else:
        print('After duplicate search number of curves does not match the '
              'number of energies supplied. Please try again')
        print('No. of curves: ' + str(len(pdd.data)))
        print('No. of energies: ' + str(len(energies)))
        os.system('pause')
        raise SystemExit
    return curve_list


def plot_results(pdd, energies, curve_list, UserInput):
    # Pull out the results and also plot to make sure everything looks good.
    max_e = max(energies)
    min_e = min(energies)
    plt.figure(figsize=(12, 8))
    for i in range(0, len(pdd.data)):
        if abs(curve_list[i].E0_fit - energies[i]) > 5:
            print('WARNING: Significant difference between expected and '
                  'fitted energies.')
        print('Energy = ' + str(energies[i]))
        print(f'E0 = {curve_list[i].E0_fit}\n'
              f'P80 = {curve_list[i].Prox80}\n'
              f'P90 = {curve_list[i].Prox90}\n'
              f'D90 = {curve_list[i].Dist90}\n'
              f'D80 = {curve_list[i].Dist80}\n'
              f'D20 = {curve_list[i].Dist20}\n'
              f'D10 = {curve_list[i].Dist10}\n'
              f'Fall Off = {curve_list[i].FallOff}\n'
              f'PTPR = {curve_list[i].PTPR}\n'
              f'Peak Width = {curve_list[i].PeakWidth}\n'
              f'Halo Ratio = {curve_list[i].HaloRat}\n'
              f'NIST Range = {curve_list[i].NISTRange}\n'
              f'NIST Diff = {curve_list[i].NISTDiff}\n')
        # Experimental data
        plt.scatter(pdd.data[i][0], pdd.data[i][1],
                    label=str(energies[i])+" MeV", s=0.5)
        # Starting fit with initial Phi0, R0, sigma, epsilon
        plt.plot(curve_list[i].bortfeld_data[0],
                 curve_list[i].bortfeld_data[1]/curve_list[i].bortfeld_scaler,
                 label=str(round(curve_list[i].E0_fit, 2))+" MeV")
    # Format plot
    plt.legend(loc="upper right", fontsize=6)
    plt.title("Energy = " + str(max_e)+'-'+str(min_e)+'MeV', fontsize=22)
    plt.xlabel("Depth (mm)", fontsize=18)
    plt.ylabel("Normalised dose", fontsize=18)
    plt.xticks(size=16)
    plt.yticks(size=16)
    filename = os.path.join(UserInput.dirname,
                            str(max_e)+'-'+str(min_e)+'MeV.png')
    plt.savefig(filename, dpi=300, bbox_inches='tight', pad_inches=0)
    # plt.show()

    return


def compile_results(pdd, energies, UserInput, curve_list):

    CURRENT_DATE = date.today()
    dirpath = os.path.join(os.getcwd(), 'data')
    # dirpath = 'O:\\protons\\Work in Progress\\Christian\\Python\\GitHub\\pdd-analysis\\data'
    RefData = ReferenceData(dirpath, UserInput.gantry)

    dict = {'ADate': [],
            'Record Date': [],
            'Operator 1': [],
            'Operator 2': [],
            'Equipment': [],
            'MachineName': [],
            'GantryAngle': [],
            'Energy': [],
            'E0': [],
            'P80': [], 'P90': [], 'D90': [], 'D80': [], 'D20': [], 'D10': [],
            'Fall Off': [], 'PTPR': [], 'Peak Width': [], 'Halo Ratio': [],
            'P80 Gantry Diff': [], 'P90 Gantry Diff': [],
            'D90 Gantry Diff': [], 'D80 Gantry Diff': [],
            'D20 Gantry Diff': [], 'D10 Gantry Diff': [],
            'Fall Off Gantry Diff': [], 'PTPR Gantry Diff': [],
            'Peak Width Gantry Diff': [], 'Halo Ratio Gantry Diff': [],
            'P80 Plan Diff': [], 'P90 Plan Diff': [],
            'D90 Plan Diff': [], 'D80 Plan Diff': [],
            'D20 Plan Diff': [], 'D10 Plan Diff': [],
            'Fall Off Plan Diff': [], 'PTPR Plan Diff': [],
            'Peak Width Plan Diff': [], 'Halo Ratio Plan Diff': [],
            'Plot_X': [], 'Plot_Y': [], 'Comments': []
            }

    for i in range(0, len(pdd.data)):
        if abs(curve_list[i].E0_fit - energies[i]) > 5:
            print('WARNING: Significant difference between expected and '
                  'fitted energies.')

        dict['ADate'].append(pdd.date)
        dict['Record Date'].append(CURRENT_DATE)
        dict['Operator 1'].append(UserInput.operator_1)
        dict['Operator 2'].append(UserInput.operator_2)
        dict['Equipment'].append(UserInput.equipment)
        dict['MachineName'].append(UserInput.gantry)
        dict['GantryAngle'].append(UserInput.gantry_angle)
        dict['Energy'].append(energies[i])
        dict['E0'].append(curve_list[i].E0_fit)
        dict['P80'].append(curve_list[i].Prox80)
        dict['P90'].append(curve_list[i].Prox90)
        dict['D90'].append(curve_list[i].Dist90)
        dict['D80'].append(curve_list[i].Dist80)
        dict['D20'].append(curve_list[i].Dist20)
        dict['D10'].append(curve_list[i].Dist10)
        dict['Fall Off'].append(curve_list[i].FallOff)
        dict['PTPR'].append(curve_list[i].PTPR)
        dict['Peak Width'].append(curve_list[i].PeakWidth)
        dict['Halo Ratio'].append(curve_list[i].HaloRat)
        dict['Plot_X'].append(pdd.data[i][0])
        dict['Plot_Y'].append(pdd.data[i][1])
        dict['Comments'].append(None)

        # Doing it in a loop in case certain keys are missing from the
        # reference data
        keys = ['P80', 'P90', 'D90', 'D80', 'D20', 'D10', 'Fall Off', 'PTPR',
                'Peak Width', 'Halo Ratio']
        for key in keys:
            try:
                dict[key + ' Gantry Diff'].append(
                    dict[key][-1] - RefData.df_gantry[key][energies[i]])
            except KeyError:
                dict[key + ' Gantry Diff'].append(None)
            try:
                dict[key + ' Plan Diff'].append(
                    dict[key][-1] - RefData.df_tps[key][energies[i]])
            except KeyError:
                dict[key + ' Plan Diff'].append(None)

    return dict


def write_to_db(dict, database_dir, pswrd=''):
    '''
    Write to the PDD Session and PDD Results Tables
    '''

    conn, cursor = di.db_connect(database_dir, pswrd=pswrd)

    sql = ('INSERT INTO [PDD Session] ([ADate], [Record Date], '
           '[Operator 1], [Operator 2], [Equipment], [MachineName], '
           '[GantryAngle], [Comments]) \n'
           'VALUES(?,?,?,?,?,?,?,?)')
    keys = ['ADate', 'Record Date', 'Operator 1', 'Operator 2', 'Equipment',
            'MachineName', 'GantryAngle', 'Comments']
    record = []
    for key in keys:
        record.append(dict[key][0])

    cursor.execute(sql, record)
    conn.commit()

    sql = ('INSERT INTO [PDD Results] ([ADate], [MachineName], [Energy], '
           '[Prox 80], [Prox 90], [Dist 90], [Dist 80], '
           '[Dist 20], [Dist 10], [Halo Ratio], [PTPR], '
           '[Prox 80 Gantry Diff], [Prox 90 Gantry Diff], '
           '[Dist 90 Gantry Diff], [Dist 80 Gantry Diff], '
           '[Dist 20 Gantry Diff], [Dist 10 Gantry Diff], '
           '[Halo Ratio Gantry Diff], [PTPR Gantry Diff], '
           '[Prox 80 Plan Diff], [Prox 90 Plan Diff], '
           '[Dist 90 Plan Diff], [Dist 80 Plan Diff], '
           '[Dist 20 Plan Diff], [Dist 10 Plan Diff], '
           '[Halo Ratio Plan Diff], [PTPR Plan Diff]) \n'
           'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)')
    keys = ['ADate', 'MachineName', 'Energy', 'P80', 'P90', 'D90', 'D80',
            'D20', 'D10', 'Halo Ratio', 'PTPR', 'P80 Gantry Diff',
            'P90 Gantry Diff', 'D90 Gantry Diff', 'D80 Gantry Diff',
            'D20 Gantry Diff', 'D10 Gantry Diff', 'Halo Ratio Gantry Diff',
            'PTPR Gantry Diff', 'P80 Plan Diff', 'P90 Plan Diff',
            'D90 Plan Diff', 'D80 Plan Diff', 'D20 Plan Diff',
            'D10 Plan Diff', 'Halo Ratio Plan Diff', 'PTPR Plan Diff']
    for i in range(0, len(dict[keys[0]])):
        record = []
        for key in keys:
            record.append(dict[key][i])
        cursor.execute(sql, record)
        conn.commit()

    cursor.close()
    conn.close()

    return


def check_dates(dummy_date, date):
    if dummy_date == '':
        dummy_date = date
    else:
        dummy_date = datetime.strptime(dummy_date, '%d/%m/%Y %H:%M:%S')
        date = datetime.strptime(date, '%d/%m/%Y %H:%M:%S')
        dates_sorted = sorted([dummy_date, date])
        diff = dates_sorted[1] - dates_sorted[0]
        if diff <= timedelta(hours=1):
            print('Time difference between files <=1 hour. Therefore taking '
                  'the ADate from the first file.')
            date = dummy_date
        else:
            choice = gg.time_diff()
            if choice:
                print('Time difference between files >1 hour but still '
                      'combining.')
                date = dummy_date
            else:
                print('Time difference between files >1 hour. Starting again.')
                os.system('pause')
                raise SystemExit
        dummy_date = dummy_date.strftime('%d/%m/%Y %H:%M:%S')
        date = date.strftime('%d/%m/%Y %H:%M:%S')
    return dummy_date, date


def create_output_dir(count, date, UserInput):

    date = datetime.strptime(date, '%d/%m/%Y %H:%M:%S')
    UserInput.title = ('Giraffe - ' + str(UserInput.gantry) + ' - '
                       + date.strftime('%Y-%m-%d %H\'%M\'%S'))
    if UserInput.dirname is None:
        UserInput.dirname = os.path.join(
            UserInput.report_dirpath, UserInput.title)
    if count == 0:
        if os.path.exists(UserInput.dirname):
            print('The directory ' + str(UserInput.dirname) + ' already exists'
                  '\nCreating a new directory ' + UserInput.dirname + '-Copy')
            UserInput.dirname = UserInput.dirname + '-Copy'
            os.mkdir(UserInput.dirname)
        else:
            os.mkdir(UserInput.dirname)

    return UserInput


def add_comments(dict, UserInput):

    choice, comments = gg.comments(UserInput)
    if choice:
        dict['Comments'] = [comments for x in dict['Comments']]

    return choice, dict


def map_drive():

    if (os.getlogin() == 'rtadmin') or (os.getlogin() == 'rtpadmin'):
        print('User ' + os.getlogin()
              + ' detected. Opening GUI to request UCLH credentials')
        values, closed = gg.map_drive_credentials()
        user = values['USER_NAME']
        password = values['PASSWORD']

        cmd1 = 'net use a: /del'
        cmd2 = 'net use a: \\\\9.140.36.84\\RTPAssetDatabase /user:UCLH\\' + user + ' ' + password

        # Disconnect anything on A
        os.system(cmd1)
        # Connect to shared drive, use drive letter A
        os.system(cmd2)
    else:
        print('User ' + os.getlogin()
              + ' detected. Not rtadmin or rtpadmin so assuming has UCLH access rights')
        pass


def disconnect_drive():

    if (os.getlogin() == 'rtadmin') or (os.getlogin() == 'rtpadmin'):
        print('User ' + os.getlogin()
              + ' detected. Disconnecting previously mapped A:// Drive')
        cmd1 = 'net use a: /del'
        os.system(cmd1)
    else:
        print('User ' + os.getlogin()
              + ' detected. Not rtadmin or rtpadmin so no need to remove A:\\ Drive')
        pass


def main():

    map_drive()

    GiraffeConfig = gc.GiraffeConfig()
    database_dir = GiraffeConfig.db_dirpath_fe
    database_password = GiraffeConfig.db_password_fe

    UserInput = GUI(database_dir, database_password)

    results = [UserInput.f1, UserInput.f2,
               UserInput.f3, UserInput.f4, UserInput.f5]

    dict = {}
    dummy_date = ''
    for count, elem in enumerate(results):
        file = elem[0]
        energies = elem[1]

        if file == '':
            pass
        else:
            print('\nAnalysing data in file - ' + str(file))
            pdd = pm.DepthDoseFile(file)

            # Check the number of energies matches the number of curves and
            # adjust for duplicates.
            pdd = check_curve_list(pdd, energies)

            dummy_date, pdd.date = check_dates(dummy_date, pdd.date)
            UserInput.adate = pdd.date
            create_output_dir(count, pdd.date, UserInput)

            # Create a list of the properties of the measured curves
            curve_list = create_curve_list(pdd, energies)

            # Plot the measured and fitted curves.
            plot_results(pdd, energies, curve_list, UserInput)

            if dict == {}:
                # Compile the results into a dictionary
                dict = compile_results(pdd, energies, UserInput, curve_list)
            else:
                dict_dummy = compile_results(
                    pdd, energies, UserInput, curve_list)
                for key in dict.keys():
                    dict[key].extend(dict_dummy[key])

    print('\nCreating PDF Report. This may take a few minutes')
    pdf.write_summary_report(dict, UserInput)
    print('Completed')

    # Add comments
    choice, dict = add_comments(dict, UserInput)

    if choice:
        # Write the results to the database
        print('\nWriting to database')
        write_to_db(dict, database_dir, pswrd=database_password)
        print('Completed')
    else:
        print('\nExiting without writing to database')

    disconnect_drive()

    # Pause before finishing (needed for when run as an executable)
    os.system('pause')


if __name__ == "__main__":
    main()
