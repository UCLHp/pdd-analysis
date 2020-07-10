import numpy as np
import datetime
import os
import easygui as eg

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
            # Find location of depth and dose data and seperate values by ;
            depth_index = self.full_file.index('Curve depth: [mm]')
            dose_index = self.full_file.index('Curve gains: [counts]')
            depth = self.full_file[1+depth_index].split(';')
            dose = self.full_file[1+dose_index].split(';')

            # Hopefully this numerical location is consistent
            date = self.full_file[1][6:25]
            # Convert to datetime object based on format used in file
            date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')

            self.data = np.asarray([depth, dose]).astype(float)
            self.date = date.strftime('%d/%m/%Y %H:%M:%S')

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

        # File types other than csv or mcc not currently supported
        else:
            print(f'File not recognised for {filestring}\n'
                  'Depth dose data not written to object')
        # If norm=True data will be normalised to Dmax
        if norm:
            normalise(self.data)


def directory_to_dictionary(dir):
    '''
    Takes a directory containing pdd files (mcc or csv) and will return a
    dictionary filled with the depth dose data. The dictionary contains
    keys that equate to the energy taken from the file name
    '''
    ref_data = {}
    for file in os.listdir(dir):
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
    def __init__(self, data, energy, plateau_depth=25):
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
    fine_ref_x = np.linspace(0, deepest, (deepest/0.1)+1)
    fine_ref_x = np.concatenate((ref_data[0], fine_ref_x))
    fine_ref_x = sorted(fine_ref_x)
    fine_ref_y = np.interp(fine_ref_x, ref_data[0], ref_data[1])
    # create fine resolution, interpolated dataset
    fine_ref = np.asarray([fine_ref_x, fine_ref_y])

    # For each test data point, calculate the gamma index compared to every
    # point in the interpolated reference data and select the minimum

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
