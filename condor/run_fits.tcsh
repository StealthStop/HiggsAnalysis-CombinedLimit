#!/bin/tcsh

#source /cvmfs/cms.cern.ch/cmsset_default.csh
#setenv SCRAM_ARCH slc6_amd64_gcc530
#cmsrel CMSSW_8_1_0
#cd CMSSW_8_1_0/src
#eval `scramv1 runtime -csh`
#git clone git@github.com:StealthStop/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
#cd $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit
#scram b clean
#scram b -j8
# 
#mkdir Keras_V1.2.5_v2
#xrdcp root://cmseos.fnal.gov//store/user/lpcsusyhad/StealthStop/FitInputs/Keras_V1.2.5_v2/njets_for_Aron.root     Keras_V1.2.5_v2/.
#xrdcp root://cmseos.fnal.gov//store/user/lpcsusyhad/StealthStop/FitInputs/Keras_V1.2.5_v2/ttbar_systematics.root  Keras_V1.2.5_v2/.
#
#mkdir Keras_V3.0.1_v2
#xrdcp root://cmseos.fnal.gov//store/user/lpcsusyhad/StealthStop/FitInputs/Keras_V3.0.1_v2/njets_for_Aron.root     Keras_V3.0.1_v2/.
#xrdcp root://cmseos.fnal.gov//store/user/lpcsusyhad/StealthStop/FitInputs/Keras_V3.0.1_v2/ttbar_systematics.root  Keras_V3.0.1_v2/.
#
#eval `scramv1 runtime -csh`
#root -l -q 'make_MVA_8bin_ws.C("2016","Keras_V1.2.5_v2","RPV","350")'
#text2workspace.py Card2016.txt -o ws_2016_RPV_350.root -m 350 --keyword-value MODEL=RPV
#combine -M AsymptoticLimits ws_2016_RPV_350.root -m 350 --keyword-value MODEL=RPV --verbose 2 -n 2016 > log_2016RPV350_Asymp.txt
#########################################################################################################################################

set inputRoot = $1
set signalType = $2
set mass = $3
set year = $4

set base_dir = `pwd`
printf "\n\n base dir is $base_dir\n\n"

source /cvmfs/cms.cern.ch/cmsset_default.csh
setenv SCRAM_ARCH slc6_amd64_gcc530

printf "\n\n ls output\n"
ls -l

printf "\n\n Get the code needed .\n\n"
cmsrel CMSSW_8_1_0
cd CMSSW_8_1_0/src
eval `scramv1 runtime -csh`
git clone https://github.com/StealthStop/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
cd $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit
scram b clean
scram b -j8

printf "\n\n ls output\n"
ls -l

printf "\n\n output of uname -s : "
uname -s
printf "\n\n"

setenv LD_LIBRARY_PATH ${PWD}:${LD_LIBRARY_PATH}
printf "\n\n LD_LIBRARY_PATH: ${LD_LIBRARY_PATH}\n\n"

printf "\n\n ls output\n"
ls -l

printf "\n\n Attempting to run Fit executable.\n\n"
mkdir Keras_V1.2.5_v2
xrdcp root://cmseos.fnal.gov//store/user/lpcsusyhad/StealthStop/FitInputs/Keras_V1.2.5_v2/njets_for_Aron.root     Keras_V1.2.5_v2/.
xrdcp root://cmseos.fnal.gov//store/user/lpcsusyhad/StealthStop/FitInputs/Keras_V1.2.5_v2/ttbar_systematics.root  Keras_V1.2.5_v2/.

mkdir Keras_V3.0.1_v2
xrdcp root://cmseos.fnal.gov//store/user/lpcsusyhad/StealthStop/FitInputs/Keras_V3.0.1_v2/njets_for_Aron.root     Keras_V3.0.1_v2/.
xrdcp root://cmseos.fnal.gov//store/user/lpcsusyhad/StealthStop/FitInputs/Keras_V3.0.1_v2/ttbar_systematics.root  Keras_V3.0.1_v2/.

eval `scramv1 runtime -csh`
echo "root -l -q 'make_MVA_8bin_ws.C("${year}","${inputRoot}","${signalType}","${mass}")'"
root -l -q -b 'make_MVA_8bin_ws.C("'${year}'","'${inputRoot}'","'${signalType}'","'${mass}'")'
text2workspace.py Card${year}.txt -o ws_${year}_${signalType}_${mass}.root -m ${mass} --keyword-value MODEL=${signalType}
combine -M AsymptoticLimits ws_${year}_${signalType}_${mass}.root -m ${mass} --keyword-value MODEL=${signalType} --verbose 2                                 -n ${year}                               > log_${year}${signalType}${mass}_Asymp.txt
combine -M FitDiagnostics   ws_${year}_${signalType}_${mass}.root -m ${mass} --keyword-value MODEL=${signalType} --plots --saveShapes --saveNormalizations   -n ${year}${signalType}${mass}           > log_${year}${signalType}${mass}_FitDiag.txt
combine -M Significance     ws_${year}_${signalType}_${mass}.root -m ${mass} --keyword-value MODEL=${signalType} -t -1 --expectSignal=1                      -n ${year}${signalType}${mass}_SignifExp > log_${year}${signalType}${mass}_Sign_sig.txt
combine -M Significance     ws_${year}_${signalType}_${mass}.root -m ${mass} --keyword-value MODEL=${signalType}                                             -n ${year}${signalType}${mass}_SignifExp > log_${year}${signalType}${mass}_Sign_noSig.txt
combine -M MultiDimFit      ws_${year}_${signalType}_${mass}.root -m ${mass} --keyword-value MODEL=${signalType} --algo=grid --points=100 --rMin 0 --rMax 3  -n SCAN_r_wSig                           > log_${year}${signalType}${mass}_multiDim.txt

printf "\n\n ls output\n"
ls -l

mv *.root ${base_dir}
mv log*.txt ${base_dir}

cd ${base_dir}

printf "\n\n ls output\n"
ls -l
