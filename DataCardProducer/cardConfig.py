path = "/uscms_data/d3/amercald/SUSY3/CMSSW_10_2_9/src/Analyzer/Analyzer/test/condor/2016_MC_Significance2/"

lumi = 1.05

#all backgrounds are entries in the dictionary. the path to the root file (starting from base path) and the systematic uncertainty are specified
background = {
    "TT" : {
        "path" : "2016_TT.root",
        "sys"  : 1.2
    },
#    "QCD" : {
 #       "path" : "None",
 #       "sys"  : 1.2
#    }
}
#all signals are entries in the dictionary. the path to the root file (starting from the base path) and the systematic uncertainty are specified 
signal = {
    "RPV350" : {
        "path" : "2016_RPV_2t6j_mStop-350.root",
        "sys"  : "--"

    },
#    "RPV550" : {
#        "path" : "None",
#        "sys"  : 1.504
#    }
}
#the names of the histograms to use along with number of bins to divide it into
histos = {
    "h1" : {
        "name"  : "h_FatJet_Pruned_2_2l_2CandJets_ge1b_opfl",
        "nbins" : 8,
        "start" : 50,
        "end"   : 150,
    },
}
#other systematics. list the name of background/signal the systematic applies to under the "apply" key
othersys = {

    #"s1" : {
    #    "sys" : 2.05,
    #    "distr" : "gmN 4",
    #    "apply" : ["TT"]
    #}
}
