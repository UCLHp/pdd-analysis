import pdd_module as pm
import easygui as eg

def main():
    '''Code to print peak properties for acquired giraffe csv file'''
    filepath = eg.fileopenbox('Select the Giraffe csv file', filetypes='*.csv')
    pdd = pm.DepthDoseFile(filepath)
    energy = eg.integerbox('Enter Beam Energy (70-245MeV)',
                           'Enter Energy', lowerbound=70, upperbound=245
                           )


    props = pm.PeakProperties(pdd.data, )
    print(f'D80 = {props.Dist80}\n'
          f'D90 = {props.Dist90}\n'
          f'D20 = {props.Dist20}\n'
          f'Fall Off = {props.FallOff}')


if __name__ == "__main__":
    main()










import easygui as eg
import os
import numpy as np
import datetime

from pdd_module import *
import bortfeld_fit as bf


class DepthDoseFile:
    '''
    Class to create a depth dose object that contains the full depth dose data
    as well as the properties provided in files.
    File must be either csv or mcc relating to MLIC or tank data respectively
    '''
    def __init__(self, filestring, norm=True):
        with open(filestring, 'r') as reader:
            self.full_file = [line.strip() for line in reader]
        # File type represented by the file extension
        self.file_type = os.path.splitext(filestring)[1]
        # All attributes listed here as None to be overwritten depending on the
        # file type, csv filees don't have gantry angle or energy data
        self.data = None
        self.date = None
        self.energy = None
        self.gantry_angle = None

        # Giraffe MLIC produces csv files containing pdd data in a string
        # format seperated by ;
        if filestring.endswith('csv'):
            # Find location of depth and seperate values by ;
            depth_index = self.full_file.index('Curve depth: [mm]')
            depth = self.full_file[1+depth_index].split(';')
            depth = [float(value)/10 for value in depth]
            # Find number of curves to loop through
            no_of_curves = [x for x in self.full_file if x.startswith('Curves:')][0]
            self.no_of_curves = int(no_of_curves.split(': ')[1])
            # Find location of depth and loop, seperating values by ;
            dose_index = self.full_file.index('Curve gains: [counts]')
            data_full = []
            for curve_index in range(0, self.no_of_curves):
                dose_one_curve = self.full_file[1+dose_index+curve_index].split(';')
                data_full.append(np.asarray([depth, dose_one_curve]).astype(float))

            # Find the date
            date = [x for x in self.full_file if x.startswith('Date:')][0]
            date = date[6:25]
            # Convert to datetime object based on format used in file
            date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')

            self.data = data_full
            self.date = date.strftime('%d/%m/%Y %H:%M:%S')


class PeakProperties:
    '''
    A PeakProperties object returns the attributes used to define an individual
    Bragg Peak. It requires depth dose data, the energy (for the NIST reference
    data) and where the 'plateau' is defined for a peak to plateau ratio.
    '''
    def __init__(self, data, energy, plateau_depth=25, bortfeld_fit_bool=False):
        # Only uses NIST values if within the hardcoded range
        if energy < 70:
            NISTRange = "Out Of Range"
        elif energy > 250:
            NISTRange = "Out Of Range"
        else:
            NISTRange = np.interp(energy, NIST[:, 0], NIST[:, 1])

        # PDDs must be normalised to get these values - creating a copy allows
        # calculation of the properties withour affecting the input data
        data = np.array(data, copy=True)
        normalise(data)

        if bortfeld_fit_bool:
            data, fit_report, E0_best = bf.bortfeld_fit(data)
            self.fit_report = fit_report
            self.E0_fit = E0_best

        data = np.array(data, copy=True)

        self.NISTRange = NISTRange
        self.Prox80 = prox_depth_seeker(80, data)
        self.Prox90 = prox_depth_seeker(90, data)
        self.Dist90 = dist_depth_seeker(90, data)
        self.Dist80 = dist_depth_seeker(80, data)
        if NISTRange == "Out Of Range":
            self.NISTDiff = "N/A"
        else:
            self.NISTDiff = self.Dist80 - NISTRange
        self.Dist20 = dist_depth_seeker(20, data)
        self.Dist10 = dist_depth_seeker(10, data)
        # Peak to Plateau Ratio (PTPR) is calculated at a user defined depth
        # The default value is set to 25mm deep
        self.PTPR = 100/np.interp(plateau_depth, data[0], data[1])
        self.FallOff = self.Dist20 - self.Dist80
        self.PeakWidth = self.Dist80 - self.Prox80
        # Halo ratio is the dose(%) at a depth one peakwidth shallower than
        # the Prox80
        self.HaloRat = np.interp(prox_depth_seeker(80, data)
                                 - self.PeakWidth, data[0], data[1]
                                 )




# Open file and create pdd object
filepath = eg.fileopenbox('Select the Giraffe csv file', filetypes='*.csv')
pdd = DepthDoseFile(filepath)

# Get list of delivered energies (preset or custom)
choices=['210-70MeV (every 10MeV)','245-220MeV (every 10MeV + 245MeV)','Custom']
selection=eg.choicebox('Delivered energies', 'Energy Selection', choices)
if selection == None:
    print('Please select the delivered energies')
    raise SystemExit
elif selection == '210-70MeV (every 10MeV)':
    energies = [210, 200, 190, 180, 170, 160, 150, 140, 130, 120, 110, 100, 90, 80, 70]
elif selection == '245-220MeV (every 10MeV + 245MeV)':
    energies = [245, 240, 230, 220]
elif selection == 'Custom':
    energies = eg.enterbox('Please enter delivered energies in the following format from highest energy to lowest - 240, 230, etc. Please note this will not write to the database', 'Custom Enery Selection', default='240, 230, ...')
    energies = [float(x) for x in energies.split(', ')]
    for x in energies:
        if x > 245 or x < 70:
            print('Energy ' + str(x) + ' is out of the allowed range (70-245MeV)')
            raise SystemExit



# Create a list of the curves searching for any duplicates
curve_list = []
if len(energies) == pdd.no_of_curves:
    for i in range (0, pdd.no_of_curves):
        props = PeakProperties(pdd.data[i], energies[i], bortfeld_fit_bool=True)
        curve_list.append(props)
elif len(energies) > pdd.no_of_curves:
    print('Not enough curves for the number of energies supplied. Please try again')
    raise SystemExit
else:
    print('There are more curves than supplied energies. Searching for duplicate curves')
    for i in range (0, pdd.no_of_curves):
        # Use a dummy energy of 100MeV to run the code.
        props = PeakProperties(pdd.data[i], 100, bortfeld_fit_bool=True)
        curve_list.append(props)
    for i in range(0, len(pdd.data)-1):
        if curve_list[i].E0_fit - curve_list[i+1].E0_fit < 2:
             choice = eg.boolbox('The curve at position ' + str(i) + ' and ' + str(i+1) + ' appear to the the same, with a fitted energy of ' + str(round(curve_list[i].E0_fit, 2)) + ' and ' + str(round(curve_list[i+1].E0_fit, 2)) + ' respectively. Are these true duplicates?', choices=['No', 'Yes'])
             if not choice:
                 # They are the same energy so add together, overwite in pdd.data and remove the extra
                 data_join = pdd.data[i]
                 data_join[1] = np.add(pdd.data[i][1], pdd.data[i+1][1])
                 pdd.data[i] = data_join
                 pdd.data.pop(i+1)
    # With new list we should have the number of energies matching number of curves. If not raise and exit and try again
    curve_list = []
    if len(energies) == len(pdd.data):
        for i in range (0, len(pdd.data)):
            props = PeakProperties(pdd.data[i], energies[i], bortfeld_fit_bool=True)
            curve_list.append(props)
    else:
        print('After duplicate search number of curves does not match the number of energies supplied. Please try again')
        print('No. of curves: ' + str(len(pdd.data)))
        print('No. of energies: ' + str(len(energies)))
        raise SystemExit

for i in range(0, len(pdd.data)):
    curve_list[i].E0_fit
    print('Energy = ' + str(energies[i]))
    print(  f'E0 = {curve_list[i].E0_fit}\n'
            f'D80 = {curve_list[i].Dist80}\n'
            f'D90 = {curve_list[i].Dist90}\n'
            f'D20 = {curve_list[i].Dist20}\n'
            f'Fall Off = {curve_list[i].FallOff}')
