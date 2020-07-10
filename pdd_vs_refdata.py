import numpy as np
from pdd_module import *
import os
import easygui as eg
import xlsxwriter
import test.test_version


def main():

    test.test_version.check_version()

    # Hard coded location of rerference data
    ref_dir = ('\\\\krypton\\rtp-share$\\protons\\Work in Progress\\Callum\\'
               'Coding\\PDD_Reference_mcc_Files')

    ref_data = directory_to_dictionary(ref_dir)

    test_dir = eg.diropenbox(title='Please Select Test Data')

    if not test_dir:
        raise SystemExit

    test_data = directory_to_dictionary(test_dir)

    # User inputs offset in terms of WET (due to tank wall thickness etc.)
    offset = eg.enterbox("Enter WET Offset (mm)", "WET Offset", ('0'))

    try:
        offset = float(offset)
    except (ValueError, TypeError) as e:
        eg.msgbox("Please re-run with an appropriate value for the WET offset",
                  title="WET Value Error")
        raise SystemExit

    setgamma = eg.buttonbox(msg="Absolute or Relative Gamma Analysis?",
                            title='Define Gamma Analysis',
                            choices=('Relative', 'Absolute'),
                            cancel_choice='Relative')

    if not setgamma:
        eg.msgbox("Please re-run the program and select Relative or Absolute",
                  title="No Gamma Type Selected")
        raise SystemExit

    crit = (eg.multenterbox("enter gamma criteria",
                            "gamma criteria",
                            ('mm', '%'),
                            ('3', '3')
                            )
            )

    try:
        for x in crit:
            float(x)
    except (ValueError, TypeError) as e:
        eg.msgbox('Please re-run the program and enter appropriate '
                  'Gamma Criteria',
                  title="Gamma Criteria Error")
        raise SystemExit

    crit = np.asarray(crit).astype(float)

    ref_data_properties = {}
    for key in ref_data:
        ref_data_properties[key] = PeakProperties(ref_data[key].data, key)

    save_dir = eg.diropenbox(title='Please Select Save Location')

    if not save_dir:
        eg.msgbox("Please re-run the program and select a save location",
                  title="No Save Location Selected")
        raise SystemExit

    workbook = xlsxwriter.Workbook(os.path.join(save_dir, 'PDD_results.xlsx'))

    test_data_properties = {}
    gammas = {}
    for key in sorted(test_data.keys()):
        if key in ref_data.keys():
            test_data[key].data[0] = test_data[key].data[0] + offset

            # Option to add noise to data for test purposes, uncomment below:
            noise = np.random.normal(0, 1, len(test_data[key].data[1]))
            test_data[key].data[1] = test_data[key].data[1] + noise

            test_data_properties[key] = PeakProperties(test_data[key].data, key)
            gammas[key] = pdd_gamma(test_data[key].data, ref_data[key].data, setgamma, crit)

            passcrit = 100.00*sum(x < 1 for x in gammas[key]) / ((len(gammas[key]) - sum(np.isnan(x) for x in gammas[key])))

            worksheet = workbook.add_worksheet(str(int(key)))
            worksheet.write('A1', 'Test Data Depth (mm)')
            worksheet.write_column('A2', test_data[key].data[0])
            worksheet.write('B1', 'Test Data Dose (%)')
            worksheet.write_column('B2', test_data[key].data[1])
            worksheet.write('C1', 'Reference Data Depth (mm)')
            worksheet.write_column('C2', ref_data[key].data[0])
            worksheet.write('D1', 'Reference Data Dose (%)')
            worksheet.write_column('D2', ref_data[key].data[1])
            worksheet.write('E1', 'Gamma Values')
            worksheet.write_column('E2', gammas[key])
            worksheet.write('G1', 'Property')
            worksheet.write_column('G2',
                                   list(test_data_properties[key].__dict__.keys()))
            worksheet.write('H1', 'Test Data')
            worksheet.write_column('H2',
                                   list(test_data_properties[key].__dict__.values()))
            worksheet.write('I1', 'Reference Data')
            worksheet.write_column('I2',
                                   list(ref_data_properties[key].__dict__.values()))
            worksheet.write('J1', 'Difference')
            for i in range(2, 14):
                worksheet.write(f'J{i}', f'=H{i}-I{i}')

            worksheet.set_column('A:A', 19.86)
            worksheet.set_column('B:B', 17.00)
            worksheet.set_column('C:C', 25.57)
            worksheet.set_column('D:D', 22.57)
            worksheet.set_column('E:E', 13.71)
            worksheet.set_column('G:G', 10.00)
            worksheet.set_column('H:H', 12.00)
            worksheet.set_column('I:I', 14.00)
            worksheet.set_column('J:J', 11.29)

            chart = workbook.add_chart({'type': 'scatter'})
            chart.add_series({
                'name': [str(int(key)), 0, 1],
                'categories': [str(int(key)), 1, 0, 1+len(test_data[key].data[0]), 0],
                'values': "='"+str(int(key))+"'!$B$2:$B$"+str(1+len(test_data[key].data[1])),
                'y2_axis': 0,
                'line': {'color': 'red', 'width': 1, },
                'marker': {'type': 'none'},
            })
            chart.add_series({
                'name': [str(int(key)), 0, 3],
                'categories': [str(int(key)), 1, 2, 1+len(ref_data[key].data[0]), 2],
                'values': "='"+str(int(key))+"'!$D$2:$D$"+str(1+len(ref_data[key].data[1])),
                'y2_axis': 0,
                'line': {'color': 'blue', 'width': 1, },
                'marker': {'type': 'none'},
            })
            chart.set_y_axis({'min': 0})
            chart.add_series({
                'name': [str(int(key)), 0, 4],
                'categories': [str(int(key)), 1, 0, 1 + len(test_data[key].data[0]), 0],
                'values': "='"+str(int(key))+"'!$E$2:$E$"+str(1+len(gammas[key])),
                'y2_axis': 1,
                'marker': {'type': 'triangle', 'size': 4},
            })
            chart.set_size({'width': 900, 'height': 650})
            chart.set_title({'name': "Gamma Pass Rate: %1.1f%%" % passcrit})

            worksheet.insert_chart('G15', chart)
            print(str(key) + ' Done')

    workbook.close()


if __name__ == '__main__':
    main()
