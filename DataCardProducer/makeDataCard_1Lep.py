import ROOT
from ROOT import TFile, gROOT, gStyle
import numpy as np
import math
from optparse import OptionParser
import root_numpy as rnp
import glob
import os

parser = OptionParser()
parser.add_option("-s", "--signal", action="store", type="string", dest="signalName",
    default="all", help="Name of signal root file to use as input (Use all to produce all data cards)")
parser.add_option("-H", "--histogram", action="store", type="string", dest="histoName",
    default="all", help="Name of histogram to make data card (Use all to produce all histograms)")
parser.add_option("-n", "--numBin", action="store", type="int", dest="numBin",
     default="5", help="Desired number of bins (results in n^2 bins)")

(options, args) = parser.parse_args()

datasets = [
    "RPV_350" ,
    "RPV_550" ,
    "RPV_850" ,
    "SYY_350" ,
    "SYY_550" ,
    "SYY_850" ,
    "SHH_350" ,
    "SHH_550" ,
    "SHH_850" ,
]

files = [
    "njets_for_Aron_2016",
    "njets_for_Aron_2017",
    "njets_for_Aron_2018pre",
    "njets_for_Aron_201post",
]

histos = [
    "h_njets_pt30_1l",
]

bins = [
    "D1",
    "D2",
    "D3",
    "D4",
]

histoNames = {
    "h_njets_pt30_1l": "h_njets_pt30_1l",
}

def writeDataCard(binVals, dataset, histo):
   
    halfsig = False

    if dataset.find('350') != -1:
        halfsig = True
 
    processNames = ["Signal", "QCD", "TT"]

    with open("1lCards/Card%s_%s.txt" % (dataset,histoNames[histo]), 'w') as f:
        f.write("Datacard for 2016 %s" % dataset)
        f.write( "\n" )
        f.write( "imax %d number of bins\n" % len(binVals[0]) )
        f.write( "jmax 2 number of processes minus 1\n" )
        f.write( "kmax 3 number of nuisance parameters\n" )
        f.write( "\n" )
        f.write( "-------------------------------------------------------------------------------------------------------------------------------------------\n" )
        f.write( "\n" )
        bins        = "bin         "
        observation = "observation "
        for i in range(len(binVals[0])):
            bins        += "D{0: <9}".format(i)
            if halfsig:
                observation += "{0: <10}".format(round((binVals[0][i]/2+binVals[1][i]+binVals[2][i]),1))
            else:
                observation += "{0: <10}".format(round((binVals[0][i]+binVals[1][i]+binVals[2][i]),1))
        f.write( bins+"\n" )
        f.write( observation+"\n" )
        f.write( "-------------------------------------------------------------------------------------------------------------------------------------------\n" )
        f.write( "# background rate taken from events in bin\n" )
        bins      = "bin              "
        process1 = "process          "
        process2 = "process          "
        rate     = "rate             "
        f.write( "" )
        for i in range(len(binVals[0])):
            for j in range(3):
                bins      += "{0: <16} ".format("D"+str(i))
                process1 += "{0: <16} ".format(processNames[j])
                process2 += "{0: <16} ".format(j)
                if j == 0 and halfsig:
                    rate     += "{0: <16} ".format(binVals[j][i]/2)
                else:
                    rate     += "{0: <16} ".format(binVals[j][i])
        f.write( bins+"\n" )
        f.write( process1+"\n" )
        f.write( process2+"\n" )
        f.write( rate+"\n" )
        f.write( "-------------------------------------------------------------------------------------------------------------------------------------------\n" )
        f.write( "# Normal uncertainties in the signal region\n" )
        lumiSys  = "lumi_13TeV      lnN  "
        ttbarSys = "ttbar_unc       lnN  "
        qcdSys   = "qcd_unc         lnN  "
        for i in range(len(binVals[0])):
            for j in range(3):
                if(j == 0):
                    lumiSys += "{0: <5} ".format("1.05")
                else:
                    lumiSys += "{0: <5} ".format("-")
                if(j == 1):
                    ttbarSys += "{0: <5}".format("1.20")
                else:
                    ttbarSys += "{0: <5} ".format("-")
                if(j == 2):
                    qcdSys += "{0: <5}".format("1.20")
                else:
                    qcdSys += "{0: <5} ".format("-")
        f.write( lumiSys+"\n" )
        f.write( ttbarSys+"\n" )
        f.write( qcdSys+"\n" )
        f.write( "-------------------------------------------------------------------------------------------------------------------------------------------\n" )

def getCard(dataset, histo):
    #gROOT.SetBatch(True)
    gStyle.SetOptStat(0)

    # Create list of histograms that we will need to pull data from
    flist = []
    hlist = [[],[],[]]

    for f in glob.glob("/uscms/home/bcrossma/nobackup/SL7/CMSSW_10_2_9/src/RootWorkingArea/1Lep_Significance/rootFiles/*2016.root"):
        flist.append(ROOT.TFile.Open(f))

    for b in bins:
        for f in flist:
            hlist[0].append(f.Get(b + '_' + dataset + '_' + histo))
            hlist[1].append(f.Get(b + '_QCD_' + histo))
            hlist[2].append(f.Get(b + '_TT_' + histo))

    # Define array of bin boundaries
    binVals = [[],[],[]]
    binInt = 0
    i = 0

#    print "Bin Edges (prints bottom left corner of bins that are kept): "
    for i_bin in range(1, 7):
        i = 0
        for hs in hlist:
            for h in hs:
                binInt = h.Integral(i_bin, i_bin)
                if (round(binInt,1) < 0.1):
                    binVals[i].append(0.1) #Used to correct any zero bins
                else:
                    binVals[i].append(round(binInt,1))
            i += 1
    
    writeDataCard(binVals, dataset, histo)

def main():
    if not os.path.exists("1lCards"):
        os.mkdir("1lCards")

    if(options.signalName == "all"):
        for d in datasets:
            print "Making data cards for signal model %s" % d
            for h in histos:
                getCard(d,h)

if __name__ == "__main__":
    main()

