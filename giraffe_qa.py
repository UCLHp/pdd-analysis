'''
Reading and analysis of csv files outputted by the Giraffe.

This programme is capable of assessing both single shot and also movie mode
outputs. It is also capable of dealing with the duplicated curves that can
occur in movie mode (but it is not capable of dealing with triplicate curves
and higher.)

This programme uses Bortfeld fitting to determine the curve parameters.

'''


import os

import easygui as eg
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import pdd_module as pm


def measured_energies():
    '''
    Get list of delivered energies (preset or custom)
    '''
    choices = ['210-70MeV (every 10MeV)',
               '245-220MeV (every 10MeV + 245MeV)',
               'Custom']
    selection = eg.choicebox('Delivered energies', 'Energy Selection', choices)

    if selection is None:
        print('Please select the delivered energies')
        os.system('pause')
        raise SystemExit

    elif selection == '210-70MeV (every 10MeV)':
        energies = [210, 200, 190, 180, 170, 160,
                    150, 140, 130, 120, 110, 100, 90, 80, 70]

    elif selection == '245-220MeV (every 10MeV + 245MeV)':
        energies = [245, 240, 230, 220]

    elif selection == 'Custom':
        energies = eg.enterbox('Please enter delivered energies in the '
                               'following format from highest energy to '
                               'lowest - 240, 230, etc. Please note this will '
                               'not write to the database',
                               'Custom Enery Selection',
                               default='240, 230, ...')
        energies = [float(x) for x in energies.split(', ')]
        for x in energies:
            if x > 245 or x < 70:
                print('Energy ' + str(x)
                      + ' is out of the allowed range (70-245MeV)')
                os.system('pause')
                raise SystemExit

    return selection, energies


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
                choice = eg.boolbox('The curve at position '
                                    + str(i) + ' and ' + str(i+1)
                                    + ' appear to the the same, with a fitted '
                                      'energy of '
                                    + str(round(curve_list[i].E0_fit, 2))
                                    + ' and '
                                    + str(round(curve_list[i+1].E0_fit, 2))
                                    + ' respectively. Are these true '
                                      'duplicates?',
                                    choices=['No', 'Yes'])
                if not choice:
                    # They are the same energy so add together etc.
                    data_join = pdd.data[i]
                    data_join[1] = np.add(pdd.data[i][1], pdd.data[i+1][1])/2
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


def plot_results(pdd, energies, curve_list):
    # Pull out the results and also plot to make sure everything looks good.
    plt.figure(figsize=(12, 8))
    for i in range(0, len(pdd.data)):
        if abs(curve_list[i].E0_fit - energies[i]) > 1:
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
    plt.xlabel("Depth (mm)", fontsize=18)
    plt.ylabel("Normalised dose", fontsize=18)
    plt.xticks(size=16)
    plt.yticks(size=16)
    plt.show()

    return


def compile_results(pdd, energies, curve_list):
    dict = {'Energy': [],
            'E0': [],
            'P80': [],
            'P90': [],
            'D90': [],
            'D80': [],
            'D20': [],
            'D10': [],
            'Fall Off': [],
            'PTPR': [],
            'Peak Width': [],
            'Halo Ratio': []
            }
    for i in range(0, len(pdd.data)):
        if abs(curve_list[i].E0_fit - energies[i]) > 1:
            print('WARNING: Significant difference between expected and '
                  'fitted energies.')
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

    return dict


def main():

    # Open file and create pdd object
    filepath = eg.fileopenbox('Select the Giraffe csv file', filetypes='*.csv')
    pdd = pm.DepthDoseFile(filepath)

    # Determine what energies were measured
    selection, energies = measured_energies()

    # Check the number of energies matches the number of curves and adjust for
    # duplicates.
    pdd = check_curve_list(pdd, energies)

    # Create a list of the properties of the measured curves
    curve_list = create_curve_list(pdd, energies)

    # Plot the measured and fitted curves.
    plot_results(pdd, energies, curve_list)

    # Compile the results into a dictionary
    dict = compile_results(pdd, energies, curve_list)
    print(dict)

    # # Save the results to QA record
    # path = eg.filesavebox(msg='Create output file', title='Save Output',
    #                       default="output.csv", filetypes=['*.csv'])
    # df = pd.DataFrame.from_dict(dict)
    # df.to_csv(path)

    path = eg.fileopenbox(msg='Locate the results file', title='Results File')



    # Pause before finishing (needed for when run as an executable)
    os.system('pause')


if __name__ == "__main__":
    main()
