from numpy import warnings,argmax,asarray, interp, linspace, concatenate, sqrt, transpose
import datetime

NIST = asarray([(70,40.75),(75,46.11),(80,51.76),(85,57.69),(90,63.89),(95,70.35),(100,77.07),(105,84.05),(110,91.28),(115,98.75),(120,106.50),(125,114.40),(130,122.60),(135,131.00),(140,139.60),(145,148.50),(150,157.60),(155,166.80),(160,176.30),(165,186.00),(170,195.90),(175,206.00),(180,216.30),(185,226.70),(190,237.40),(195,248.30),(200,259.30),(205,270.50),(210,281.90),(215,293.40),(220,305.20),(225,317.10),(230,329.10),(235,341.30),(240,353.70),(245,366.30),(250,379.00)])

def ReadGiraffe(filename):
    file = open(filename,'r')
    FullData=[]
    for line in file:
        FullData.append((line.rstrip().lstrip()))
    XData = FullData[1+([i for i, elem in enumerate(FullData) if 'Curve depth: [mm]' in elem][0])].split(',')
    YData = FullData[1+([i for i, elem in enumerate(FullData) if 'Curve gains: [counts]' in elem][0])].split(',')
    XData = [i for i in XData if i] #Removes empty strings
    YData = [i for i in YData if i] #Removes empty strings

    Data=[XData,YData]
    Data=asarray(Data)

    Data = (Data.astype(float))

    maxy = max(Data[1]) # Find the maximum value in the y data
    Data[1] = 100*Data[1]/maxy # Convert all values to percentages with dmax = 100%

    DATE = FullData[1][6:25]
    DATE = datetime.datetime.strptime(DATE,'%Y-%m-%dT%H:%M:%S').strftime('%d/%m/%Y %H:%M:%S')

    return Data, DATE

def ReadTank(filename):
    file = open(filename,'r')
    FullData=[] # Create empty array to append data
    for line in file:
        FullData.append((line.rstrip().lstrip())) # Appends every line in the file


    BEGIN_DATA = 1+FullData.index('BEGIN_DATA') # Finds beginning line of data
    END_DATA = FullData.index('END_DATA') # Finds last line of data

    ENERGY_Index = [i for i, elem in enumerate(FullData) if 'ENERGY' in elem] # Energy is in written in text on a line
    ENERGY = FullData[ENERGY_Index[0]][7:] # Reads the numerical energy without the label
    ENERGY = float(ENERGY) # Converts the text read value into a float

    DATE_Index = [i for i, elem in enumerate(FullData) if 'MEAS_DATE' in elem] # Date is in written text in a line
    DATE = FullData[DATE_Index[0]][10:] # Reads the numerical date without the label
    DATE = datetime.datetime.strptime(DATE,'%d-%b-%Y %H:%M:%S').strftime('%d/%m/%Y %H:%M:%S') # Converts the text read value into a date in the correct format 'dd/mm/yyyy HH:MM:SS'

    GantryAngle_index = [i for i, elem in enumerate(FullData) if 'GANTRY=' in elem] # Gantry Angle is in written text in a line
    GantryAngle = FullData[GantryAngle_index[0]][7:] # Gantry angle is a label so doesn't require conversion to a float.

    Data=[] # Creates empty array to append numerical data without header
    for i in range(BEGIN_DATA,END_DATA,1): # Loops through each line containing numerical data
        Data.append(FullData[i].split()) # Appends the values split into depth and dose values.

    Data = asarray(Data) # Converts data into a numpy array
    Data = transpose((Data.astype(float))) # Transposes so that columns represent depths and dose respectively
    maxy = max(Data[1]) # Find the maximum value in the y data
    Data[1] = 100*Data[1]/maxy # Convert all values to percentages with dmax = 100%
    return Data, ENERGY, DATE, GantryAngle

def ProximalDepthSeeker(Dose,Data): # same as previous formula but approaching data from the front
        warnings.filterwarnings('ignore') # Prevents the "NaN" error message in the python display
        index = argmax((asarray(Data[1]))>Dose)
        y0 = (Data[1][index-1])
        y1 = (Data[1][index])
        x0 = (Data[0][index-1])
        x1 = (Data[0][index])
        slope = ((y1-y0)/(x1-x0)) # calculate the gradient - note a linear interpolation is performed
        intercept = y0-(slope*x0) # calculate the theoretical intercept
        proximal = (Dose-intercept)/slope # finds x value for given Dose level
        return proximal; #Out put the value for use later

def DistalDepthSeeker(Dose,Data): # Define a formula to find x for a given y in the distal fall off
        warnings.filterwarnings('ignore') # Prevents the "NaN" error message in the python display
        index = argmax((asarray(list(reversed(Data[1]))))>Dose) # Find the first value that exceeds the "Dose" value approaching from greatest x value
        y0 = (Data[1][len(Data[1])-index-1]) # These 4 lines fetch the points either side of the value
        y1 = (Data[1][len(Data[1])-index])
        x0 = (Data[0][len(Data[0])-index-1])
        x1 = (Data[0][len(Data[0])-index])
        slope = ((y1-y0)/(x1-x0)) # calculate the gradient - note a linear interpolation is performed
        intercept = y0-(slope*x0) # calculate the theoretical intercept
        distal = (Dose-intercept)/slope # finds x value for given Dose level
        return distal; # Output the value for later use

class PeakProperties:
    def __init__(self, NISTRange, Prox80, Prox90, Dist90, Dist80, Dist20, Dist10, PTPR, HaloRat):
        self.NISTRange = NISTRange
        self.Prox80 = Prox80
        self.Prox90 = Prox90
        self.Dist90 = Dist90
        self.Dist80 = Dist80
        if NISTRange == "Out Of Range": #Catches if energies are outside the hardcoded NIST data
            self.NISTDiff = "N/A"
        else:
            self.NISTDiff = self.Dist80 - NISTRange
        self.Dist20 = Dist20
        self.Dist10 = Dist10
        self.PTPR = PTPR
        self.FallOff = self.Dist20 - self.Dist80
        self.PeakWidth = self.Dist80 - self.Prox80
        self.HaloRat = HaloRat

def OnePDD(Data, Energy):
    if Energy<70: #Only uses NIST values if within the range hardcoded at the beginning
        NISTRange = "Out Of Range"
    elif Energy>250: #Only uses NIST values if within the range hardcoded at the beginning
        NISTRange = "Out Of Range"
    else:
        NISTRange = interp(Energy,NIST[:,0],NIST[:,1]) #Performs linear interpolation between NIST data points if Energy isn't available
    maxy = max(Data[1]) # Find the maximum value in the y data
    Data[1] = 100*Data[1]/maxy # Convert all values to percentages with dmax = 100%

    Plateaux = interp(25,Data[0],Data[1])
    PTPR = 100/Plateaux # Calcualtes peak to plateau ratio
    HaloRat = interp(ProximalDepthSeeker(80,Data)-(DistalDepthSeeker(80,Data)-ProximalDepthSeeker(80,Data)),Data[0],Data[1])

    Data_Props = PeakProperties(NISTRange, ProximalDepthSeeker(80,Data), ProximalDepthSeeker(90,Data), DistalDepthSeeker(90,Data), DistalDepthSeeker(80,Data), DistalDepthSeeker(20,Data), DistalDepthSeeker(10,Data), PTPR, HaloRat)

    return (Data_Props)


def TwoPDDs(Data1, Data2, Energy, setGamma, crit):

    #Hard Coding the NIST Reference Data

    ##############################
    #Formatting and normalising the data
    ##############################

    if Energy<70: #Only uses NIST values if within the range hardcoded at the beginning
        NISTRange = "Out Of Range"
    elif Energy>250: #Only uses NIST values if within the range hardcoded at the beginning
        NISTRange = "Out Of Range"
    else:
        NISTRange = interp(Energy,NIST[:,0],NIST[:,1]) #Performs linear interpolation between NIST data points if Energy isn't available

    maxy1 = max(Data1[1]) # Find the maximum value in the y data
    Data1[1] = 100*Data1[1]/maxy1 # Convert all values to percentages with dmax = 100%
    maxy2 = max(Data2[1]) #Find maximim value in the y data
    Data2[1] = 100*Data2[1]/maxy2 # Convert all values to percentages with dmax = 100%

    Plateaux_1 = interp(25,Data1[0],Data1[1])
    PTPR_1 = 100/Plateaux_1 # Calcualtes peak to plateau ratio
    Plateaux_2 = interp(25,Data2[0],Data2[1])
    PTPR_2 = 100/Plateaux_2
    HaloRatT = interp(ProximalDepthSeeker(80,Data1)-(DistalDepthSeeker(80,Data1)-ProximalDepthSeeker(80,Data1)),Data1[0],Data1[1])
    HaloRatR = interp(ProximalDepthSeeker(80,Data2)-(DistalDepthSeeker(80,Data2)-ProximalDepthSeeker(80,Data2)),Data2[0],Data2[1])

    #####################
    #Pasting results as a PeakProperties Class as defined above
    #####################


    Data1_Props = PeakProperties(NISTRange, ProximalDepthSeeker(80,Data1), ProximalDepthSeeker(90,Data1), DistalDepthSeeker(90,Data1), DistalDepthSeeker(80,Data1), DistalDepthSeeker(20,Data1), DistalDepthSeeker(10,Data1), PTPR_1, HaloRatT)

    Data2_Props = PeakProperties(NISTRange, ProximalDepthSeeker(80,Data2), ProximalDepthSeeker(90,Data2), DistalDepthSeeker(90,Data2), DistalDepthSeeker(80,Data2), DistalDepthSeeker(20,Data2), DistalDepthSeeker(10,Data2), PTPR_2, HaloRatR)


    _Datax2i = linspace(0,Data2[0][len(Data2[0])-1],(len(Data2[0])-0.9)/0.1) #Creates x data points between 0 and max depth in steps of 0.1mm
    Datax2i = concatenate((Data2[0],_Datax2i)) #appends xvals to non interpolated x points
    Datax2i = sorted(Datax2i) #Sorts all xvalues
    Datay2i = interp(Datax2i,Data2[0],Data2[1]) #Linearly interpolates to get y data at all interpolated x points
    Datax2i = asarray(Datax2i)
    ########################
    #Perform Gamma Analysis
    ########################

    if setGamma == 'Relative':
        gammas = [] #Creates empty array in which to put minimum gamma values for each of the non interpolated x points
        for x in range(0,len(Data1[0])): #Need to cycle through each non interpolated x value and find minimum gamma value
            gammas.append(min(sqrt(((((100*(Data1[1][x]-Datay2i[:]))/Datay2i[:])/crit[1])**2)+(((Data1[0][x]-Datax2i[:])/crit[0])**2)))) #Return the minimum gamma and iteratively put minimum gamma value into gammas array

    if setGamma =='Absolute':
        gammas = []
        for x in range(0,len(Data1[0])):
            gammas.append(min(sqrt((((Data1[1][x]-Datay2i[:])/crit[1])**2)+(((Data1[0][x]-Datax2i[:])/crit[0])**2))))

    return (gammas, Data1_Props, Data2_Props) #Spits out required values to use in code below.
