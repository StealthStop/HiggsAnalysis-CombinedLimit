import ROOT
#from cardConfig import path,signal,background,histos,othersys,lumi

class dataCardMaker:

    def __init__(self, path, signal, background, histos, lumi, outpath, othersys):
        self.path = path
        self.signal = signal
        self.background = background
        self.histos = histos
        self.outpath = outpath
        self.othersys = othersys
        self.lumi = lumi
        self.fillBinValues()
        self.writeCards()

    def fillBinValues(self):
        self.nbins = 0
        for sg in self.signal.keys():
            binValues = []
            tfile = ROOT.TFile.Open(path+self.signal[sg]["path"])
            for hist in self.histos.keys():
                h = tfile.Get(self.histos[hist]["name"])
                histbins = h.GetNbinsX()
                skip = histbins/self.histos[hist]["nbins"] 
                for bin in range(1, histbins, skip):
                    val = round(h.Integral(bin, bin + skip), 1)
                    binValues.append(val)
            self.signal[sg]["binValues"] = binValues
        for bg in self.background.keys():
            binValues = []
            tfile = ROOT.TFile.Open(path+self.background[bg]["path"])
            for hist in self.histos.keys():
                h = tfile.Get(self.histos[hist]["name"])
                histbins = h.GetNbinsX()
                skip = histbins/self.histos[hist]["nbins"]
                for bin in range(1, histbins, skip):
                    val = round(h.Integral(bin, bin + skip), 1)
                    binValues.append(val)
            self.background[bg]["binValues"] = binValues
        for hist in self.histos.keys():
            self.nbins += histos[hist]["nbins"]
        self.observedPerBin = []        
        for n in range(self.nbins):
            obs = 0
            for sg in self.signal.keys():
                obs += self.signal[sg]["binValues"][n]
            for bg in self.background.keys():
                obs += self.background[bg]["binValues"][n]
            self.observedPerBin.append(obs)
            

    def writeCards(self):

        with open(self.outpath, "w") as file:
            file.write("imax {} \n".format(self.nbins))
            file.write("jmax {} \n".format(len(self.background.keys())))
            file.write("kmax * \n")
            file.write("\n------------------------")
            bin_str = "{0:<15}".format("\nbin")
            for bin in range(self.nbins):
                temp_str = "D{}".format(bin)
                bin_str += "{0:<12}".format(temp_str)
            file.write(bin_str)
            obs_str = "{0:<15}".format("\nobservation")
            for obs in range(self.nbins):
                obs_str += "{0:<12}".format(self.observedPerBin[obs])
            file.write(obs_str)
            file.write("\n--------------------------")
            pbin_str = "{0:<15}".format("\nbin")
            process1_str = "{0:<15}".format("\nprocess")
            process2_str = "{0:<15}".format("\nprocess")
            rate_str = "{0:<15}".format("\nrate")
            for bin in range(self.nbins):
                for proc in self.signal.keys():
                    temp_str = "D{}".format(bin)
                    pbin_str += "{0:<12}".format(temp_str)
                    process1_str += "{0:<12}".format(proc)
                    process2_str += "{0:<12}".format(0)
                    rate_str += "{0:<12}".format(self.signal[proc]["binValues"][bin])
                cnt = 1
                for proc in self.background.keys():
                    cnt += 1
                    temp_str = "D{}".format(bin)
                    pbin_str += "{0:<12}".format(temp_str)
                    process1_str += "{0:<12}".format(proc)
                    process2_str += "{0:<12}".format(cnt)
                    rate_str += "{0:<12}".format(self.background[proc]["binValues"][bin])
            file.write(pbin_str)
            file.write(process1_str)
            file.write(process2_str)
            file.write(rate_str)
            process2_str = "{0:<15}".format("\nprocess")
            file.write("\n--------------------------")
            lumi_str = "{0:<15}".format("\nlumi")
            for bin in range(self.nbins):
                for proc in range(len(self.signal.keys()) + len(self.background.keys())):
                    lumi_str += "{0:<12}".format(1.02)
            file.write(lumi_str)
            for signal1 in self.signal.keys():
                sig_str = "{0:<8}".format("\n"+signal1)
                sig_str += "{0:<7}".format("lnN")
                for bin in range(self.nbins):
                    for signal2 in self.signal.keys():
                        if signal1 == signal2:
                            sig_str += "{0:<12}".format(self.signal[signal1]["sys"])
                        else:
                            sig_str += "{0:<12}".format("--")
                file.write(sig_str)
            for background1 in self.background.keys():
                bg_str = "{0:<8}".format("\n"+background1)
                bg_str += "{0:<7}".format("lnN")
                bg_str += "{0:<12}".format("--")*len(self.signal.keys())                
                for bin in range(self.nbins):
                    for background2 in self.background.keys():
                        if background1 == background2:
                            bg_str += "{0:<12}".format(self.background[background1]["sys"])
                        else:
                            bg_str += "{0:<12}".format("--")
                file.write(bg_str)
            if self.othersys:
                for sys in self.othersys.keys():
                    sys_str = "{0:<8}".format("\n"+sys)
                    sys_str += "{0:<7}".format(self.othersys[sys]["distr"])
                    for bin in range(self.nbins):
                        for sg in self.signal.keys():
                            if sg in self.othersys[sys]["apply"]:
                                sys_str += "{0:<12}".format(self.othersys[sys]["sys"])
                            else:
                                sys_str += "{0:<12}".format("--")
                        for bg in self.background.keys():
                            if bg in self.othersys[sys]["apply"]:
                                sys_str += "{0:<12}".format(self.othersys[sys]["sys"])
                            else:
                                sys_str += "{0:<12}".format("--")
                    file.write(sys_str)
                    
#dataCardMaker(path, signal, background, histos, lumi, "datacard.txt", othersys)

