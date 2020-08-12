import numpy as np
import pdd_module as pdd
import os
import easygui as eg
import xlsxwriter
import test.test_version


'''
This script has been written to speed up the process of gathering tank data
at commissioning. It asks the user to select a directory containing mcc files.
The mcc filenames should correspond to the delivered energy.
The script will write the results to an excel spreadsheet.
'''


def main():
    # test_version checks there haven't been changes to master branch on github
    test.test_version.check_version()

    mcc_dir = eg.diropenbox(title='Please select mcc directory')
    if not mcc_dir:
        raise SystemExit

    # directory_to_dictionary from the pdd_module reads all files in the
    # directory (mcc or csv) and returns a dictionary with keys equating to the
    # filename (which should be the energy). Each entry is a DepthDoseFile
    # object where you can access any of the data in the original file.
    data = pdd.directory_to_dictionary(mcc_dir)

    # User inputs offset in terms of WET (due to tank wall thickness etc.)
    offset = eg.enterbox("Enter WET Offset (mm)", "WET Offset", ('0'))

    try:
        offset = float(offset)
    except (ValueError, TypeError) as e:
        eg.msgbox("Please re-run with an appropriate value for the WET offset",
                  title="WET Value Error")
        raise SystemExit

    save_dir = eg.diropenbox(title='Please Select Save Location')
    if not save_dir:
        raise SystemExit

    # Create empty excel file to write results to
    workbook = xlsxwriter.Workbook(os.path.join(save_dir, 'Ref_results.xlsx'))

    # Loop through each key (energy) in the dir, get the properties using
    # the PeakProperties class then write them to the excel file

    data_properties = {}
    # sort keys so that the energies appear numerically on the excel sheets
    for key in sorted(data.keys()):
        # Apply WET offset to data
        data[key].data[0] = data[key].data[0] + offset

        data_properties[key] = pdd.PeakProperties(data[key].data, key)

        # normalise function from pdd_module, normalise at calibration depth
        pdd.normalise(data[key].data, at_depth=25)

        worksheet = workbook.add_worksheet(str(int(key)))
        # Write normalised data to first two rows
        worksheet.write('A1', 'Depth (mm)')
        worksheet.write_column('A2', data[key].data[0])
        worksheet.write('B1', 'Dose (%)')
        worksheet.write_column('B2', data[key].data[1])

        # Gap for aesthetics then write property title and values
        worksheet.write('D1', 'Property')
        worksheet.write_column('D2',
                               list(data_properties[key].__dict__.keys()))
        worksheet.write('E1', 'Value')
        worksheet.write_column('E2',
                               list(data_properties[key].__dict__.values()))
        # Set column widths for aesthetics
        worksheet.set_column('A:A', 11.00)
        worksheet.set_column('B:B', 11.29)
        worksheet.set_column('D:D', 10.00)
        worksheet.set_column('E:E', 12.00)
        worksheet.set_column('G:G', 10.00)

        # Create the scatter plot using the previously written data
        chart = workbook.add_chart({'type': 'scatter'})
        chart.add_series({
            'name': [str(int(key)), 0, 1],
            'categories': [str(int(key)), 1, 0, 1+len(data[key].data[0]), 0],
            'values': "='" + str(int(key)) + "'!$B$2:$B$"
                           + str(1+len(data[key].data[1])),
            'y2_axis': 0,
            'line': {'color': 'red', 'width': 1, },
            'marker': {'type': 'none'},
        })
        chart.set_size({'width': 900, 'height': 650})
        chart.set_title({'name': "Measured PDD"})

        worksheet.insert_chart('G2', chart)
        # Track progress in the command line
        print(str(key) + ' Done')

    workbook.close()


if __name__ == '__main__':
    main()
