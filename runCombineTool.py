import ROOT
import math
import sys
import os
import json
import subprocess
import numpy as np
import array as arr
import glob
from os import system
from ROOT import TFile, gROOT, gStyle

from parseSignificance import parseSignificance
from sortSignificance import sortSignificance 

debug = True

def print_db(input):
    if (debug):
        print input

def main():
    # ---------------------
    # get the data cards
    # ---------------------
    paths = [
        'Njet_Cards',
        'OldSeed_Cards',
        'TopSeed_Cards'
    ]

    for path in paths:
        os.system("rm Significance_{}.txt".format(path))
        os.system("rm ExpectedSignificance_{}.txt".format(path))

    # ---------------------------
    # loop over the data cards
    # ---------------------------
    dataCards = []

    for f in glob.glob("DataCardProducer/{}/*.txt".format(paths[0])):
        dataCards.append(f.rsplit('/',1)[1])

    for datacard in dataCards:
        print("------------------------------------------------------------------------------")
        print_db("Getting data cards: " + datacard)
        print("------------------------------------------------------------------------------")
         
        # ----------------------
        # loop over the paths
        # ----------------------
        for path in paths:
            #print("\n")
            print_db("Going to path: " + path)

            # --------------------------------
            # saving the outputs as a txt file
            # --------------------------------
            with open('Significance_{}.txt'.format(path), 'a') as f:
                f.write("------------------------------------------------------------------------------\n")
                f.write("GettingDataCards: " + datacard + "\n")
                f.write("GoingToPath: " + path + "\n")
                f.write("------------------------------------------------------------------------------\n")
                f.close()

            # --------------------------------
            # running the combine tool command
            # --------------------------------
            command = ('combine -M Significance DataCardProducer/' + path + '/' + datacard + ' -t -1 --expectSignal=1')
            os.system(command + '&>> Significance_{}.txt'.format(path))      


            # -----------------------------------------------
            # read the txt file to get only significance line
            # -----------------------------------------------
            ExpectedSignificance = {}

            with open("Significance_{}.txt".format(paths[0]), "r") as f:
                all_lines = f.readlines()
                
                for line in all_lines:
                    if "GettingDataCards: " in line:
                        datacard_ = line.split(" ")[-1].rstrip("\n")
                    if "GoingToPath: " in line:
                        path_ = line.split(" ")[-1].rstrip("\n")
                    if "Significance: " in line:
                        significance = float(line.split(" ")[-1].rstrip("\n"))
                       
                        file1 = open("ExpectedSignificance_{}.txt".format(path), "a")
                        file1.writelines("Data Card: %s  |  Seed Method: %s  |  Significance: %f\n" % (datacard_, path_, significance))
         
                        # ----------------------------------------        
                        # create a dictionary to convert into JSON
                        # ----------------------------------------
                        ExpectedSignificance = {
                            "data card   " : datacard_,
                            "seed method " : path_,
                            "significance" : significance,
                        }

                        # -----------------
                        # convert into JSON
                        # -----------------
                        x = json.dumps(ExpectedSignificance, indent=1)
                        with open('ExpectedSignificance_json.txt', 'a') as g:
                            g.write(x)
                            g.close()
 
    f.close()
  
    for path in paths:
        parseSignificance(["Significance_{}.txt".format(path)])
        sortSignificance(["Significance_{}.txt".format(path)])

if __name__ == "__main__":
    main()                
