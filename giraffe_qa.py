import pdd_module as pm
import easygui as eg

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
