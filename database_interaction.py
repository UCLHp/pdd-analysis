import pypyodbc
import easygui as eg
import pandas as pd


def db_connect(DATABASE_DIR, *, pswrd=False):
    '''
    Function to connect to connect to the access database at location defined
    by the DATABASE_DIR input. Connection will fail if password is required
    but not supplied
    '''
    if pswrd:
        conn = pypyodbc.connect(
                'Driver={Microsoft Access Driver (*.mdb, *.accdb)};'
                'DBQ=' + DATABASE_DIR + ';'
                f'PWD={pswrd}'
                )
    else:
        conn = pypyodbc.connect(
                'Driver={Microsoft Access Driver (*.mdb, *.accdb)};'
                'DBQ=' + DATABASE_DIR + ';'
                )
    cursor = conn.cursor()
    return conn, cursor


def db_fetch(DATABASE_DIR, db_table, *, pswrd=False, column=None):
    '''
    A function to pull a table of data from a database table and output as a
    list. If column set to integer, selects that column from the table only
    '''
    conn, cursor = db_connect(DATABASE_DIR, pswrd=pswrd)

    cursor.execute(f'select * from [{db_table}]')
    if column is None:
        db_table = [list(row) for row in cursor.fetchall()]
        return db_table
    else:
        db_column = [row[column] for row in cursor.fetchall()]
        return db_column


def select_from_list(message, input_list, column=None):
    '''
    Function to get user to select from a list of data. If the data is in a
    table format, the column containing the desired list should be defined
    '''
    if column is None:
        choice = eg.choicebox(message, 'Please make a selection', input_list)
    else:
        choices = [row[column] for row in input_list]
        choice = eg.choicebox(message, 'Please make a selection', choices)

    if not choice:
        eg.msgbox(f'No selection made\n'
                  'Code will terminate', 'No user input')
        raise SystemExit
    else:
        return choice


def props_table_from_db(DATABASE_DIR, ROUNDDATA, gantry=None, *, pswrd=False):
    '''
    Return a pandas dataframe containing all the reference data properties
    stored in the access database. If no gantry selected, tps data table will
    be returned
    '''
    conn, cursor = db_connect(DATABASE_DIR, pswrd=pswrd)

    if gantry:
        conditional_string = 'where [Gantry]=\'' + str(gantry) + '\''
    else:
        # "" and '' used instead of [] becuase ? is functional character in SQL
        conditional_string = "where 'Planning Reference?'=True"

    ref_props = pd.read_sql('select  [Energy], [Prox 80], [Prox 90], '
                            '[Dist 90], [Dist 80], [Dist 20], [Dist 10], '
                            '[Fall Off], [Halo Ratio], [PTPR] '
                            'from [PDD Reference Data Current Query] '
                            + conditional_string, conn
                            )
    # Default energy ordering puts 100MeV before 70MeV, sort values for 70-245
    ref_props.sort_values(by=['energy'], inplace=True)
    ref_props = ref_props.reset_index(drop=True)
    # Also need to round the dataframe to a set value to match any calculated
    # fields (e.g. fall off)
    ref_props = ref_props.round(ROUNDDATA)
    return ref_props
