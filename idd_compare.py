"""
    Demo script:
        - Ceate IDDs from i) asc file used to define Eclipse model, and ii) RT DICOM files.
        - Compare IDD peak properties
        - Graph and print results
        
    Alex Grimwood 2021
"""

import os
root_path = 'O:/protons/Work in Progress/AlexG/pdd-analysis'
asc_path = 'O:/protons/Work in Progress/AlexG/pdd-analysis/TPS_IDD_70-245-MeV.asc'
dcm_path = 'O:/protons/Work in Progress/AlexG/pdd-analysis/zzz_PBT_comm_SingleSpots/1 Spt G 270 100MU/SeparateBeamAG'
root_path = os.path.normpath(root_path)
asc_path = os.path.normpath(asc_path)
dcm_path = os.path.normpath(dcm_path)
out_path = os.path.join(root_path, 'idd_compare_output')
os.makedirs(out_path, exist_ok=True)
os.chdir(root_path)

import pdd_module
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Load IDDs from the asc file
asc = pdd_module.DepthDoseFile(asc_path)

# Generate IDDs from RT Dose DICOMs
rd = pdd_module.DoseCube(dcm_path, depth_axis='x', msg=True)

# Assess IDD properties from both sources and save to dataframe
RD = []
ASC = []
p = []
ENERGIES = rd.energy
for energy in ENERGIES:
    asc_index = asc.energy.index(energy)
    asc_data = asc.data[asc_index]
    rd_index = rd.energy.index(energy)
    rd_iso = rd.isocentre[rd_index][0]
    rd_crn = rd.dosecube_vertex[rd_index][0]
    rd_offset = (rd_iso-rd_crn)
    rd_dep = rd.data[rd_index][0,:]
    rd_dos = rd.data[rd_index][1,:]
    rd_depth = rd_dep-rd_offset
    rd_data = np.vstack((rd_depth, rd_dos))
    asc_peak = pdd_module.PeakProperties(asc_data, energy)
    rd_peak = pdd_module.PeakProperties(rd_data, energy)
    ASC.append(asc_peak)
    RD.append(rd_peak)
    p.append(
        {
            "Energy": energy,
            "NIST Range": asc_peak.NISTRange,
            "ASC NIST Diff": np.round(asc_peak.NISTDiff,2),
            "DCM NIST Diff": np.round(rd_peak.NISTDiff,2),
            "ASC Peak Width": np.round(asc_peak.PeakWidth,2),
            "DCM Peak Width": np.round(asc_peak.PeakWidth-rd_peak.PeakWidth,2),
            "Peak Width Diff": np.round(rd_peak.PeakWidth,2),
            "ASC P80": np.round(asc_peak.Prox80,2),
            "ASC D80": np.round(asc_peak.Dist80,2),
            "DCM P80": np.round(rd_peak.Prox80,2),
            "DCM D80": np.round(rd_peak.Dist80,2),
            "P80 Diff": np.round(rd_peak.Prox80-asc_peak.Prox80,2),
            "D80 Diff": np.round(rd_peak.Dist80-asc_peak.Dist80,2),
            "ASC P90": np.round(asc_peak.Prox90,2),
            "ASC D90": np.round(asc_peak.Dist90,2),
            "DCM P90": np.round(rd_peak.Prox90,2),
            "DCM D90": np.round(rd_peak.Dist90,2),
            "P90 Diff": np.round(rd_peak.Prox90-asc_peak.Prox90,2),
            "D90 Diff": np.round(rd_peak.Dist90-asc_peak.Dist90,2),
        }
    )
    
# Write analysis to files
results_df = pd.DataFrame(p)
results_df.to_csv(os.path.join(out_path,'idd_analysis.csv'))

prop_cycle = plt.rcParams['axes.prop_cycle']
colors = prop_cycle.by_key()['color']
cols = colors[0:2]

fig = plt.figure(figsize=(20,20))

ax2=plt.subplot(2,3,1)    
ax3=plt.subplot(2,3,2)
ax4=plt.subplot(2,3,3)
ax1=plt.subplot(2,3,4)
ax5=plt.subplot(2,3,5)
ax6=plt.subplot(2,3,6)

mrk = ['x','+']
ls = ''
ms = 4

v_parts = ax1.violinplot(dataset=[results_df['ASC NIST Diff'],results_df['DCM NIST Diff']], showmedians=True, showextrema=True)
ax1.set_xticks([1.0,2.0])
ax1.set_xticklabels(['ASC','DCM'])
ax1.set_ylabel('NIST Diff (mm)')
ax1.set_title('NIST Range Differences')
ax1.set_xticks([1.0,2.0])
ax1.set_xticklabels(['ASC','DCM'])
ax1.set_ylabel('NIST Diff (mm)')
ax1.set_title('NIST Range Differences')
for vp, c in zip(v_parts['bodies'],colors[0:2]):
    vp.set_edgecolor(c)
    vp.set_facecolor(c)
    
for partname in ('cbars','cmins','cmaxes'):
    vp = v_parts[partname]
    vp.set_edgecolor('black')
    vp.set_linewidth(1)

v_parts['cmedians'].set_linewidth(2)
v_parts['cmedians'].set_edgecolor('black')

ax2.plot(results_df['Energy'],results_df['ASC Peak Width'],marker=mrk[0], linestyle=ls, ms=ms)
ax2.plot(results_df['Energy'],results_df['DCM Peak Width'],marker=mrk[1], linestyle=ls, ms=ms)
ax2.set_xlabel('Energy (MeV)')
ax2.set_ylabel('Peak Width (mm)')
ax2.legend(['ASC','DCM'])
ax2.set_title('Peak Widths')

ax3.plot(results_df['Energy'],results_df['ASC P80'], color=colors[0], marker=mrk[0], linestyle=ls, ms=ms)
ax3.plot(results_df['Energy'],results_df['ASC D80'], color=colors[0], marker=mrk[0], linestyle=ls, ms=ms)
ax3.plot(results_df['Energy'],results_df['DCM P80'], color=colors[1], marker=mrk[1], linestyle=ls, ms=ms)
ax3.plot(results_df['Energy'],results_df['DCM D80'], color=colors[1], marker=mrk[1], linestyle=ls, ms=ms)
ax3.set_xlabel('Energy (MeV)')
ax3.set_ylabel('Peak 80% (mm)')
ax3.legend(['ASC P80','ASC D80','DCM P80','DCM D80'])
ax3.set_title('Peak-Distal 80%')

ax4.plot(results_df['Energy'],results_df['ASC P90'], color=colors[0], marker=mrk[0], linestyle=ls, ms=ms)
ax4.plot(results_df['Energy'],results_df['ASC D90'], color=colors[0], marker=mrk[0], linestyle=ls, ms=ms)
ax4.plot(results_df['Energy'],results_df['DCM P90'], color=colors[1], marker=mrk[1], linestyle=ls, ms=ms)
ax4.plot(results_df['Energy'],results_df['DCM D90'], color=colors[1], marker=mrk[1], linestyle=ls, ms=ms)
ax4.set_xlabel('Energy (MeV)')
ax4.set_ylabel('Peak 90% (mm)')
ax4.legend(['ASC P90','ASC D90','DCM P90','DCM D90'])
ax4.set_title('Peak-Distal 90%')

v_parts = ax5.violinplot(dataset=[results_df['P80 Diff'],results_df['D80 Diff']], showmedians=True, showextrema=True)
ax5.set_xticks([1.0,2.0])
ax5.set_xticklabels(['ASC','DCM'])
ax5.set_ylabel('80% Diff (mm)')
ax5.set_title('ASC-DCM 80% Differences')
ax5.set_xticks([1.0,2.0])
ax5.set_xticklabels(['P80','D80'])
for vp, c in zip(v_parts['bodies'],colors[2:4]):
    vp.set_edgecolor(c)
    vp.set_facecolor(c)
    
for partname in ('cbars','cmins','cmaxes'):
    vp = v_parts[partname]
    vp.set_edgecolor('black')
    vp.set_linewidth(1)

v_parts['cmedians'].set_linewidth(2)
v_parts['cmedians'].set_edgecolor('black')

v_parts = ax6.violinplot(dataset=[results_df['P90 Diff'],results_df['D90 Diff']], showmedians=True, showextrema=True)
ax6.set_xticks([1.0,2.0])
ax6.set_xticklabels(['ASC','DCM'])
ax6.set_ylabel('90% Diff (mm)')
ax6.set_title('ASC-DCM 90% Differences')
ax6.set_xticks([1.0,2.0])
ax6.set_xticklabels(['P90','D90'])
for vp, c in zip(v_parts['bodies'],colors[2:4]):
    vp.set_edgecolor(c)
    vp.set_facecolor(c)
    
for partname in ('cbars','cmins','cmaxes'):
    vp = v_parts[partname]
    vp.set_edgecolor('black')
    vp.set_linewidth(1)

v_parts['cmedians'].set_linewidth(2)
v_parts['cmedians'].set_edgecolor('black')

fig.savefig(os.path.join(out_path,'NIST_Differences.pdf'))
