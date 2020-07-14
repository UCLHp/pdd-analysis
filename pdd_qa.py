import easygui as eg
import os
from datetime import date
import pypyodbc
import pandas as pd
import test.test_version
import pdd_module as pdd
import database_interaction as di


def main():

    test.test_version.check_version()

    ###########################################################################
    # SELECT DATA AND LOAD REFERENCE DIRECTORIES
    ###########################################################################

    qadir = eg.diropenbox(title='Please select folder containing pdd data')

    if not dir:
        eg.msgbox('Please re-run the code and select a folder containing the '
                  'data to be analysed', title='Folder Selection Error')
        raise SystemExit

    DATABASE_DIR = ('\\\\krypton\\rtp-share$\\protons\\Work in Progress'
                    '\\Christian\\Database\\Proton\\Test FE - CB.accdb')
    REFDATA_DIR = ('\\\\krypton\\rtp-share$\\protons\\Work in Progress'
                   '\\Christian\\Python\\PDD Analysis\\Reference Tank Data')
    CURRENT_DATE = date.today()  # For the record later
    ROUNDDATA = 3    # For rounding so sig figs match between qs and db

    ###########################################################################
    # CONNECT TO DB AND SELECT USER DEFINED VARIABLES (GANTRY ETC.)
    ###########################################################################

    # Select Operator
    operators = di.db_fetch(DATABASE_DIR, 'Operators')
    operator = di.select_from_list('Select User', operators, column=2)
    print(f'Operator = {operator}\n')

    # Select Gantry
    machines = di.db_fetch(DATABASE_DIR, 'MachinesQuery')
    gantry = di.select_from_list('Select Gantry', machines, column=0)
    print(f'Gantry = {gantry}\n')

    # Select measurement device
    devices = di.db_fetch(DATABASE_DIR, 'PDD Equipment Query')
    device = di.select_from_list('Select Chamber/Device', devices, column=1)
    print(f'Chamber/Device Used = {device}\n')

    measurement_type = [item[2] for item in devices if item[1] == device][0]

    # Enter the WET offset through a user entry box
    offset = eg.enterbox("Enter WET Offset (mm)", "WET Offset", ('0'))
    if not offset:
        eg.msgbox('Offset Value required to run \n'
                  'Code will terminate',
                  title='No WET value entered')
        raise SystemExit
    try:
        offset = float(offset)
    except (ValueError, TypeError) as e:
        eg.msgbox('Please re-run the program and enter an appropriate '
                  'value for the WET offset', title='WET Value Error')
        raise SystemExit
    print(f'[0]\nWET = {str(offset)} \n')

    print('\nRunning the quality system data check...')

    ###########################################################################
    # CHECK REFERENCE DATA FOR BOTH TPS AND CURRENT GANTRY
    ###########################################################################

    # Gantry specific reference data from DataBase
    ref_props_gant_db = di.props_table_from_db(DATABASE_DIR, ROUNDDATA, gantry)
    ref_props_gant_db.name = 'ref_props_gant_db'

    # TPS reference data from DataBase
    ref_props_tps_db = di.props_table_from_db(DATABASE_DIR, ROUNDDATA)
    ref_props_tps_db.name = 'ref_props_tps_db'

    # Gantry specific reference data from QS
    ref_data_gant_qs = pdd.directory_to_dictionary(os.path.join(REFDATA_DIR,
                                                                gantry))
    ref_props_gant_qs = pdd.dict_to_df(ref_data_gant_qs, ROUNDDATA)
    ref_props_gant_qs.name = 'ref_props_gant_qs'

    # TPS reference data from QS
    ref_data_tps_qs = pdd.directory_to_dictionary(os.path.join(REFDATA_DIR,
                                                               'Gantry 1'))
    ref_props_tps_qs = pdd.dict_to_df(ref_data_tps_qs, ROUNDDATA)
    ref_props_tps_qs.name = 'ref_props_tps_qs'

    pdd.check_dataframes(ref_props_gant_db, ref_props_gant_qs)

    pdd.check_dataframes(ref_props_tps_db, ref_props_tps_qs)

    print('\nQuality System Data Matches Database')

    ###########################################################################
    # WRITE RESULTS TO DATABASE
    ###########################################################################

    if measurement_type == 'MLIC':
        GA = eg.enterbox('Enter Measurement Gantry Angle',
                         'Gantry Angle during acquisition',
                         ('270')
                         )
        try:
            float(GA)
        except (ValueError, TypeError) as e:
            eg.msgbox('Please re-run the program and enter an appropriate '
                      'Gantry Angle', title='Gantry Angle Value Error')
            raise SystemExit

    # Check that the user has slected the correct opperator, gantry, etc.
    # This data will be written straight into the database and, given
    # the amount of it, it will be annoying/time conssuming to correct this
    # once it's already in the database.

    if not eg.ynbox(msg='Please confirm that the following information is '
                    'correct... \n\nOperator = ' + operator + '\nGantry = ' +
                    gantry + '\nMeasurement Type = ' + measurement_type +
                    '\nChamber/Device = ' + device + '\nWET = ' + str(offset),
                    title='User Input Confirmation'):
        eg.msgbox('User inputs not confirmed. Please re-run', 'Input Error')

        raise SystemExit

    print('\n\nRunning main data analysis...')

    measured_data = pdd.directory_to_dictionary(qadir)

    conn, cursor = di.db_connect(DATABASE_DIR)

    for key in sorted(measured_data.keys()):
        metrics = pdd.PeakProperties(measured_data[key].data, key)
        if measurement_type == 'MLIC':
            measured_data[key].gantry_angle = GA

        db = [measured_data[key].date, CURRENT_DATE, operator, device, gantry,
              measured_data[key].gantry_angle, int(key),
              round(metrics.Prox80, ROUNDDATA),
              round(metrics.Prox90, ROUNDDATA),
              round(metrics.Dist90, ROUNDDATA),
              round(metrics.Dist80, ROUNDDATA),
              round(metrics.Dist20, ROUNDDATA),
              round(metrics.Dist10, ROUNDDATA),
              round(metrics.HaloRat, ROUNDDATA),
              round(metrics.PTPR, ROUNDDATA),
              round(ref_props_gant_qs.query(f'energy=={key}')['prox 80'].item()
              - metrics.Prox80, ROUNDDATA),
              round(ref_props_gant_qs.query(f'energy=={key}')['prox 90'].item()
              - metrics.Prox90, ROUNDDATA),
              round(ref_props_gant_qs.query(f'energy=={key}')['dist 90'].item()
              - metrics.Dist90, ROUNDDATA),
              round(ref_props_gant_qs.query(f'energy=={key}')['dist 80'].item()
              - metrics.Dist80, ROUNDDATA),
              round(ref_props_gant_qs.query(f'energy=={key}')['dist 20'].item()
              - metrics.Dist20, ROUNDDATA),
              round(ref_props_gant_qs.query(f'energy=={key}')['dist 10'].item()
              - metrics.Dist10, ROUNDDATA),
              round(ref_props_gant_qs.query(f'energy=={key}')['halo ratio'].item()
              - metrics.HaloRat, ROUNDDATA),
              round(ref_props_gant_qs.query(f'energy=={key}')['ptpr'].item()
              - metrics.PTPR, ROUNDDATA),
              round(ref_props_tps_qs.query(f'energy=={key}')['prox 80'].item()
              - metrics.Prox80, ROUNDDATA),
              round(ref_props_tps_qs.query(f'energy=={key}')['prox 90'].item()
              - metrics.Prox90, ROUNDDATA),
              round(ref_props_tps_qs.query(f'energy=={key}')['dist 90'].item()
              - metrics.Dist90, ROUNDDATA),
              round(ref_props_tps_qs.query(f'energy=={key}')['dist 80'].item()
              - metrics.Dist80, ROUNDDATA),
              round(ref_props_tps_qs.query(f'energy=={key}')['dist 20'].item()
              - metrics.Dist20, ROUNDDATA),
              round(ref_props_tps_qs.query(f'energy=={key}')['dist 10'].item()
              - metrics.Dist10, ROUNDDATA),
              round(ref_props_tps_qs.query(f'energy=={key}')['halo ratio'].item()
              - metrics.HaloRat, ROUNDDATA),
              round(ref_props_tps_qs.query(f'energy=={key}')['ptpr'].item()
              - metrics.PTPR, ROUNDDATA)
              ]

        sql = ('INSERT INTO [PDD Results] ([ADate], [Record Date], '
               '[Operator], [Equipment], [MachineName], [GantryAngle], '
               '[Energy], [Prox 80], [Prox 90], [Dist 90], [Dist 80], '
               '[Dist 20], [Dist 10], [Halo Ratio], [PTPR], '
               '[Prox 80 Gantry Diff], [Prox 90 Gantry Diff], '
               '[Dist 90 Gantry Diff], [Dist 80 Gantry Diff], '
               '[Dist 20 Gantry Diff], [Dist 10 Gantry Diff], '
               '[Halo Ratio Gantry Diff], [PTPR Gantry Diff], '
               '[Prox 80 Plan Diff], [Prox 90 Plan Diff], '
               '[Dist 90 Plan Diff], [Dist 80 Plan Diff], '
               '[Dist 20 Plan Diff], [Dist 10 Plan Diff], '
               '[Halo Ratio Plan Diff], [PTPR Plan Diff]) \n'
               'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'
               '?,?,?,?,?)'
               )
        try:
            cursor.execute(sql, db)
        except pypyodbc.IntegrityError:
            eg.msgbox('Data already exists in database\n'
                      'Please come up with something original',
                      title='Data duplication')
            raise SystemExit

    conn.commit()

    print('\nCompleted :)\n')

    eg.msgbox('Code finished running. Please review results in QA Database',
              title='All Energies Completed')


if __name__ == '__main__':
    main()
