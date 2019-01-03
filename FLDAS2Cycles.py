#!/usr/bin/env python3

import datetime
import math
import subprocess
import sys
import csv
import os

from dateutil import parser

def satvp(temp):
    return .6108 * math.exp(17.27 * temp / (temp + 237.3))


def tdew(ea):
    return 237.3 * math.log(ea / 0.6108) / (17.27 - math.log(ea / 0.6108))


def ea(patm, q):
    return patm * q / (0.622 * (1 - q) + q)


def process_day(row):
    tavg = float(row['Tair_f_tavg']) - 273.15
    ea_kPa = ea(float(row['Psurf_f_tavg']), float(row['Qair_f_tavg'])) / 1000
    rH = ea_kPa / satvp(tavg)
    vpd_ea = satvp(tavg) - ea_kPa

    # This formula is empiric and location / season dependent; hopefully is not needed
    # if LDAS provides Tmax and Tmin instead of the average for the day
    delta_T = 17.37 * (1.0 - 1.0 / (1.0 + vpd_ea / (0.33 * ea_kPa)))
    Tdew = tdew(ea_kPa)
    Patm = float(row['Psurf_f_tavg'])

    pp = float(row['Rainf_f_tavg']) * 86400.0
    tx = tavg + 0.5 * delta_T
    tn = tavg - 0.5 * delta_T
    solar =  float(row['SWdown_f_tavg']) * 86400.0 / 1000000.0
    if tn > Tdew:
        rhx = 100.0 * ea_kPa / satvp(tn)
    else:
        rhx = 99.9
    if tx > Tdew:
        rhn = 100.0 * ea_kPa / satvp(tx)
    else:
        rhn = 99.8
    wind = float(row['Wind_f_tavg'])

    dt = datetime.datetime.strptime(row['Date'],'%Y%m%d')
    data = '%s  %6.2f  %6.2f  %6.2f  %8.4f  %8.4f %8.4f %6.2f\n' \
           %(dt.strftime('%Y  %j'), pp, tx, tn, solar, rhx, rhn, wind)

    return (data, Patm)


def main():

    for fldas_name in os.listdir('data/'):
        if fldas_name.endswith(".csv"):
            data = ""
            Patm_total = 0.0
            Patm_count = 0

            print("Opening " + fldas_name)

            with open(os.path.join('data/', fldas_name)) as csv_file:
                csv_reader = csv.DictReader(csv_file, delimiter=',')
                line_count = 0
                for row in csv_reader:
                    (line, Patm) = process_day(row)
                    data += line
                    Patm_total += Patm
                    Patm_count += 1

            Patm_avg = Patm_total / Patm_count
            elevation = - 8200 * math.log(Patm_avg / 101325)

            fname = os.path.join('data/', fldas_name[:-4] + '.weather')
            fp = open(fname, 'w')
            # FLDAS file names are: XxxxxYyyy
            lat = float(fldas_name[6:9]) / 100.0

            fp.write('LATITUDE %4.2f\n' %(lat))
            # TODO, were do we get altitude and screening height from?
            fp.write('ALTITUDE %.2f\n' %(elevation))
            fp.write('SCREENING_HEIGHT 2\n')
            fp.write('YEAR  DOY    PP     TX      TN      SOLAR     RHX      RHN       WIND\n')
            fp.write(data)
            fp.close()

main()

