import numpy as np
from pdd_module import *
import os
import easygui as eg
import xlsxwriter
import test.test_version

def main():

    test.test_version.check_version()

    mcc_dir = eg.diropenbox(title='Please Select mcc directory')
    if not mcc_dir:
        raise SystemExit

    data = directory_to_dictionary(mcc_dir)

    # User inputs offset in terms of WET (due to tank wall thickness etc.)
    offset = eg.enterbox("Enter WET Offset (mm)", "WET Offset", ('0'))
# Battery low
    try:
        offset = float(offset)
    except (ValueError, TypeError) as e:
        eg.msgbox("Please re-run with an appropriate value for the WET offset",
                  title="WET Value Error")
        raise SystemExit

    save_dir = eg.diropenbox(title='Please Select Save Location')
    workbook = xlsxwriter.Workbook(os.path.join(save_dir, 'Ref_results.xlsx'))

    data_properties = {}
    for key in sorted(data.keys()):
        data[key][0] = data[key][0] + offset

        data_properties[key] = PeakProperties(data[key], key)

        worksheet = workbook.add_worksheet(str(int(key)))
        worksheet.write('A1', 'Depth (mm)')
        worksheet.write_column('A2', data[key][0])
        worksheet.write('B1', 'Dose (%)')
        worksheet.write_column('B2', data[key][1])
        worksheet.write('D1', 'Property')
        worksheet.write_column('D2',
                               list(data_properties[key].__dict__.keys()))
        worksheet.write('E1', 'Value')
        worksheet.write_column('E2',
                               list(data_properties[key].__dict__.values()))

        worksheet.set_column('A:A', 11.00)
        worksheet.set_column('B:B', 11.29)
        worksheet.set_column('D:D', 10.00)
        worksheet.set_column('E:E', 12.00)
        worksheet.set_column('G:G', 10.00)

        chart = workbook.add_chart({'type': 'scatter'})
        chart.add_series({
            'name': [str(int(key)), 0, 1],
            'categories': [str(int(key)), 1, 0, 1+len(data[key][0]), 0],
            'values': "='"+str(int(key))+"'!$B$2:$B$"+str(1+len(data[key][1])),
            'y2_axis': 0,
            'line': {'color': 'red', 'width': 1, },
            'marker': {'type': 'none'},
        })
        chart.set_size({'width': 900, 'height': 650})
        chart.set_title({'name': "Measured PDD"})

        worksheet.insert_chart('G2', chart)
        print(str(key) + ' Done')

    workbook.close()


if __name__ == '__main__':
    main()
