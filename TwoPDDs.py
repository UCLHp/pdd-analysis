from numpy import asarray, random, isnan
from PDD_Module2 import *
from tkinter import Tk, filedialog
import os
from easygui import multenterbox, buttonbox, enterbox, msgbox
import random as rnd
import pandas as pd
import xlsxwriter

NIST = asarray([(70,40.75),(75,46.11),(80,51.76),(85,57.69),(90,63.89),(95,70.35),(100,77.07),(105,84.05),(110,91.28),(115,98.75),(120,106.50),(125,114.40),(130,122.60),(135,131.00),(140,139.60),(145,148.50),(150,157.60),(155,166.80),(160,176.30),(165,186.00),(170,195.90),(175,206.00),(180,216.30),(185,226.70),(190,237.40),(195,248.30),(200,259.30),(205,270.50),(210,281.90),(215,293.40),(220,305.20),(225,317.10),(230,329.10),(235,341.30),(240,353.70),(245,366.30),(250,379.00)])

root = Tk() #Open TK for a File Dialog
root.withdraw() #Hides the tk Pop-up window

dir = 'C:/Users/cgillies/Desktop/Python_3/GIT Some/TwoDataSets-PDD/Reference Data' # Hard coded reference data location

RefData={}
TestData={}
gammas={}
RefDataProps={}
TestDataProps={}

for filename in os.listdir(dir): # Loop through each file in the directory
    file = os.path.basename(filename) # Splits file into the location and:
    name = float(os.path.splitext(file)[0]) # Extracts filename without extension (should be the energy)
    RefData[name], E, D, GA = ReadTank(os.path.join(dir,filename)) # This function is in the PDD module and reads MCC files.



dir2 = filedialog.askdirectory(title='Please Select Test Data') #Asks user to select folder containing data in MCC or CSV format
if dir2 == '':
    exit()

OffSet = enterbox("Enter WET Offset (mm)", "WET Offset", ('0')) #User inputs offset in terms of water equivalent thickness (due to tank wall chamber thickness etc.)

if OffSet == None:  #Ensure something was selected for WET thickness
    msgbox("Please re-run the program and enter an offset, even if it's 0.0", title="WET box closed without entry")
    exit()


try: # Ensure entered WET value is a sensible entry
    float(OffSet)
except ValueError:
    msgbox("Please re-run the program and enter an appropriate value for the WET offset", title="WET Value Error")
    exit()
OffSet=float(OffSet)

for filename in os.listdir(dir2): # Loop through each file in the directory
    file = os.path.basename(filename) # Splits file into the location and:
    name = float(os.path.splitext(file)[0]) # Extracts filename without extension (should be the energy)
    TestData[name], E, D, GA = ReadTank(os.path.join(dir2,filename)) # This function is in the PDD module and reads MCC files.


    TestData[name][0] = TestData[name][0]+OffSet
    noise = random.normal(0,1,len(TestData[name][1]))
    TestData[name][1] = TestData[name][1] + noise



setGamma = buttonbox(msg="Absolute or Relative Gamma Analysis?",title='Define Gamma Analysis', choices=('Relative','Absolute'), cancel_choice = 'Relative') #Pop up box to choose absolute or relative gamma

if setGamma == None:  #Ensure something was selected for Gamma
    msgbox("Please re-run the program and select Relative or Absolute", title="No Gamma Type Selected")
    exit()

crit = (multenterbox("enter gamma criteria","gamma criteria", ('mm','%'), ('3','3'))) # Get's user to enter criteria for gamma analysis
try: # Ensures Gamma Criteria entries are numbers
    for x in crit:
        float(x)
except ValueError:
    msgbox("Please re-run the program and enter appropriate Gamma Criteria", title="Gamma Criteria Error")
    exit()

crit = asarray(crit).astype(float)



writer = pd.ExcelWriter('TEST.xlsx',engine='xlsxwriter')

DiffList = ['=I2-H2','=I3-H3','=I4-H4','=I5-H5','=I6-H6','=I7-H7','=I8-H8','=I9-H9','=I10-H10','=I11-H11','=I12-H12','=I13-H13']

for key in sorted(TestData.keys()):
    if key in RefData.keys():

        gammas[key], TestDataProps[key], RefDataProps[key],  = TwoPDDs(TestData[key], RefData[key], float(key), setGamma, crit)
        PassCrit = 100.00*sum(x<1 for x in gammas[key])/((len(gammas[key])-sum(isnan(x) for x in gammas[key]))) # Calculates the pass criteria as a fraction of gammas less than 1
        TestDataXL = pd.DataFrame({'Test Data Depth':TestData[key][0],'Test Data Dose':TestData[key][1]})
        RefDataXL = pd.DataFrame({'Reference Data Depth':RefData[key][0],'Reference Data Dose':RefData[key][1]})
        gammasXL = pd.DataFrame({'Gamma Values':gammas[key]})
        DataPropsXL = pd.DataFrame({'Property':list(TestDataProps[key].__dict__.keys()),'Test Data':list(TestDataProps[key].__dict__.values()),'Reference Data':list(RefDataProps[key].__dict__.values()),'Difference':DiffList})

        TestDataXL.to_excel(writer,sheet_name=str(int(key)),index=False)
        RefDataXL.to_excel(writer,sheet_name=str(int(key)),index=False, startcol=2)
        gammasXL.to_excel(writer,sheet_name=str(int(key)),index=False, startcol=4)
        DataPropsXL.to_excel(writer,sheet_name=str(int(key)),index=False,startcol=6)

        workbook = writer.book
        worksheet = writer.sheets[str(int(key))]

        worksheet.set_column('A:A', 14.43)
        worksheet.set_column('B:B', 13.43)
        worksheet.set_column('C:C', 20.0)
        worksheet.set_column('D:D', 19.0)
        worksheet.set_column('E:E', 13.71)
        worksheet.set_column('G:G', 10.0)
        worksheet.set_column('H:H', 12.0)
        worksheet.set_column('I:I', 14.0)
        worksheet.set_column('J:J', 11.29)


        chart = workbook.add_chart({'type': 'scatter'})
        chart.add_series({'name': [str(int(key)),0,1],'categories': [str(int(key)),1,0,1+len(TestData[key][0]),0],'values': "='"+str(int(key))+"'!$B$2:$B$"+str(1+len(TestData[key][1])),'y2_axis':0})
        chart.add_series({'name': [str(int(key)),0,3],'categories': [str(int(key)),1,2,1+len(RefData[key][0]),2],'values': "='"+str(int(key))+"'!$D$2:$D$"+str(1+len(RefData[key][1])),'y2_axis':0})
        chart.set_y_axis({'min':0})
        chart.add_series({'name': [str(int(key)),0,4],'categories': [str(int(key)),1,0,1+len(TestData[key][0]),0],'values': "='"+str(int(key))+"'!$E$2:$E$"+str(1+len(gammas[key])),'y2_axis':1})
        chart.set_size({'width': 900, 'height':650})
        chart.set_title({'name': "Gamma Pass Rate: %1.1f%%" % PassCrit}) #Makes the title including how well the gamma analysis passed

        # chart.add_series({'values': ["'='"+str(int(key))+"'!$A$2:$B$"+str(1+len(TestData[key][0]))+"'"]})
        # chart.add_series({'values': '=70!$A$2'})
        worksheet.insert_chart('G15', chart)
        print(str(key) +' Done')
        # writer.save()
writer.save()

# workbook = xlsxwriter.Workbook('TEST.xlsx')
