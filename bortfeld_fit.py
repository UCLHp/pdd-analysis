'''
Fitting Bragg curves using Bortfeld1997's equation
with Phi0, R0, sigma and epsilon as free parameters.

'''
import numpy as np
from numpy import inf
import matplotlib.pyplot as plt
import math
import datetime
import scipy.special as spec
import easygui as eg
from lmfit import Model
from lmfit import Parameters

import pdd_module as pm


def read_data(filepath):
    """
    Reads in experimental data.
        Will accept 2 file types:
            1) Giraffe Output (csv)
            2) csv file with 2 columns (all data no column headings):
                Column 1 = Depth(mm) and Column 2 = Measured Values

    Returns data = [[depth, dose1], [depth, dose2], etc.]
        (where [depth, dose] is a numpy array)
    """
    with open(filepath, 'r') as reader:
        full_file = [line.strip() for line in reader]

    if full_file[0].startswith('Measurement:'):
        # Get depth data and convert to cm
        depth_index = full_file.index('Curve depth: [mm]')
        depth = full_file[1+depth_index].split(';')
        depth = [float(value)/10 for value in depth]
        # Find number of curves
        no_of_curves = [x for x in full_file if x.startswith('Curves:')][0]
        no_of_curves = int(no_of_curves.split(': ')[1])
        # Find location of dose and loop, seperating values by ;
        dose_index = full_file.index('Curve gains: [counts]')
        data_full = []
        for curve_index in range(0, no_of_curves):
            dose_one_curve = full_file[1+dose_index+curve_index].split(';')
            dose_one_curve = [float(value) for value in dose_one_curve]
            norm_dose = [100*d/max(dose_one_curve) for d in dose_one_curve]
            data_full.append(np.asarray([depth, norm_dose]).astype(float))
    else:
        no_of_curves = 1
        depth = []
        dose = []
        file = open(filepath)
        lines = file.readlines()
        file.close()
        for line in lines:
            depth.append(float(line.strip().split(",")[0]))
            dose.append(float( line.strip().split(",")[1]))
        depth = [float(value)/10 for value in depth]
        max_dose = max(dose)
        norm_dose = [100*d/max_dose for d in dose]
        data_full = [np.asarray([depth, norm_dose]).astype(float)]

    return data_full

def normalised_dose(x, Phi0, R0, sigma, epsilon):
    ''' Dose as Equation 27 (polyenergetic with straggling)
    '''
    y = []
    for x_value in x:
        psi = 1.0*(R0-x_value)/sigma
        num1 = math.exp(-psi*psi/4) * math.pow(sigma, 1.0/p) * spec.gamma(1.0/p)
        denom = math.sqrt(2*math.pi) * rho * p * math.pow(alpha, 1.0/p) *(1 + beta*R0)
        num2 = 1.0/sigma * spec.pbdv(-1.0/p,-psi)[0] + (beta/p + gamma*beta + epsilon/R0)*spec.pbdv((-1.0/p -1),-psi)[0]
        # For points significantly beyond the peak num1*num2 becomes 0.0*inf and
        # so triggers a RuntimeWarning. This returns NaN which can then be turned
        # to zero with no significant loss of accuracy.
        dose = Phi0 * num1 * num2 / denom
        y.append(dose)
    y = np.array(y)
    # Replace NaN and inf with zeros. This is mainly for past the peak.
    y[y == -inf] = 0
    y[y == inf] = 0
    return np.nan_to_num(y)

def only_fit_peak(x, y, R0_init, sigma_init):
    ''' Shorten the data to that within -18*sigma to +8*sigma of the peak
    '''
    prox_pos = R0_init - 15*sigma_init
    prox_index = np.argmin(np.absolute(x - prox_pos))
    dist_pos = R0_init + 8*sigma_init
    dist_index = np.argmin(np.absolute(x - dist_pos))
    y = y[prox_index:dist_index]
    x = x[prox_index:dist_index]
    return x, y

def make_plot(model, x, y, E0_data, params, x_bortfeld_best, y_bortfeld_best, E0_best, params_best):

    plt.figure(figsize=(12,8))
    # Experimental data
    plt.scatter(x, y, label="Measured data "+str(E0_data)+" MeV", s=0.5, c="black")
    # Starting fit with initial Phi0, R0, sigma, epsilon
    x_bortfeld = np.arange(0, int(max(x)+1), 0.001).tolist()
    y_bortfeld = model.eval(params, x=x_bortfeld)
    plt.plot(x_bortfeld, y_bortfeld, label="Bortfeld1997 polyenergetic", linestyle="--")
    # Best fit with optimised Phi0, R0, sigma, epsilon
    lbl = "Best fit: R0="+str(round(params_best['R0'].value,2))
    lbl=lbl+", sigma="+str(round(params_best['sigma'].value,2))
    lbl=lbl+" epsilon="+str(round(params_best['epsilon'].value,2))
    lbl=lbl+" Phi0="+str(round(params_best['Phi0'].value,2))
    lbl=lbl+" E0="+str(round(E0_best,2))
    x_bortfeld_best = np.arange(0, int(max(x)+1), 0.001).tolist()
    y_bortfeld_best = model.eval(params_best, x=x_bortfeld_best)
    x_bortfeld_best, y_bortfeld_best = only_fit_peak(x_bortfeld_best, y_bortfeld_best, params['R0'].value, params['sigma'].value)
    plt.plot(x_bortfeld_best, y_bortfeld_best, label=lbl)
    # Format plot
    plt.legend( loc="upper left", fontsize=16 )
    plt.xlabel("Depth (cm)", fontsize=18)
    plt.ylabel("Normalised dose", fontsize=18)
    plt.xticks(size=16); plt.yticks(size=16)
    plt.show()

    return


def bortfeld_fit(data, plotting=False):
    ''' Fits Bortfeld1997 equation to the input data (focused around the peak)
        and returns a data set constructed by finely sampling the fitted
        Bortfeld curve.

        Input data:
            data = [depth, norm_dose]
            depth = list of depths in cm
            norm_dose = dose normalised to maximum value (set to 100)

        Output data, fit_report:
            data = [depth, norm_dose] (as input)
            fit_report = report of the model fitting as produced by lmfit
    '''

    global p, alpha, beta, gamma, rho

    # PARAMETERS
    p = 1.77
    alpha = 2.2E-3   # Power law: R0=alpha*E0^p, with [E0]=MeV
    beta = 0.012     # Gradient of linear fit for fluence reduction with residual range (cm^-1)
    gamma = 0.6      # Fraction of dose from inelastic nuclear interactions absorbed locally
    rho = 1.0        # Density of material [g/cm^3]

    # Read data
    x = np.array(data[0])
    y = np.array(data[1])

    # Form initial guess for optimizer.
    R0_init = x[np.argmax(y)]
    E0_data = math.pow(R0_init/alpha, 1.0/p)
    sigma_init = math.sqrt(((0.012*math.pow(R0_init,0.935))**2) + ((0.01*E0_data*alpha*p*math.pow(E0_data,p-1))**2))
    epsilon_init = 0.1
    Phi0_init = 0.0192*E0_data + 1.2152 # Derived emperically from some trial fits

    # Cut data to that closer to the peak
    x_peak, y_peak = only_fit_peak(x, y, R0_init, sigma_init)

    # Make the model and create the variable parameters
    model = Model(normalised_dose)
    params=Parameters()
    params.add("Phi0",value=Phi0_init)
    params.add("R0",value=R0_init, min=0)
    params.add("sigma",value=sigma_init, min=0)
    params.add("epsilon", value=epsilon_init, min=0)

    # Fit the model
    result = model.fit(y_peak, params, x=x_peak)
    fit_report = result.fit_report()

    # Get best parameters
    energy = math.pow(result.params['R0'].value/alpha, 1.0/p)
    params_best=Parameters()
    params_best.add("Phi0", value=result.params['Phi0'].value)
    params_best.add("R0", value=result.params['R0'].value, min=0)
    params_best.add("sigma", value=result.params['sigma'].value, min=0)
    params_best.add("epsilon", value=result.params['epsilon'].value, min=0)
    E0_best = math.pow(result.params['R0'].value/alpha, 1.0/p)

    x_bortfeld_best = np.arange(0, int(max(x)+1), 0.001).tolist()
    y_bortfeld_best = model.eval(params_best, x=x_bortfeld_best)
    x_bortfeld_best, y_bortfeld_best = only_fit_peak(x_bortfeld_best, y_bortfeld_best, params['R0'].value, params['sigma'].value)
    scaler = 100/np.amax(y_bortfeld_best)
    y_bortfeld_best = [scaler*value for value in y_bortfeld_best]

    if plotting:
        make_plot(model, x, y, E0_data, params, x_bortfeld_best, y_bortfeld_best, E0_best, params_best)

    data = [x_bortfeld_best, y_bortfeld_best]
    data = np.array(data, copy=True)
    print(E0_best)
    print(fit_report)

    return data, scaler, fit_report, E0_best


if __name__ == "__main__":

    # Read in data
    filepath = eg.fileopenbox('Select the csv file', filetypes='*.csv')
    data_full = read_data(filepath)

    # Perform fit and print basic results
    for data in data_full:
        data, scaler, fit_report, E0_best = bortfeld_fit(data, plotting=True)
        print('Energy = '+str(round(E0_best,2)))
        print('P80 = '+str(pm.prox_depth_seeker(80, data)))
        print('P90 = '+str(pm.prox_depth_seeker(90, data)))
        print('D90 = '+str(pm.dist_depth_seeker(90, data)))
        print('D80 = '+str(pm.dist_depth_seeker(80, data)))
        print('D20 = '+str(pm.dist_depth_seeker(20, data)))
        print('D10 = '+str(pm.dist_depth_seeker(10, data)))
        print()














#
