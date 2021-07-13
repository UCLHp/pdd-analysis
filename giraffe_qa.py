


import os
import datetime

import easygui as eg
import numpy as np

import pdd_module as pm

import matplotlib.pyplot as plt


def main():
    '''
    Reading and analysis of csv files outputted by the Giraffe.

    This programme is capable of assessing both single shot and also movie mode
    outputs. It's also capable of dealing with the duplicated curves that can
    occur in movie mode (but it is not capable of dealing with triplicate
    curves and higher.)

    This programme uses Bortfeld fitting to determine the curve parameters.
    based on the 1997 Paper by Bortfeld

    '''
    # Open file and create pdd object
    filepath = eg.fileopenbox('Select the Giraffe csv file', filetypes='*.csv')
    pdd = pm.DepthDoseFile(filepath)

    # Get list of delivered energies (preset or custom)
    choices = ['210-70MeV (every 10MeV)',
               '245-220MeV (every 10MeV + 245MeV)',
               'Custom']
    selection = eg.choicebox('Delivered energies', 'Energy Selection', choices)
    if not selection:
        print('None selected - code will terminate')
        raise SystemExit
    elif selection == '210-70MeV (every 10MeV)':
        energies = [210, 200, 190, 180, 170, 160, 150,
                    140, 130, 120, 110, 100, 90, 80, 70]
    elif selection == '245-220MeV (every 10MeV + 245MeV)':
        energies = [245, 240, 230, 220]
    elif selection == 'Custom':
        energies = eg.enterbox('Please enter delivered energies in the'
                               'following format from highest energy to the '
                               'lowest - 240, 230, etc. Please note this will '
                               'not write to the database',
                               'Custom Enery Selection',
                               default='240, 230, ...')
        energies = [float(x) for x in energies.split(', ')]
        for x in energies:
            if x > 245 or x < 70:
                print('Energy ' + str(x) + ' is out of range (70-245MeV)')
                raise SystemExit

    # Create an empty curve list searching for any duplicates
    curve_list = []
    # Search for duplicate curves
    if len(energies) > len(pdd.data):
        # Fewer curves than energies so exit
        print('Not enough curves for the number of energies supplied.'
              'Please try again - Code will terminate')
        raise SystemExit
    if len(energies) < len(pdd.data):
        # More curves than energies so search for duplicates
        # (NB: only works for duplicates not triplicates etc.)
        print('More curves detected than supplied energies. '
              'Searching for duplicates')
        for i in range(0, pdd.no_of_curves):
            # Use a dummy energy of 100MeV to run the code.
            props = pm.PeakProperties(pdd.data[i], 100, bortfeld_fit_bool=True)
            curve_list.append(props)
        for i in range(0, len(pdd.data)-1):
            # Check for curves with similar energies
            if curve_list[i].E0_fit - curve_list[i+1].E0_fit < 2:
                 choice = eg.boolbox('The curve at position ' + str(i) + ' and ' + str(i+1) + ' appear to the the same, with a fitted energy of ' + str(round(curve_list[i].E0_fit, 2)) + ' and ' + str(round(curve_list[i+1].E0_fit, 2)) + ' respectively. Are these true duplicates?', choices=['No', 'Yes'])
                 if not choice:
                     # They are the same energy so add together etc.
                     data_join = pdd.data[i]
                     data_join[1] = np.add(pdd.data[i][1], pdd.data[i+1][1])/2
                     pdd.data[i] = data_join
                     pdd.data.pop(i+1)

    # Double check that now there are the right number of curves and exit if not, otherwise make a new curve_list.
    curve_list = []
    if len(energies) == len(pdd.data):
        # Same number of energies as curves so create list of the curve properties
        for i in range (0, len(pdd.data)):
            props = pm.PeakProperties(pdd.data[i], energies[i], bortfeld_fit_bool=True)
            curve_list.append(props)
    else:
        print('After duplicate search number of curves does not match the number of energies supplied. Please try again')
        print('No. of curves: ' + str(len(pdd.data)))
        print('No. of energies: ' + str(len(energies)))
        raise SystemExit

    # Pull out the results and also plot to make sure everything looks good.
    plt.figure(figsize=(12,8))
    for i in range(0, len(pdd.data)):
        curve_list[i].E0_fit
        if abs(curve_list[i].E0_fit - energies[i]) > 1:
            print('WARNING: Significant difference between expected and fitted energies.')
        print(  'Energy = ' + str(energies[i]))
        print(  f'E0 = {curve_list[i].E0_fit}\n'
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
        plt.scatter(pdd.data[i][0], pdd.data[i][1], label=str(energies[i])+" MeV", s=0.5)
        # Starting fit with initial Phi0, R0, sigma, epsilon
        plt.plot(curve_list[i].bortfeld_data[0], curve_list[i].bortfeld_data[1]/curve_list[i].bortfeld_scaler, label=str(round(curve_list[i].E0_fit,2))+" MeV")
    # Format plot
    plt.legend(loc="upper right", fontsize=6)
    plt.xlabel("Depth (mm)", fontsize=18)
    plt.ylabel("Normalised dose", fontsize=18)
    plt.xticks(size=16); plt.yticks(size=16)
    plt.show()


if __name__ == "__main__":
    main()
