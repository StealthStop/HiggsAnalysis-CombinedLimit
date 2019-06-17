#!/bin/tcsh

set inputRoot2016 = $1
set inputRoot2017 = $2
set signalType = $3
set mass = $4
set year = $5
set dataType = $6
set rVal = $7
set rStep = $8
set seed = $9
set numToys = $10
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
git clone -b Chris_temp https://github.com/StealthStop/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
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
mkdir ${inputRoot2016}
xrdcp root://cmseos.fnal.gov//store/user/lpcsusyhad/StealthStop/FitInputs/${inputRoot2016}/njets_for_Aron.root     ${inputRoot2016}/.
xrdcp root://cmseos.fnal.gov//store/user/lpcsusyhad/StealthStop/FitInputs/${inputRoot2016}/ttbar_systematics.root  ${inputRoot2016}/.

mkdir ${inputRoot2017}
xrdcp root://cmseos.fnal.gov//store/user/lpcsusyhad/StealthStop/FitInputs/${inputRoot2017}/njets_for_Aron.root     ${inputRoot2017}/.
xrdcp root://cmseos.fnal.gov//store/user/lpcsusyhad/StealthStop/FitInputs/${inputRoot2017}/ttbar_systematics.root  ${inputRoot2017}/.

eval `scramv1 runtime -csh`

combineCards.py Y16=Card2016.txt Y17=Card2017.txt > CardCombo.txt
root -l -q -b 'make_MVA_8bin_ws.C("2016","'${inputRoot2016}'","'${signalType}'","'${mass}'","'${dataType}'")'
root -l -q -b 'make_MVA_8bin_ws.C("2017","'${inputRoot2017}'","'${signalType}'","'${mass}'","'${dataType}'")'
text2workspace.py Card${year}.txt -o ws_${year}_${signalType}_${mass}.root -m ${mass} --keyword-value MODEL=${signalType}

combine -M GenerateOnly ws_${year}_${signalType}_${mass}.root --toysFrequentist -m ${mass} --keyword-value MODEL=${signalType} --verbose 2 -n ${year} --saveToys --expectSignal=0 -t ${numToys} -s ${seed}

set i = 1
@ x = ( ${numToys} + 1)
while ($i < $x)
    combine -M MultiDimFit  ws_${year}_${signalType}_${mass}.root --setParameters r=0 -m ${mass} --freezeParameters r --saveNLL -D higgsCombineCombo.GenerateOnly.mH${mass}.MODEL${signalType}.${seed}.root:toys/toy_${i} -n _bfit_toy_${i} -s ${seed}
    combine -M MultiDimFit  ws_${year}_${signalType}_${mass}.root --setParameters r=0 -m ${mass} --algo=grid --setParameterRanges r=0,${rVal} --points ${rStep} --saveNLL -D higgsCombineCombo.GenerateOnly.mH${mass}.MODEL${signalType}.${seed}.root:toys/toy_${i} -n _toy_${i} -s ${seed}
    @ i++
end

root -l -b -q 'count_toys.C(${numToys},"${mass}","${seed}")'

printf "\n\n ls output\n"
ls -l

mv *.root ${base_dir}
mv log*.txt ${base_dir}

cd ${base_dir}

printf "\n\n ls output\n"
ls -l
