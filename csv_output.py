import easygui as eg
import pandas as pd


def output_to_csv(peak_data):

    path = eg.filesavebox(msg='Create output file', title='Save Output',
                          default="output.csv", filetypes=['*.csv'])

    dict = {'E0': peak_data.E0_fit,
            'P80': peak_data.Prox80,
            'P90': peak_data.Prox90,
            'D90': peak_data.Dist90,
            'D80': peak_data.Dist80,
            'D20': peak_data.Dist20,
            'D10': peak_data.Dist10,
            'Fall Off': peak_data.FallOff,
            'PTPR': peak_data.PTPR,
            'Peak Width': peak_data.PeakWidth,
            'Halo Ratio': peak_data.HaloRat,
            'NIST Range': peak_data.NISTRange,
            'NIST Diff': peak_data.NISTDiff,
            }

    df = pd.DataFrame.from_dict(dict)

    df.to_csv(path)

    return
