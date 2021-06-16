import numpy as np
from numpy import inf
import math

import pdd_module as pm
import easygui as eg


def normalised_dose(x, Phi0, R0, sigma, epsilon):
    ''' Dose as Equation 27 (polyenergetic with straggling)
    '''
    y = []
    for x_value in x:
        psi = 1.0*(R0-x_value)/sigma
        num1 = math.exp(-psi*psi/4) * math.pow(sigma, 1.0/p) * spec.gamma(1.0/p)
        denom = math.sqrt(2*math.pi) * rho * p * math.pow(alpha, 1.0/p) *(1 + beta*R0)
        num2 = 1.0/sigma * spec.pbdv(-1.0/p,-psi)[0] + (beta/p + gamma*beta + epsilon/R0)*spec.pbdv((-1.0/p -1), -psi)[0]
        dose = Phi0 * num1 * num2 / denom
        y.append(dose)
    y = np.array(y)
    # REPLACE ALL nan AND inf WITH ZEROS
    # (This was to catch errors with parabolic cylinder function at low depths
    # but hopefully not needed if focussing on the peak)
    y[y == -inf] = 0
    y[y == inf] = 0
    return np.nan_to_num(y)


def only_fit_peak(x, y, R0_init, sigma_init):
    ''' Shorten the data to that within -15*sigma to +6*sigma of the peak
    '''
    prox_pos = R0_init - 15*sigma_init
    prox_index = np.argmin(np.absolute(x - prox_pos))
    dist_pos = R0_init + 6*sigma_init
    dist_index = np.argmin(np.absolute(x - dist_pos))
    y = y[prox_index:dist_index]
    x = x[prox_index:dist_index]
    return x, y


def bortfeld_fit(data):
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

    # Form initial guess for optimizer
    R0_init = x[np.argmax(y)]
    E0_data = math.pow(R0_init/alpha, 1.0/p)
    sigma_init = math.sqrt(((0.012*math.pow(R0_init,0.935))**2) + ((0.01*E0_data*alpha*p*math.pow(E0_data,p-1))**2))
    epsilon_init = 0.1
    Phi0_init = 1.0

    # Cut data to that closer to the peak
    x_peak, y_peak = only_fit_peak(x, y, R0_init, sigma_init)

    # Make the model and create the variable parameters
    model = Model(normalised_dose)
    params = Parameters()
    params.add("Phi0", value=Phi0_init)
    params.add("R0", value=R0_init, min=0)
    params.add("sigma", value=sigma_init, min=0)
    params.add("epsilon", value=epsilon_init, min=0)

    # Fit the model
    result = model.fit(y_peak, params, x=x_peak)
    fit_report = result.fit_report()

    # Get best parameters
    energy = math.pow(result.params['R0'].value/alpha, 1.0/p)
    params_best = Parameters()
    params_best.add("Phi0", value=result.params['Phi0'].value)
    params_best.add("R0", value=result.params['R0'].value, min=0)
    params_best.add("sigma", value=result.params['R0'].value, min=0)
    params_best.add("epsilon", value=result.params['epsilon'].value, min=0)

    x_bortfeld_best = np.arange(0, int(max(x)+1), 0.0005).tolist()
    y_bortfeld_best = model.eval(params_best, x=x_bortfeld_best)
    x_bortfeld_best, y_bortfeld_best = only_fit_peak(x_bortfeld_best, y_bortfeld_best)
    y_bortfeld_best = [100*value/np.amax(y_bortfeld_best) for value in y_bortfeld_best]

    data = [x_bortfeld_best, y_bortfeld_best]

    return data, fit_report


def main():
    '''Code to print peak properties for acquired giraffe csv file'''
    filepath = eg.fileopenbox('Select the Giraffe csv file', filetypes='*.csv')
    pdd = pm.DepthDoseFile(filepath)
    energy = eg.integerbox('Enter Beam Energy (70-245MeV)',
                           'Enter Energy', lowerbound=70, upperbound=245
                           )
    props = pm.PeakProperties(pdd.data, energy)
    print(f'D80 = {props.Dist80}\n'
          f'D90 = {props.Dist90}\n'
          f'D20 = {props.Dist20}\n'
          f'Fall Off = {props.FallOff}')


if __name__ == "__main__":
    main()
