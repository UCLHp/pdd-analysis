import numpy as np
import datetime
import os
import easygui as eg
import pandas as pd
import glob
import warnings
from pydicom import *

import bortfeld_fit as bf

# NIST reference data for the Distal 80% for energies between 70MeV and 250MeV
# https://physics.nist.gov/cgi-bin/Star/ap_table.pl
NIST = np.asarray([(70, 40.75), (75, 46.11), (80, 51.76), (85, 57.69),
                   (90, 63.89), (95, 70.35), (100, 77.07), (105, 84.05),
                   (110, 91.28), (115, 98.75), (120, 106.50), (125, 114.40),
                   (130, 122.60), (135, 131.00), (140, 139.60), (145, 148.50),
                   (150, 157.60), (155, 166.80), (160, 176.30), (165, 186.00),
                   (170, 195.90), (175, 206.00), (180, 216.30), (185, 226.70),
                   (190, 237.40), (195, 248.30), (200, 259.30), (205, 270.50),
                   (210, 281.90), (215, 293.40), (220, 305.20), (225, 317.10),
                   (230, 329.10), (235, 341.30), (240, 353.70), (245, 366.30),
                   (250, 379.00)
                   ]
                  )


def normalise(data, at_depth=None):
    '''
    Function to normalise data to Dmax or at a user defined depth
    '''
    if at_depth:
        norm_value = np.interp(at_depth, data[0], data[1])
        data[1] = data[1]/norm_value
    else:
        data[1] = 100*data[1]/max(data[1])


class DepthDoseFile:
    '''
    Class to create a depth dose object that contains the full depth dose data
    as well as the properties provided in files.

    File must be either csv or mcc relating to MLIC or tank data respectively.

    If MLIC csv will output in format
        self.data = [[depth, dose1], [depth, dose2]]
    If tank mcc will output in format
        self.data = [depth, dose]
    note - in both cases "[depth, dose]" is a numpy array)
    '''
    def __init__(self, filestring, norm=True):
        with open(filestring, 'r') as reader:
            self.full_file = [line.strip() for line in reader]
        # File type represented by the file extension
        self.file_type = os.path.splitext(filestring)[1]
        # All attributes listed here as None to be overwritten depending on the
        # file type, csv filees don't have gantry angle or energy data,
        # mcc files don't have number of curves
        self.data = None
        self.date = None
        self.energy = None
        self.gantry_angle = None
        self.no_of_curves = None

        # Giraffe MLIC produces csv files containing pdd data in a string
        # format seperated by ;
        if filestring.endswith('csv'):
            # Find location of depth and seperate values by ;
            depth_index = self.full_file.index('Curve depth: [mm]')
            depth = self.full_file[1+depth_index].split(';')
            # Find number of curves
            no_of_curves = [x for x in self.full_file if x.startswith('Curves:')][0]
            no_of_curves = int(no_of_curves.split(': ')[1])
            # Find location of dose and loop, seperating values by ;
            dose_index = self.full_file.index('Curve gains: [counts]')
            data_full = []
            for curve_index in range(0, no_of_curves):
                dose_one_curve = self.full_file[1+dose_index+curve_index].split(';')
                data_full.append(np.asarray([depth, dose_one_curve]).astype(float))
            # Find date and convert to datetime object based on format in csv
            date = [x for x in self.full_file if x.startswith('Date:')][0]
            date = date[6:25]
            date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
            # Add to class
            self.data = data_full
            self.date = date.strftime('%d/%m/%Y %H:%M:%S')
            self.no_of_curves = no_of_curves

        # The PTW tank produces mcc files containing pdd data
        elif filestring.endswith('mcc'):
            # Find indices for required data in file
            energy_index = [i for i, elem in enumerate(self.full_file)
                            if 'ENERGY' in elem]
            date_index = [i for i, elem in enumerate(self.full_file)
                          if 'MEAS_DATE' in elem]
            angle_index = [i for i, elem in enumerate(self.full_file)
                           if 'GANTRY=' in elem]
            begin_data = 1 + self.full_file.index('BEGIN_DATA')
            end_data = self.full_file.index('END_DATA')

            # Read date as string, then datetime object based on formatting
            date = self.full_file[date_index[0]][10:]
            date = datetime.datetime.strptime(date, '%d-%b-%Y %H:%M:%S')

            self.energy = float(self.full_file[energy_index[0]][7:])
            self.date = date.strftime('%d/%m/%Y %H:%M:%S')
            self.gantry_angle = self.full_file[angle_index[0]][7:]

            data = [self.full_file[i].split() for i in
                    range(begin_data, end_data)
                    ]
            # data currently structured like this:
            # data[:][0] = x, data[:][1] = y data
            data = np.asarray(data)
            # Transpose means data[0] = x data, data[1] = y data
            self.data = np.transpose((data.astype(float)))

        # The PTW tank produces mcc files containing pdd data
        elif filestring.endswith('asc'):
            # Find indices for required data in file
            energy_index = [i for i, elem in enumerate(self.full_file)
                            if 'ENERGY' in elem]
            date_index = [i for i, elem in enumerate(self.full_file)
                          if 'DATE' in elem]
            start_index = [i+1 for i, elem in enumerate(self.full_file)
                          if '%NET 0.0' in elem]
            end_index = [i for i, elem in enumerate(self.full_file)
                          if '$ENOM' in elem]
            no_of_curves = len(start_index)
            
            
            # Find location of dose and loop, seperating values by ;
            data_full = []
            energy = []
            for curve_index in range(0, no_of_curves):
                data = [self.full_file[i].split()[3:-1] for i in range(start_index[curve_index], end_index[curve_index])]
                data = np.asarray(data)
                data = np.transpose((data.astype(float)))
                data_full.append(data)
                # Read energy
                energy.append(float(self.full_file[energy_index[curve_index]][8:]))
            
            # Read date as string, then datetime object based on formatting
            date = self.full_file[date_index[0]][6:]
            date = datetime.datetime.strptime(date, '%Y-%m-%d')
            

            # Add to class
            self.data = data_full
            self.energy = energy
            self.date = date
            self.no_of_curves = no_of_curves
            self.norm = norm

        # File types other than csv or mcc not currently supported
        else:
            print(f'File not recognised for {filestring}\n'
                  'Depth dose data not written to object')
        # If norm=True data will be normalised to Dmax
        if norm:
            if filestring.endswith(('csv','asc')):
                for data in self.data:
                    normalise(data)
            else:
                normalise(self.data)


class DoseCube:
    '''
    Class to create a depth dose object that contains the full depth dose data.
    '''
    def __init__(self, dicomRoot, norm=True, msg=True):
        
        # RT Dose files
        dicomRoot = os.path.normpath(dicomRoot)
        planFile = glob.glob(os.path.join(dicomRoot,"RN*.dcm"))
        if len(planFile) !=1:
            eg.msgbox("Missing or incorrect number of plan files. Code will terminate",
                      title="DICOM Plan File Error")
            raise SystemExit
        else:
            planFile = planFile[0]
            
        doseFiles = glob.glob(os.path.join(dicomRoot,"RD*.dcm"))
        num_files = len(doseFiles)
        
        # Plan data
        if msg:
            print("Processing plan file: "+planFile)
            
        pfile = dcmread(planFile)
        plan_date = pfile.RTPlanDate
        plan_beam_name = []
        plan_beam_number = []
        plan_energy = []
        plan_gantry_angle = []
        for beam in pfile.IonBeamSequence:
            plan_beam_name.append(beam.BeamName)
            plan_beam_number.append(beam.BeamNumber)
            control_points = beam.IonControlPointSequence[0]
            plan_energy.append(int(control_points.NominalBeamEnergy))
            plan_gantry_angle.append(int(control_points.GantryAngle))
            
        if len(plan_beam_number) != num_files:
            warnings.warn("Incorrect number of dose files. Check output.")
            
        # Loop through RT dose files
        data = []
        beam_name = []
        energy = []
        gantry_angle = []
        dose_beam_number = []
        i=1
        for f in doseFiles:
            if msg:
                print("Processing dose file "+str(i)+" of "+str(num_files)+": "+f)
                
            dfile = dcmread(f)
            dvol = dfile.pixel_array # record dose
            # Preallocate data
            dose1D = np.zeros((2,dvol.shape[2]))
            # Geometry
            cube_vertex = dfile.ImagePositionPatient
            pixel_spacing = dfile.PixelSpacing
            depths = np.arange(0, dose1D.shape[1]*pixel_spacing[0], pixel_spacing[0])                            
            # create depth-dose profile
            dose2D = np.sum(dvol,0)
            dose1D[0,:] = depths
            dose1D[1,:] = np.sum(dose2D,0)
            data.append(dose1D)
            # Beam parameters
            beam_seq = dfile.ReferencedRTPlanSequence[0].ReferencedFractionGroupSequence[0].ReferencedBeamSequence[0]
            beam_number =beam_seq.ReferencedBeamNumber
            beam_index = plan_beam_number.index(beam_number)
            beam_name.append(plan_beam_name[beam_index])
            energy.append(plan_energy[beam_index])
            gantry_angle.append(plan_gantry_angle[beam_index])
            dose_beam_number.append(beam_number)
            # counter 
            i += 1
        
        # If norm=True data will be normalised to Dmax
        if norm:
            for d in data:
                normalise(d)
        
        self.rt_plan_file = planFile
        self.rt_dose_files = doseFiles
        self.date = plan_date
        self.no_of_curves = num_files
        self.data = data
        self.energy = energy
        self.gantry_angle = gantry_angle
        self.dose_beam_number = dose_beam_number
        self.beam_name = beam_name
    
        
def directory_to_dictionary(dir):
    '''
    Takes a directory containing pdd files (mcc or csv) and will return a
    dictionary filled with the depth dose data. The dictionary contains
    keys that equate to the energy taken from the file name
    '''
    ref_data = {}
    for file in [_ for _ in os.listdir(dir) if _.endswith('.mcc')]:
        path = os.path.join(dir, file)
        try:
            name = float(os.path.splitext(file)[0])
        except ValueError:
            eg.msgbox(f"File {os.path.splitext(file)[0]} incorrectly named\n"
                      + "Please rename with the relevant energy used\n"
                      + "Code will terminate",
                      title="Reference Data Error")
            raise SystemExit

        ref_data[name] = DepthDoseFile(path)

        # For mcc files, check that the energy written to the file matches the
        # user defined filename
        if file[-3:] == 'mcc' and name != ref_data[name].energy:
            eg.msgbox(f"File {file}: Energy doesn't match filename" +
                      "Code will terminate",
                      title="Reference Data Error")
            raise SystemExit

    return ref_data


def prox_depth_seeker(dose, data):
    '''
    Function that returns the depth at which the user defined dose is exceeded.
    The value returned will be on the shallower side of the bragg peak
    '''
    index = np.argmax((data[1]) > dose)
    y0 = (data[1][index - 1])
    y1 = (data[1][index])
    x0 = (data[0][index - 1])
    x1 = (data[0][index])
    slope = ((y1-y0) / (x1-x0))
    intercept = y0 - (slope*x0)
    proximal = (dose-intercept) / slope
    return proximal


def dist_depth_seeker(dose, data):
    '''
    Function that returns the depth at which the user defined dose is exceeded.
    The value returned will be on the deeper side of the bragg peak
    '''
    index = np.argmax((np.asarray(list(reversed(data[1])))) > dose)
    y0 = (data[1][len(data[1])-index-1])
    y1 = (data[1][len(data[1])-index])
    x0 = (data[0][len(data[0])-index-1])
    x1 = (data[0][len(data[0])-index])
    slope = ((y1-y0)/(x1-x0))
    intercept = y0-(slope*x0)
    distal = (dose-intercept)/slope
    return distal


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
            data[0] = data[0]/10 # Convert depths to cm
            data, scaler, fit_report, E0_best = bf.bortfeld_fit(data)
            data[0] = 10*data[0] # Convert depths back to mm
            self.bortfeld_data = data
            self.bortfeld_scaler = scaler
            self.fit_report = fit_report
            self.E0_fit = E0_best

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


def pdd_gamma(test_data, ref_data, setgamma, crit):
    '''
    Function to return the gamma values for each point in a set of reference
    data relative to an interpolated set of reference data. setgamma defines
    relative (global) or absolute (local) gamma calculation based on crit: the
    gamma criteria ie. 2mm 2%
    '''
    # Find deepest depth measured in test pdd and only
    deepest = ref_data[0][len(ref_data[0])-1]
    # Need more fine resolution in reference data so new data set created
    # With values linearly interpolated every 0.1mm
    fine_ref_x = np.linspace(0, deepest, int((deepest*10)+1))
    fine_ref_x = np.concatenate((ref_data[0], fine_ref_x))
    fine_ref_x = sorted(fine_ref_x)
    fine_ref_y = np.interp(fine_ref_x, ref_data[0], ref_data[1])
    # create fine resolution, interpolated dataset
    fine_ref = np.asarray([fine_ref_x, fine_ref_y])

    # For each test data point, calculate the gamma index compared to every
    # point in the interpolated reference data and select the minimum
    # https://aapm.onlinelibrary.wiley.com/doi/epdf/10.1118/1.598248

    # Relative is a local gamma analysis
    if setgamma == 'Relative':
        gammas = []
        for x in range(0, len(test_data[0])):
            dose_diff = (test_data[1][x] - fine_ref[1][:]) / fine_ref[1][:]
            dose_div_crit = 100*dose_diff/crit[1]

            depth_diff = test_data[0][x] - fine_ref[0][:]
            depth_div_crit = depth_diff / crit[0]

            gammas.append(min(np.sqrt(dose_div_crit**2 + depth_div_crit**2)))

    # Absolute is a global gamma analysis
    if setgamma == 'Absolute':
        gammas = []
        for x in range(0, len(test_data[0])):
            dose_diff = test_data[1][x] - fine_ref[1][:]
            dose_div_crit = dose_diff / crit[1]

            depth_diff = test_data[0][x] - fine_ref[0][:]
            depth_div_crit = depth_diff / crit[0]

            gammas.append(min(np.sqrt(dose_div_crit**2 + depth_div_crit**2)))

    return (gammas)


def dict_to_df(data_dictionary, ROUNDDATA):
    '''
    Convert a dictionary of pdd data into a pandas dataframe that can easily be
    written to an access database. the dataframe contains the properties of
    the bragg peaks to be tracked over time
    '''
    ref_props = []
    # key should represent the energy of the bragg peak
    for key in sorted(data_dictionary.keys()):
        metrics = PeakProperties(data_dictionary[key].data, key)
        ref_props.append([key, round(metrics.Prox80, ROUNDDATA),
                          round(metrics.Prox90, ROUNDDATA),
                          round(metrics.Dist90, ROUNDDATA),
                          round(metrics.Dist80, ROUNDDATA),
                          round(metrics.Dist20, ROUNDDATA),
                          round(metrics.Dist10, ROUNDDATA),
                          round(metrics.FallOff, ROUNDDATA),
                          round(metrics.HaloRat, ROUNDDATA),
                          round(metrics.PTPR, ROUNDDATA)
                          ]
                         )
    return pd.DataFrame(ref_props,
                        columns=['energy', 'prox 80', 'prox 90',
                                 'dist 90', 'dist 80', 'dist 20',
                                 'dist 10', 'fall off',
                                 'halo ratio', 'ptpr'
                                 ]
                        )


def check_dataframes(DF1, DF2):
    '''
    Compares two dataframes against each other. First the shape is compared to
    ensure all data is there to be compared, then np.allclose is used to flag
    any item by item discrepancies of larger than 0.001 - due to float rounding
    issues
    '''
    if DF1.shape != DF2.shape:
        print(DF1.shape, DF2.shape)
        eg.msgbox(f'Discrepancy between {DF1.name} and {DF2.name}\n'
                  'Data sizes do not match \n'
                  'Code will terminate',
                  'Reference Data Error')
        raise SystemExit

    if not np.allclose(DF1, DF2, atol=0.001):
        eg.msgbox(f'Discrepancy in data between {DF1.name} and {DF2.name}\n'
                  'Code will terminate\n'
                  'Please check the values printed in the terminal',
                  'Reference Data Error')
        print(f'{DF1.name} Values\n')
        print(DF1)
        print(f'{DF2.name} Values\n')
        print(DF2)
        print("Difference \n")
        Difference = DF1 - DF2
        Difference['energy'] = DF1['energy']
        print(Difference)
        input('Press Enter To Close Window')
        raise SystemExit
    # Pass if dataframes are the same
    else:
        pass
    
    
