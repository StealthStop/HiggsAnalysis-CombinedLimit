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
    "RPV350" ,
    "RPV550" ,
    "RPV850" ,
    "SYY350" ,
    "SYY550" ,
    "SYY850" ,
    "SHH350" ,
    "SHH550" ,
    "SHH850" ,
]

histos = {
    #Stop1 vs Stop2 Mass
    "h_Mass_stop1vsstop2_PtRank_baseline_0l" ,
    "h_Mass_stop1vsstop2_MassRank_baseline_0l" ,
    "h_Mass_stop1vsstop2_ScalarPtRank_baseline_0l" , 
    
    #Diff vs Avg
    "h_stopMasses_diffVSavg_baseline_0l" ,

    # stops MassVsPt
    "h_stop1_MassVsPt_PtRank_baseline_0l" ,
    "h_stop2_MassVsPt_PtRank_baseline_0l" ,
    "h_stop1_MassVsPt_MassRank_baseline_0l" ,
    "h_stop2_MassVsPt_MassRank_baseline_0l" ,
    "h_stop1_MassVsPt_ScalarPtRank_baseline_0l" ,
    "h_stop2_MassVsPt_ScalarPtRank_baseline_0l" ,
    "h_stop1_MassVsScalarPt_ScalarPtRank_baseline_0l" ,
    "h_stop2_MassVsScalarPt_ScalarPtRank_baseline_0l" ,
}


histoNames = {
    #Stop1 vs Stop2 Mass
    "h_Mass_stop1vsstop2_PtRank_baseline_0l"             : "stop12_Pt",
    "h_Mass_stop1vsstop2_MassRank_baseline_0l"           : "stop12_Mass",
    "h_Mass_stop1vsstop2_ScalarPtRank_baseline_0l"       : "stop12_SPt", 
    
    #Diff vs Avg
    "h_stopMasses_diffVSavg_baseline_0l"                 : "diffavg",

    # stops MassVsPt
    "h_stop1_MassVsPt_PtRank_baseline_0l"                : "m1vsPt_Pt",
    "h_stop2_MassVsPt_PtRank_baseline_0l"                : "m2vsPt_Pt",
    "h_stop1_MassVsPt_MassRank_baseline_0l"              : "m1vsPt_Mass",
    "h_stop2_MassVsPt_MassRank_baseline_0l"              : "m2vsPt_Mass",
    "h_stop1_MassVsPt_ScalarPtRank_baseline_0l"          : "m1vsPt_SPt",
    "h_stop2_MassVsPt_ScalarPtRank_baseline_0l"          : "m2vsPt_SPt",
    "h_stop1_MassVsScalarPt_ScalarPtRank_baseline_0l"    : "m1vsSPt_SPt",
    "h_stop2_MassVsScalarPt_ScalarPtRank_baseline_0l"    : "m2vsSPt_SPt",
}

njets = [
    "_Njet6",
    "_Njet7",
    "_Njet8",
    "_Njet9",
    "_Njet10",
    "_Njet11",
    "_Njetge12",
]

def writeDataCard(binVals, dataset, histo):

    halfsig = False 
 
    if dataset.find('350') != -1: 
        halfsig = True 
    
    processNames = ["Signal", "QCD", "TT"]

    with open("Njet_Cards/Card%s_%s.txt" % (dataset,histoNames[histo]), 'w') as f:
        f.write("Datacard for 2016 %s" % dataset)
        f.write( "\n" )
        f.write( "imax %d number of bins\n" % len(binVals) )
        f.write( "jmax 2 number of processes minus 1\n" )
        f.write( "kmax 3 number of nuisance parameters\n" )
        f.write( "\n" )
        f.write( "-------------------------------------------------------------------------------------------------------------------------------------------\n" )
        f.write( "\n" )
        bins        = "bin         "
        observation = "observation "
        for i in range(len(binVals)):
            bins        += "D{0: <9}".format(i)
            if halfsig:
                observation += "{0: <10}".format(round((binVals[i][0]/2+binVals[i][0]+binVals[i][0]),1))
            else:
                observation += "{0: <10}".format(round((binVals[i][0]+binVals[i][0]+binVals[i][0]),1))
        f.write( bins+"\n" )
        f.write( observation+"\n" )
        f.write( "-------------------------------------------------------------------------------------------------------------------------------------------\n" )
        f.write( "# background rate taken from events in bin\n" )
        bins      = "bin              "
        process1 = "process          "
        process2 = "process          "
        rate     = "rate             "
        f.write( "" )
        for i in range(len(binVals)):
            for j in range(3):
                bins      += "{0: <16} ".format("D"+str(i))
                process1 += "{0: <16} ".format(processNames[j])
                process2 += "{0: <16} ".format(j)
                if j == 0 and halfsig: 
                    rate     += "{0: <16} ".format(binVals[i][j]/2) 
                else: 
                    rate     += "{0: <16} ".format(binVals[i][j]) 
        f.write( bins+"\n" )
        f.write( process1+"\n" )
        f.write( process2+"\n" )
        f.write( rate+"\n" )
        f.write( "-------------------------------------------------------------------------------------------------------------------------------------------\n" )
        f.write( "# Normal uncertainties in the signal region\n" )
        lumiSys  = "lumi_13TeV      lnN  "
        ttbarSys = "ttbar_unc       lnN  "
        qcdSys   = "qcd_unc         lnN  "
        for i in range(len(binVals)):
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
    hlist = []

    for f in glob.glob("/uscms/home/bcrossma/nobackup/SL7/CMSSW_10_2_9/src/Analyzer/Analyzer/test/condor/NjetsBinning/output-files/rootFiles/*.root"):
        if(f.find(dataset) != -1):
            flist = [ROOT.TFile.Open(f)] + flist
        elif (f.find("TT") != -1 or f.find("QCD") != -1):
            flist.append(ROOT.TFile.Open(f))


    #Ordering of histos in this list is signal, QCD, TT
    for nj in njets:
        hlist_temp = []
        for f in flist:
            histo_name = histo + nj
            hlist_temp.append(f.Get(histo + nj))
        hlist.append(hlist_temp)

    # Define array of bin boundaries
    binVals = []
    binInt = 0
    i = 0

    xstep = hlist[0][0].GetNbinsX()/options.numBin 
    ystep = hlist[0][0].GetNbinsY()/options.numBin 
 
#    print "Bin Edges (prints bottom left corner of bins that are kept): "
    for x in range(0, hlist[0][0].GetNbinsX()-1, xstep):
        for y in range(0, hlist[0][0].GetNbinsY()-1, ystep):
            for hs in hlist:
                temp_binVals = []
                for h in hs:
                    binInt = h.Integral(x, x+xstep-1, y, y+ystep-1)
                    if (round(binInt,1) < 0.1):
                        temp_binVals.append(0.1) #Used to correct any zero bins
                    else:
                        temp_binVals.append(round(binInt,1))
                binVals.append(temp_binVals)

    writeDataCard(binVals, dataset, histo)

def main():
    if not os.path.exists("Njet_Cards"):
        os.mkdir("Njet_Cards")

    if(options.signalName == "all"):
        for d in datasets:
            print "Making data cards for signal model %s" % d
            if (d == "TT" or d == "QCD"):
                break
            if(options.histoName == "all"):
                for h in histos:
                    getCard(d,h)
            else:
                getCard(d,options.histoName)

    else:
        if(options.histoName == "all"):
            for h in histos:
                getCard(options.signalName,h)
        else:
            getCard(options.signalName,options.histoName)

if __name__ == "__main__":
    main()

