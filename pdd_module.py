import numpy as np
import datetime
import os
import easygui as eg

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


def readgiraffe(filename, normalise=True):
    '''
    Reads a csv file as output by the IBA giraffe MLIC
    will normalise data to dmax by default
    returns the data in x y format along with datetime of acquisition
    '''
    if filename[-3:] != 'csv':
        eg.msgbox(f'{filename} is not a csv file')
        return None, None

    with open(filename, 'r') as file:
        read_file = [line.rstrip().lstrip() for line in file]

    depth_index = [read_file.index(x) for x in read_file
                   if x.startswith('Curve depth')][0]
    depth = read_file[1+depth_index].split(';')
    dose_index = [read_file.index(x) for x in read_file
                  if x.startswith('Curve gains')][0]
    dose = read_file[1+dose_index].split(';')
    # Remove blank strings
    depth = [i for i in depth if i]
    dose = [i for i in dose if i]
    data = np.asarray([depth, dose]).astype(float)

    if normalise:
        maxy = max(data[1])
        data[1] = 100*data[1]/maxy

    date = read_file[1][6:25]

    # Read the date as formatted in csv file
    date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
    # Write date as string in more convenient format
    date = date.strftime('%d/%m/%Y %H:%M:%S')

    return data, date


def readmcc(filename, normalise=True):
    '''
    Reads an mcc file as output by the PTW water tank
    will normalise data to dmax by default
    returns the data in x y format, datetime, energy and gantry angle
    '''
    if filename[-3:] != 'mcc':
        eg.msgbox('Not an mcc file')
        return None, None, None, None

    with open(filename, 'r') as file:
        read_file = [line.rstrip().lstrip() for line in file]

    begin_data = 1 + read_file.index('BEGIN_DATA')
    end_data = read_file.index('END_DATA')

    energy_index = [i for i, elem in enumerate(read_file) if 'ENERGY' in elem]
    energy = float(read_file[energy_index[0]][7:])

    date_index = [i for i, elem in enumerate(read_file) if 'MEAS_DATE' in elem]
    date = read_file[date_index[0]][10:]
    date = datetime.datetime.strptime(date, '%d-%b-%Y %H:%M:%S')
    date = date.strftime('%d/%m/%Y %H:%M:%S')

    angle_index = [i for i, elem in enumerate(read_file) if 'GANTRY=' in elem]
    gantry_angle = read_file[angle_index[0]][7:]

    data = []
    for i in range(begin_data, end_data, 1):
        data.append(read_file[i].split())

    # data currently structured like this: data[:][0] = x, data[:][1] = y data
    data = np.asarray(data)
    # Transpose means data[0] = x data, data[1] = y data
    data = np.transpose((data.astype(float)))
    if normalise:
        maxy = max(data[1])
        data[1] = 100*data[1]/maxy
    return data, energy, date, gantry_angle


def directory_to_dictionary(dir):
    '''
    Takes a directory containing pdd files (mcc or csv) and will return a
    dictionary filled with the depth dose data. The dictionary contains
    keys that equate to the energy taken from the file name
    '''
    ref_data = {}
    for filename in os.listdir(dir):
        path = os.path.join(dir, filename)
        file = os.path.basename(filename)  # Get filename without its directory
        try:
            name = float(os.path.splitext(file)[0])
        except ValueError:
            eg.msgbox(f"File {os.path.splitext(file)[0]} incorrectly named\n" +
                      "Please rename with the relevant energy used\n" +
                      "Code will terminate",
                      title="Reference Data Error")
            raise SystemExit
        if file[-3:] == 'mcc':
            ref_data[name], energy, date, gantry_angle = readmcc(path)
            if not name == energy:
                eg.msgbox(f"File {file}: Energy doesn't match filename" +
                          "Code will terminate",
                          title="Reference Data Error")
                raise SystemExit
        if file[-3:] == 'csv':
            ref_data[name], date = readgiraffe(os.path.join(dir, filename))
    return ref_data


def ProximalDepthSeeker(dose, data):
    index = np.argmax((data[1]) > dose)
    y0 = (data[1][index - 1])
    y1 = (data[1][index])
    x0 = (data[0][index - 1])
    x1 = (data[0][index])
    slope = ((y1-y0) / (x1-x0))
    intercept = y0 - (slope*x0)
    proximal = (dose-intercept) / slope
    return proximal


def DistalDepthSeeker(dose, data):
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
    def __init__(self, data, energy, plateau_depth=25):
        if energy < 70:  # Only uses NIST values if within the hardcoded range
            NISTRange = "Out Of Range"
        elif energy > 250:
            NISTRange = "Out Of Range"
        else:
            NISTRange = np.interp(energy, NIST[:, 0], NIST[:, 1])
        self.NISTRange = NISTRange
        self.Prox80 = ProximalDepthSeeker(80, data)
        self.Prox90 = ProximalDepthSeeker(90, data)
        self.Dist90 = DistalDepthSeeker(90, data)
        self.Dist80 = DistalDepthSeeker(80, data)
        if NISTRange == "Out Of Range":
            self.NISTDiff = "N/A"
        else:
            self.NISTDiff = self.Dist80 - NISTRange
        self.Dist20 = DistalDepthSeeker(20, data)
        self.Dist10 = DistalDepthSeeker(10, data)
        self.PTPR = 100/np.interp(plateau_depth, data[0], data[1])
        self.FallOff = self.Dist20 - self.Dist80
        self.PeakWidth = self.Dist80 - self.Prox80
        self.HaloRat = np.interp(ProximalDepthSeeker(80, data)
                                 - (DistalDepthSeeker(80, data)
                                    - ProximalDepthSeeker(80, data)
                                    ),
                                 data[0], data[1]
                                 )


def two_pdds(test_data, ref_data, setgamma, crit):

    deepest = ref_data[0][len(ref_data[0])-1]
    _datax2i = np.linspace(0, deepest, (deepest/0.1)+1)
    datax2i = np.concatenate((ref_data[0], _datax2i))
    datax2i = sorted(datax2i)
    datay2i = np.interp(datax2i, ref_data[0], ref_data[1])
    datax2i = np.asarray(datax2i)
    if setgamma == 'Relative':
        gammas = []
        for x in range(0, len(test_data[0])):
            gammas.append(min(np.sqrt(((((100*(test_data[1][x]-datay2i[:]))
                                       / datay2i[:])/crit[1])**2)
                                      + (((test_data[0][x]-datax2i[:])
                                         / crit[0])**2))))

    if setgamma == 'Absolute':
        gammas = []
        for x in range(0, len(test_data[0])):
            gammas.append(min(np.sqrt((((test_data[1][x]-datay2i[:])
                                       / crit[1])**2)
                                      + (((test_data[0][x] - datax2i[:])
                                         / crit[0])**2))))

    return (gammas)
