import PySimpleGUI as sg
import os


def giraffe_gui_check(values):

    req_fields = ['REPORT_FOLDER', 'OPERATOR_1', 'GANTRY', 'GANTRY_ANGLE',
                  'EQUIPMENT', 'F1', 'F1_ENERGIES']

    check = True
    for field in req_fields:
        if values[field] == '':
            print(field + ' is a required field')
            check = False
    for field in ['F1', 'F2', 'F3', 'F4', 'F5']:
        if values[field] != '':
            if values[field+'_ENERGIES'] == '':
                print(field + '_ENERGIES is required as a file has '
                      'been entered in ' + field)
                check = False
            if not values[field].endswith('.csv'):
                print(field + ' does not end with .csv')
                check = False
    if values['OPERATOR_1'] == values['OPERATOR_2']:
        print('Operator 1 and Operator 2 cannot be the same')
        check = False

    return check


def giraffe_gui(operators=[], machines=[], gantry_angles=[], equipment_list=[]):

    sg.theme('Topanga')

    img = 'data\\logo\\giraffe_small.png'
    energies = ['70-210MeV (every 10MeV)',
                '220-245MeV (every 10MeV + 245MeV)',
                'Custom']

    frame = sg.Frame('User Input',
                     [[sg.Text('Operator 1:', size=(12, 1)), sg.InputOptionMenu(
                            operators, key='OPERATOR_1', size=(12, 1))],
                      [sg.Text('Operator 2:', size=(12, 1)), sg.InputOptionMenu(
                            operators, key='OPERATOR_2', size=(12, 1))],
                      [sg.Text('Gantry:', size=(12, 1)), sg.InputOptionMenu(
                            machines, key='GANTRY', size=(12, 1))],
                      [sg.Text('Gantry Angle:', size=(12, 1)), sg.InputOptionMenu(
                            gantry_angles, key='GANTRY_ANGLE', size=(12, 1))],
                      [sg.Text('Equipment:', size=(12, 1)), sg.InputOptionMenu(
                            equipment_list, key='EQUIPMENT', size=(12, 1))]])

    SYMBOL_UP = '▲'
    SYMBOL_DOWN = '▼'

    extra_files = sg.pin(sg.Column([[sg.Text('File 3:', size=(12, 1)), sg.Input(
                                            key='F3'), sg.FileBrowse()],
                                    [sg.Text('File 3 - Energies:', size=(12, 1)), sg.InputOptionMenu(
                                            energies, key='F3_ENERGIES', size=(35, 1))],
                                    [sg.Text('File 4:', size=(12, 1)), sg.Input(
                                            key='F4'), sg.FileBrowse()],
                                    [sg.Text('File 4 - Energies:', size=(12, 1)), sg.InputOptionMenu(
                                            energies, key='F4_ENERGIES', size=(35, 1))],
                                    [sg.Text('File 5:', size=(12, 1)), sg.Input(
                                            key='F5'), sg.FileBrowse()],
                                    [sg.Text('File 5 - Energies:', size=(12, 1)), sg.InputOptionMenu(
                                            energies, key='F5_ENERGIES', size=(35, 1))]],
                                   key='EXTRA FILES', visible=False))

    layout = [[sg.Text('Select the report output location (Routine QA/IDD/Reports)')],
              [sg.Text('Report Folder:', size=(12, 1)), sg.Input(
                  key='REPORT_FOLDER'), sg.FolderBrowse()],
              [sg.Text('_'*70)],
              [sg.Text('Select the measurement parameters')],
              [frame, sg.Image(img, size=(150, 150))],
              [sg.Text('File 1:', size=(12, 1)), sg.Input(
                           key='F1'), sg.FileBrowse()],
              [sg.Text('File 1 - Energies:', size=(12, 1)), sg.InputOptionMenu(
                        energies, key='F1_ENERGIES', size=(35, 1))],
              [sg.Text('File 2', size=(12, 1)), sg.Input(
                           key='F2'), sg.FileBrowse()],
              [sg.Text('File 2 - Energies:', size=(12, 1)), sg.InputOptionMenu(
                        energies, key='F2_ENERGIES', size=(35, 1))],
              [sg.Text(SYMBOL_UP, enable_events=True, key='-OPEN EXTRA FILES-'),
               sg.Text('Extra Files', enable_events=True, key='-OPEN EXTRA FILES TEXT-')],
              [extra_files],
              [sg.Button('OK'), sg.Button('Exit')]]

    window = sg.Window('Giraffe User Input', layout)

    event, values = window.read()
    open = False
    while True:  # Event Loop
        if event == sg.WIN_CLOSED or event == 'Exit':
            event, values = window.read()
            print(values)
            closed = False
            break
        if event == 'OK':
            event, values = window.read()
            check = giraffe_gui_check(values)
            if check is True:
                closed = True
                break
            else:
                print('UserInput check failed see notes above.\n')
                pass
        if event.startswith('-OPEN EXTRA FILES-'):
            event, values = window.read()
            open = not open
            window['-OPEN EXTRA FILES-'].update(
                    SYMBOL_DOWN if open else SYMBOL_UP)
            window['EXTRA FILES'].update(visible=open)

    window.close()

    if closed is False:
        print('GUI not closed correctly')
        os.system('pause')
        raise SystemExit

    return values


def custom_energies():

    sg.theme('Topanga')

    layout = [[sg.Text('Please enter delivered energies in the '
                       'following format from highest energy to '
                       'lowest - 240, 230, etc. Please note this will '
                       'not write to the database')],
              [sg.Text('Energies:', size=(12, 1)),
               sg.Input(key='ENERGIES', size=(100, 1))],
              [sg.Button('OK', size=(12, 1)), sg.Button('Exit', size=(12, 1))]]

    window = sg.Window('Custom Energy Input', layout)
    event, values = window.read()
    while True:  # Event Loop
        if event == sg.WIN_CLOSED or event == 'Exit':
            event, values = window.read()
            print(values)
            closed = False
            break
        if event == 'OK':
            event, values = window.read()
            closed = True
            break

    if closed is False:
        print('GUI not closed correctly')
        window.close()
        os.system('pause')
        raise SystemExit

    energies = values['ENERGIES']
    energies = [float(x) for x in energies.split(', ')]
    for x in energies:
        if x > 245 or x < 70:
            print('Energy ' + str(x)
                  + ' is out of the allowed range (70-245MeV)')
            window.close()
            os.system('pause')
            raise SystemExit

    return energies


def same_curve(i, curve_list):

    sg.theme('Topanga')

    msg = ('The curve at position ' + str(i) + ' and ' + str(i+1)
           + ' appear to the the same, \nwith a fitted energy of '
           + str(round(curve_list[i].E0_fit, 2))
           + ' and ' + str(round(curve_list[i+1].E0_fit, 2))
           + ' respectively. \nAre these true duplicates?')

    layout = [[sg.Text(msg)],
              [sg.Button('Yes', size=(12, 1)), sg.Button('No', size=(12, 1))]]

    window = sg.Window('Same Curve Check', layout, element_justification='c')
    event, values = window.read()
    while True:
        if event == sg.WIN_CLOSED:
            print('GUI not closed correctly')
            window.close()
            os.system('pause')
            raise SystemExit
        if event == 'Yes':
            choice = True
            break
        if event == 'No':
            choice = False
            break
    window.close()

    return choice


def time_diff():

    sg.theme('Topanga')
    msg = ('Time difference between files is >1 hour.'
           '\nDo you want to take the ADate from the first file '
           'or start again?')

    layout = [[sg.Text(msg)],
              [sg.Button('Combine ADates'),
               sg.Button('Start Again')]]

    window = sg.Window('ADate Difference', layout, element_justification='c')
    event, values = window.read()

    while True:
        if event == sg.WIN_CLOSED:
            print('GUI not closed correctly')
            window.close()
            os.system('pause')
            raise SystemExit
        if event == 'Combine ADates':
            event, values = window.read()
            choice = True
            break
        if event == 'Start Again':
            choice = False
            break

    window.close()

    return choice


def comments(UserInput):

    sg.theme('Topanga')

    msg1 = 'PLEASE REVIEW SUMMARY REPORT BEFORE ENTERING DATA INTO DATABASE!'
    msg2 = 'Report saved here: ' + str(UserInput.dirname)

    layout = [[sg.Text(msg1)],
              [sg.Text(msg2)],
              [sg.Text('_'*100)],
              [sg.Text('')],
              [sg.Text('Comments'), sg.Input(
                  '', key='COMMENTS', size=(100, 1))],
              [sg.Text('')],
              [sg.Button('Save results to database'),
               sg.Button('Do NOT save results to database')]]

    window = sg.Window('Comments', layout, element_justification='c')
    event, values = window.read()

    while True:
        if event == sg.WIN_CLOSED:
            print('GUI not closed correctly')
            window.close()
            os.system('pause')
            raise SystemExit
        if event == 'Save results to database':
            event, values = window.read()
            choice = True
            break
        if event == 'Do NOT save results to database':
            event, values = window.read()
            choice = False
            break

    window.close()
    comments = values['COMMENTS']
    if comments == '':
        comments = None

    return choice, comments


def map_drive_credentials():

    sg.theme('Topanga')

    msg1 = 'You\'re not logged in on a UCLH account. Please provide UCLH account details here.'
    msg2 = '(Note this will disconnect any drive mapped to A: and replace with the assets database location)'

    layout = [[sg.Text(msg1)],
              [sg.Text(msg2)],
              [sg.Text('UserName: \tUCLH\\', size=(19, 1)),
               sg.InputText('', key='USER_NAME')],
              [sg.Text('Password', size=(19, 1)),
               sg.InputText('', key='PASSWORD', password_char='*')],
              [sg.Button('Continue'), sg.Button('Exit')]]
    window = sg.Window('Map Network Drive', layout)

    event, values = window.read()

    closed = True
    while True:  # Event Loop
        if event == sg.WIN_CLOSED or event == 'Exit':
            event, values = window.read()
            closed = False
            break
        if event == 'Continue':
            event, values = window.read()
            break

    window.close()

    return values, closed


if __name__ == '__main__':
    map_drive_credentials()
