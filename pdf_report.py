
import os
import shutil
import numpy as np
import pandas as pd
import calendar
from datetime import datetime
from fpdf import FPDF
import matplotlib.pyplot as plt


class PDF(FPDF):
    def __init__(self, title):
        super().__init__()
        self.WIDTH = 210
        self.HEIGHT = 297
        self.title = title

    def header(self):
        # Custom logo and positioning
        # Create an `assets` folder and put any wide and short image inside
        # Name the image `logo.png`
        self.image('data\\logo\\giraffe.png', 10, 6, 15)
        self.set_font('Arial', 'B', 16)
        self.cell((self.WIDTH/2)-10-30)
        self.cell(60, 1, self.title, 0, 0, 'C')
        self.ln(40)

    def footer(self):
        # Page numbers in the footer
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')

    def page_body_userinput(self, UserInput):
        self.set_font('Arial', size=12, style='BU')
        self.cell(10, h=10)
        self.cell(25, h=10, ln=2, txt='User Input')
        self.set_font('Arial', size=8)
        now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        self.cell(25, h=5, ln=2, txt='Acquired on: ' + UserInput.adate)
        self.cell(25, h=5, ln=2, txt='Report created: ' + now)
        self.cell(25, h=5, ln=2, txt='Gantry: ' + UserInput.gantry)
        self.cell(25, h=5, ln=2, txt='Gantry Angle: ' + UserInput.gantry_angle)
        self.cell(25, h=5, ln=2, txt='Equipment: ' + UserInput.equipment)
        self.cell(25, h=5, ln=2, txt='Operator 1: ' + UserInput.operator_1)
        if UserInput.operator_2 is None:
            self.cell(25, h=5, ln=2, txt='Operator 2: ')
        else:
            self.cell(25, h=5, ln=2, txt='Operator 2: '
                      + UserInput.operator_2)

    def page_body_omnipro(self, dict):
        self.set_font('Arial', size=12, style='BU')
        self.cell(10, h=10)
        self.cell(25, h=10, ln=1,
                  txt='Range Parameters - Compare against OmniPro')
        self.set_font('Arial', size=10, style='B')
        keys = ['D20', 'D80', 'D90']
        self.cell(10, h=10)
        self.cell(25, h=10, border=1, align='C', txt='Energy')
        for key in keys:
            self.cell(20, h=10, border=1, align='C', txt=key)
        self.ln()
        self.set_font('Arial', size=8)
        for i, value in enumerate(dict['Energy']):
            self.cell(10, h=5)
            self.cell(25, h=5, border=1, align='C', txt=str(dict['Energy'][i]))
            for key in keys:
                self.cell(20, h=5, border=1, align='C',
                          txt=str(round((dict[key][i]/10), 3)))
            self.ln()

    def page_body_summary(self, dict):
        self.set_font('Arial', size=12, style='BU')
        self.cell(10, h=10)
        self.cell(25, h=10, ln=1, txt='Results Summmary')
        self.set_font('Arial', size=8)
        dict_keys = list(dict.keys())
        gantry_diff_keys = [key for key in dict_keys if 'Gantry Diff' in key]
        plan_diff_keys = [key for key in dict_keys if 'Plan Diff' in key]
        gantry_diff_failed = []
        plan_diff_failed = []
        for i, value in enumerate(dict['Energy']):
            for key in gantry_diff_keys:
                if dict[key][i] is None:
                    pass
                elif abs(dict[key][i]) > 0.3:
                    msg = '['+str(dict['Energy'][i])+'MeV] ' + \
                                  key+' - Fail (Warning)'
                    gantry_diff_failed.append(msg)
            for key in plan_diff_keys:
                if dict[key][i] is None:
                    pass
                elif abs(dict[key][i]) > 1:
                    msg = '['+str(dict['Energy'][i])+'MeV] ' + \
                                  key+' - Fail (Action)'
                    plan_diff_failed.append(msg)
        self.cell(10, h=6)
        if gantry_diff_failed:
            self.cell(50, h=6, ln=2, txt='Warning Level:')
            for msg in gantry_diff_failed:
                self.cell(50, h=6, ln=2, txt=msg)
        if plan_diff_failed:
            self.cell(50, h=6, ln=2, txt='Action Level:')
            for msg in plan_diff_failed:
                self.cell(50, h=6, ln=2, txt=msg)
        if (not gantry_diff_failed) and (not plan_diff_failed):
            self.cell(50, h=6,  ln=2, txt='All energies passed')

    def page_body_3images(self, images):
        # Determine how many plots there are per page and set positions
        # and margins accordingly
        if len(images) == 3:
            self.image(images[0], 15, 25, self.WIDTH - 30)
            self.image(images[1], 15, self.WIDTH / 2 + 5, self.WIDTH - 30)
            self.image(images[2], 15, self.WIDTH / 2 + 90, self.WIDTH - 30)
        elif len(images) == 2:
            self.image(images[0], 15, 25, self.WIDTH - 30)
            self.image(images[1], 15, self.WIDTH / 2 + 5, self.WIDTH - 30)
        else:
            self.image(images[0], 15, 25, self.WIDTH - 30)

    def print_3images(self, images):
        # Generates the report
        self.add_page()
        self.page_body_3images(images)

    def print_text(self, dict, UserInput):
        # Generates the report
        self.add_page()
        self.set_y(30)
        self.page_body_userinput(UserInput)
        self.ln(10)
        self.page_body_summary(dict)
        self.ln(10)
        self.page_body_omnipro(dict)


def plot(dict, key_y, key_x='Energy', filename='output.png'):
    plt.figure(figsize=(12, 4))
    plt.grid(color='#F2F2F2', alpha=1, zorder=0)
    plt.scatter(dict[key_x], dict[key_y], color='teal', zorder=2)
    if (key_y[-11:] == 'Gantry Diff') and (key_x == 'Energy'):
        plt.plot([65, 250], [0.3, 0.3],
                 color='orange', lw=3, zorder=1)
        plt.plot([65, 250], [-0.3, -0.3],
                 color='orange', lw=3, zorder=1)
        plt.plot([215, 215], [-0.3, 0.3],
                 linestyle='dashed', color='plum', zorder=1)
    elif (key_y[-9:] == 'Plan Diff') and (key_x == 'Energy'):
        plt.plot([65, 250], [1, 1],
                 color='firebrick', lw=3, zorder=2)
        plt.plot([65, 250], [-1, -1],
                 color='firebrick', lw=3, zorder=2)
        plt.plot([215, 215], [-1, 1],
                 linestyle='dashed', color='plum', zorder=1)

    plt.title(key_y, fontsize=18)
    plt.xlabel(key_x + '(MeV)', fontsize=12)
    plt.xticks(fontsize=9)
    plt.ylabel('Difference (mm)\n(Reference - Measured)', fontsize=12)
    plt.yticks(fontsize=9)
    plt.savefig(filename, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close()


def compile_graphs(dict, dirname):

    keys = ['D20 Gantry Diff', 'D80 Gantry Diff', 'D90 Gantry Diff',
            'D20 Plan Diff', 'D80 Plan Diff', 'D90 Plan Diff']
    for key in keys:
        filename = key + '.png'
        plot(dict, key, filename=os.path.join(dirname, filename))

    counter = 0
    pages_data = []
    temp = []
    # Get all plots
    plan_diff_files = sorted([x for x in os.listdir(dirname) if 'Plan' in x])
    gantry_diff_files = sorted(
        [x for x in os.listdir(dirname) if 'Gantry' in x])
    files = gantry_diff_files + plan_diff_files
    # Iterate over all created visualization
    for filename in files:
        # We want 3 per page
        if counter == 3:
            pages_data.append(temp)
            temp = []
            counter = 0
        temp.append(os.path.join(dirname, filename))
        counter = counter + 1

    if temp:
        pages_data.append(temp)

    return pages_data


def write_summary_report(dict, UserInput):

    filename = 'Giraffe Summary Report.pdf'
    report_filepath = os.path.join(UserInput.dirname, filename)

    pages_data = compile_graphs(dict, UserInput.dirname)
    pdf = PDF(UserInput.title)
    pdf.print_text(dict, UserInput)
    for page in pages_data:
        pdf.print_3images(page)
    pdf.output(report_filepath)

    return
