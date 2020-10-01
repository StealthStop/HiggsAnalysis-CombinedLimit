#!/usr/bin/env python
import re
from sys import argv, stdout, stderr, exit
import datetime
from optparse import OptionParser
import HiggsAnalysis.CombinedLimit.calculate_pulls as CP 

# tool to compare fitted nuisance parameters to prefit values.
#
# Also used to check for potential problems in RooFit workspaces to be used with combine
# (see https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsWG/HiggsPAGPreapprovalChecks)

# import ROOT with a fix to get batch mode (http://root.cern.ch/phpBB3/viewtopic.php?t=3198)
hasHelp = False
for X in ("-h", "-?", "--help"):
    if X in argv:
        hasHelp = True
        argv.remove(X)
argv.append( '-b-' )
import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat("")
#ROOT.gSystem.Load("libHiggsAnalysisCombinedLimit")
argv.remove( '-b-' )
if hasHelp: argv.append("-h")

parser = OptionParser(usage="usage: %prog [options] in.root  \nrun with --help to get list of options")
parser.add_option("--vtol", "--val-tolerance", dest="vtol", default=0.30, type="float", help="Report nuisances whose value changes by more than this amount of sigmas")
parser.add_option("--stol", "--sig-tolerance", dest="stol", default=0.10, type="float", help="Report nuisances whose sigma changes by more than this amount")
parser.add_option("--vtol2", "--val-tolerance2", dest="vtol2", default=2.0, type="float", help="Report severely nuisances whose value changes by more than this amount of sigmas")
parser.add_option("--stol2", "--sig-tolerance2", dest="stol2", default=0.50, type="float", help="Report severely nuisances whose sigma changes by more than this amount")
parser.add_option("-a", "--all",      dest="show_all_parameters",    default=False,  action="store_true", help="Print all nuisances, even the ones which are unchanged w.r.t. pre-fit values.")
parser.add_option("-A", "--abs",      dest="absolute_values",    default=False,  action="store_true", help="Report also absolute values of nuisance values and errors, not only the ones normalized to the input sigma")
parser.add_option("-p", "--poi",      dest="poi",    default="r",    type="string",  help="Name of signal strength parameter (default is 'r' as per text2workspace.py)")
parser.add_option("-f", "--format",   dest="format", default="text", type="string",  help="Output format ('text', 'latex', 'twiki'")
parser.add_option("-g", "--histogram", dest="plotfile", default=None, type="string", help="If true, plot the pulls of the nuisances to the given file.")
parser.add_option("", "--pullDef",  dest="pullDef", default="", type="string", help="Choose the definition of the pull, see python/calculate_pulls.py for options")
parser.add_option("--approved",      dest="approved",    default=False,  action="store_true", help="Plot is approved, no preliminary")

(options, args) = parser.parse_args()
if len(args) == 0:
    parser.print_usage()
    exit(1)

if options.pullDef!="" and options.pullDef not in CP.allowed_methods(): exit("Method %s not allowed, choose one of [%s]"%(options.pullDef,",".join(CP.allowed_methods())))

if options.pullDef and options.absolute_values : 
    print "Pulls are always defined as absolute, will modify --absolute_values to False for you"
    options.absolute_values = False 

if options.pullDef : options.show_all_parameters=True

setUpString = "diffNuisances run on %s, at %s with the following options ... "%(args[0],datetime.datetime.utcnow())+str(options)

file = ROOT.TFile(args[0])
if file == None: raise RuntimeError, "Cannot open file %s" % args[0]
fit_s  = file.Get("fit_s")
fit_b  = file.Get("fit_b")
prefit = file.Get("nuisances_prefit")
if fit_s == None or fit_s.ClassName()   != "RooFitResult": raise RuntimeError, "File %s does not contain the output of the signal fit 'fit_s'"     % args[0]
if fit_b == None or fit_b.ClassName()   != "RooFitResult": raise RuntimeError, "File %s does not contain the output of the background fit 'fit_b'" % args[0]
if prefit == None or prefit.ClassName() != "RooArgSet":    raise RuntimeError, "File %s does not contain the prefit nuisances 'nuisances_prefit'"  % args[0]

isFlagged = {}

# maps from nuisance parameter name to the row to be printed in the table
table = {}

# get the fitted parameters
fpf_b = fit_b.floatParsFinal()
fpf_s = fit_s.floatParsFinal()

pulls = []

nuis_p_i=0
title = "pull" if options.pullDef else "#theta"

# Also make histograms for pull distributions:
hist_fit_b  = ROOT.TH1F("fit_b"   ,"B-only fit Nuisances;;%s "%title,prefit.getSize(),0,prefit.getSize())
hist_fit_s  = ROOT.TH1F("fit_s"   ,"S+B fit Nuisances   ;;%s "%title,prefit.getSize(),0,prefit.getSize())
hist_prefit = ROOT.TH1F("prefit_nuisancs","Prefit Nuisances    ;;%s "%title,prefit.getSize(),0,prefit.getSize())
# Store also the *asymmetric* uncertainties
gr_fit_b    = ROOT.TGraphAsymmErrors(); gr_fit_b.SetTitle("fit_b_g")
gr_fit_s    = ROOT.TGraphAsymmErrors(); gr_fit_s.SetTitle("fit_b_s")


# loop over all fitted parameters
nuis_list = []
for i in range(fpf_s.getSize()):

    nuis_s = fpf_s.at(i)
    name   = nuis_s.GetName();
    nuis_b = fpf_b.find(name)
    nuis_p = prefit.find(name)

    # keeps information to be printed about the nuisance parameter
    row = []

    flag = False;
    mean_p, sigma_p, sigma_pu, sigma_pd = 0,0,0,0

    if nuis_p == None:
        # nuisance parameter NOT present in the prefit result
        if not options.absolute_values and not (options.pullDef=="unconstPullAsym"): continue
        row += [ "[%.6f, %.6f]" % (nuis_s.getMin(), nuis_s.getMax()) ]

    else:
        nuis_list.append({"name" : name, "bobj" : nuis_b, "sobj" : nuis_s, "bval" : nuis_b.getVal(), "sval" : nuis_s.getVal()})

        # get best-fit value and uncertainty at prefit for this 
        # nuisance parameter
        if nuis_p.getErrorLo()==0: nuis_p.setError(nuis_p.getErrorHi())
        mean_p, sigma_p, sigma_pu,sigma_pd = (nuis_p.getVal(), nuis_p.getError(),nuis_p.getErrorHi(),nuis_p.getErrorLo())

        if not sigma_p > 0: sigma_p = (nuis_p.getMax()-nuis_p.getMin())/2
        nuisIsSymm = abs(abs(nuis_p.getErrorLo())-abs(nuis_p.getErrorHi()))<0.01 or nuis_p.getErrorLo() == 0
        if options.absolute_values: 
            if nuisIsSymm : row += [ "%.6f +/- %.6f" % (nuis_p.getVal(), nuis_p.getError()) ]
            else: row += [ "%.6f +%.6f %.6f" % (nuis_p.getVal(), nuis_p.getErrorHi(), nuis_p.getErrorLo()) ]

nuis_list = sorted(nuis_list, key=lambda i: abs(i["bval"]), reverse=True)

bchi2 = 0.0; sbchi2 = 0.0
for d in nuis_list:
    name = d["name"]; 
    print name, nuis_p_i
    nuis_b = d["bobj"]; nuis_s = d["sobj"]

    for fit_name, nuis_x in [('b', nuis_b), ('s',nuis_s)]:
        if nuis_x == None: row += [ " n/a " ]
        else: 
            nuisIsSymm = abs(abs(nuis_x.getErrorLo())-abs(nuis_x.getErrorHi()))<0.01 or nuis_x.getErrorLo() == 0
    
            if nuisIsSymm : nuis_x.setError(nuis_x.getErrorHi())
            nuiselo = abs(nuis_x.getErrorLo()) if nuis_x.getErrorLo()>0 else nuis_x.getError()
            nuisehi = nuis_x.getErrorHi()
            if options.pullDef and nuis_p!=None: nx,ned,neu = CP.returnPullAsym(options.pullDef,nuis_x.getVal(),mean_p,nuisehi,sigma_pu,abs(nuiselo),abs(sigma_pd))
            else: nx,ned,neu = nuis_x.getVal(), nuiselo, nuisehi
    
            if nuisIsSymm : row += [ "%+.6f +/- %.6f" % (nx, (abs(ned)+abs(neu))/2) ]
            else: row += [ "%+.6f +%.6f %.6f" % (nx, neu, ned) ]
    
            if nuis_p != None:
                if options.plotfile: 
                    if fit_name=='b':
                        nuis_p_i+=1
                        if options.pullDef and nuis_p!=None:
                            #nx,ned,neu = CP.returnPullAsym(options.pullDef,nuis_x.getVal(),mean_p,nuis_x.getErrorHi(),sigma_pu,abs(nuis_x.getErrorLo()),abs(sigma_pd))
                            gr_fit_b.SetPoint(nuis_p_i-1,nuis_p_i-0.5+0.1,nx)
                            gr_fit_b.SetPointError(nuis_p_i-1,0,0,ned,neu)
                        else:
                            if "d_" != name[0:2]:
                                if nuis_x.getVal() > 0:
                                    bchi2 += (nuis_x.getVal() / nuis_x.getErrorLo())**2.0
                                else:
                                    bchi2 += (nuis_x.getVal() / nuis_x.getErrorHi())**2.0

                            gr_fit_b.SetPoint(nuis_p_i-1,nuis_p_i-0.5+0.1,nuis_x.getVal())
                            gr_fit_b.SetPointError(nuis_p_i-1,0,0,abs(nuis_x.getErrorLo()),nuis_x.getErrorHi())
                        hist_fit_b.SetBinContent(nuis_p_i,nuis_x.getVal())
                        hist_fit_b.SetBinError(nuis_p_i,nuis_x.getError())
                        hist_fit_b.GetXaxis().SetBinLabel(nuis_p_i,name)
                        gr_fit_b.GetXaxis().SetBinLabel(nuis_p_i,name)
                    if fit_name=='s':
                        if options.pullDef and nuis_p!=None:
                            #nx,ned,neu = CP.returnPullAsym(options.pullDef,nuis_x.getVal(),mean_p,nuis_x.getErrorHi(),sigma_pu,abs(nuis_x.getErrorLo()),abs(sigma_pd))
                            gr_fit_s.SetPoint(nuis_p_i-1,nuis_p_i-0.5-0.1,nx)
                            gr_fit_s.SetPointError(nuis_p_i-1,0,0,ned,neu)
                        else:
                            if "d_" != name[0:2]:
                                if nuis_x.getVal() > 0:
                                    sbchi2 += (nuis_x.getVal() / nuis_x.getErrorLo())**2.0
                                else:
                                    sbchi2 += (nuis_x.getVal() / nuis_x.getErrorHi())**2.0

                            gr_fit_s.SetPoint(nuis_p_i-1,nuis_p_i-0.5-0.1,nuis_x.getVal())
                            gr_fit_s.SetPointError(nuis_p_i-1,0,0,abs(nuis_x.getErrorLo()),nuis_x.getErrorHi())
                            hist_fit_s.SetBinContent(nuis_p_i,nuis_x.getVal())
                            hist_fit_s.SetBinError(nuis_p_i,nuis_x.getError())
                            hist_fit_s.GetXaxis().SetBinLabel(nuis_p_i,name)
                            gr_fit_s.GetXaxis().SetBinLabel(nuis_p_i,name)
    
                    hist_prefit.SetBinContent(nuis_p_i,mean_p)
                    hist_prefit.SetBinError(nuis_p_i,sigma_p)

                    hist_prefit.GetXaxis().SetBinLabel(nuis_p_i,name.replace("np_", ""))
                    hist_prefit.GetXaxis().SetBinLabel(nuis_p_i,name.replace("np_", ""))

                    if "Combo" not in file.GetName():
                        hist_prefit.GetXaxis().SetBinLabel(nuis_p_i,name.replace("_2016", "").replace("_2017", "").replace("_2018pre", "").replace("_2018post", "").replace("_2018", "").replace("np_", ""))
                        hist_prefit.GetXaxis().SetBinLabel(nuis_p_i,name.replace("_2016", "").replace("_2017", "").replace("_2018pre", "").replace("_2018post", "").replace("_2018", "").replace("np_", ""))

                    #hist_prefit.GetXaxis().LabelsOption("v")
    
                if sigma_p>0: 
                    if options.pullDef:
                        valShift = nx 
                        sigShift = 1
                    else: 
                        # calculate the difference of the nuisance parameter
                        # w.r.t to the prefit value in terms of the uncertainty
                        # on the prefit value
                        valShift = (nuis_x.getVal() - mean_p)/sigma_p
    
                        # ratio of the nuisance parameter's uncertainty
                        # w.r.t the prefit uncertainty
                        sigShift = nuis_x.getError()/sigma_p
    
                else :
                    #print "No definition for prefit uncertainty %s. Printing absolute shifts"%(nuis_p.GetName())
                    valShift = (nuis_x.getVal() - mean_p)
                    sigShift = nuis_x.getError()
    
                if options.pullDef: row[-1] += ""
                elif options.absolute_values: row[-1] += " (%+4.2fsig, %4.2f)" % (valShift, sigShift)
                else: row[-1] = " %+4.2f, %4.2f" % (valShift, sigShift)
                    
                if fit_name == 'b':
                    pulls.append(valShift)
    
                if (abs(valShift) > options.vtol2 or abs(sigShift-1) > options.stol2):
    
                    # severely report this nuisance:
                    # 
                    # the best fit moved by more than 2.0 sigma or the uncertainty (sigma)
                    # changed by more than 50% (default thresholds) w.r.t the prefit values
    
                    isFlagged[(name,fit_name)] = 2
    
                    flag = True
    
                elif (abs(valShift) > options.vtol  or abs(sigShift-1) > options.stol):
    
                    # report this nuisance:
                    # 
                    # the best fit moved by more than 0.3 sigma or the uncertainty (sigma)
                    # changed by more than 10% (default thresholds) w.r.t the prefit values
    
                    if options.show_all_parameters: isFlagged[(name,fit_name)] = 1
    
                    flag = True
    
                elif options.show_all_parameters:
                    flag = True
    
    # end of loop over s and b
    
    row += [ "%+4.2f"  % fit_s.correlation(name, options.poi) ]
    if flag or options.show_all_parameters: table[name] = row

#end of loop over all fitted parameters

#----------
# print the results
#----------

#print details
#print setUpString

fmtstring = "%-40s     %15s    %15s  %10s"
highlight = "*%s*"
morelight = "!%s!"
pmsub, sigsub = None, None
if options.format == 'text':
    if options.pullDef:
        fmtstring = "%-40s       %30s    %30s  %10s"
        print fmtstring % ('name',  'b-only fit pull', 's+b fit pull', 'rho')
    elif options.absolute_values:
        fmtstring = "%-40s     %15s    %30s    %30s  %10s"
        print fmtstring % ('name', 'pre fit', 'b-only fit', 's+b fit', 'rho')
    else:
        print fmtstring % ('name', 'b-only fit', 's+b fit', 'rho')
elif options.format == 'latex':
    pmsub  = (r"(\S+) \+/- (\S+)", r"$\1 \\pm \2$")
    sigsub = ("sig", r"$\\sigma$")
    highlight = "\\textbf{%s}"
    morelight = "{{\\color{red}\\textbf{%s}}}"
    if options.pullDef:
        fmtstring = "%-40s & %30s & %30s & %6s \\\\"
        print "\\begin{tabular}{|l|r|r|r|} \\hline ";
        print (fmtstring % ('name', '$b$-only fit pull', '$s+b$ fit pull', r'$\rho(\theta, \mu)$')), " \\hline"
    elif options.absolute_values:
        fmtstring = "%-40s &  %15s & %30s & %30s & %6s \\\\"
        print "\\begin{tabular}{|l|r|r|r|r|} \\hline ";
        print (fmtstring % ('name', 'pre fit', '$b$-only fit', '$s+b$ fit', r'$\rho(\theta, \mu)$')), " \\hline"
    else:
        fmtstring = "%-40s &  %15s & %15s & %6s \\\\"
        print "\\begin{tabular}{|l|r|r|r|} \\hline ";
        #what = r"$(x_\text{out} - x_\text{in})/\sigma_{\text{in}}$, $\sigma_{\text{out}}/\sigma_{\text{in}}$"
        what = r"\Delta x/\sigma_{\text{in}}$, $\sigma_{\text{out}}/\sigma_{\text{in}}$"
        print  fmtstring % ('',     '$b$-only fit', '$s+b$ fit', '')
        print (fmtstring % ('name', what, what, r'$\rho(\theta, \mu)$')), " \\hline"
elif options.format == 'twiki':
    pmsub  = (r"(\S+) \+/- (\S+)", r"\1 &plusmn; \2")
    sigsub = ("sig", r"&sigma;")
    highlight = "<b>%s</b>"
    morelight = "<b style='color:red;'>%s</b>"
    if options.pullDef:
        fmtstring = "| <verbatim>%-40s</verbatim>  | %-30s  | %-30s   | %-15s  |"
        print "| *name* | *b-only fit pull* | *s+b fit pull* | "
    elif options.absolute_values:
        fmtstring = "| <verbatim>%-40s</verbatim>  | %-15s  | %-30s  | %-30s   | %-15s  |"
        print "| *name* | *pre fit* | *b-only fit* | *s+b fit* | "
    else:
        fmtstring = "| <verbatim>%-40s</verbatim>  | %-15s  | %-15s | %-15s  |"
        print "| *name* | *b-only fit* | *s+b fit* | *corr.* |"
elif options.format == 'html':
    pmsub  = (r"(\S+) \+/- (\S+)", r"\1 &plusmn; \2")
    sigsub = ("sig", r"&sigma;")
    highlight = "<b>%s</b>"
    morelight = "<strong>%s</strong>"
    print """
<html><head><title>Comparison of nuisances</title>
<style type="text/css">
    td, th { border-bottom: 1px solid black; padding: 1px 1em; }
    td { font-family: 'Consolas', 'Courier New', courier, monospace; }
    strong { color: red; font-weight: bolder; }
</style>
</head><body style="font-family: 'Verdana', sans-serif; font-size: 10pt;"><h1>Comparison of nuisances</h1>
<table>
"""
    if options.pullDef:
        print "<tr><th>nuisance</th><th>background fit pull </th><th>signal fit pull</th><th>correlation</th></tr>"
        fmtstring = "<tr><td><tt>%-40s</tt> </td><td> %-30s </td><td> %-30s </td><td> %-15s </td></tr>"
    elif options.absolute_values:
        print "<tr><th>nuisance</th><th>pre fit</th><th>background fit </th><th>signal fit</th><th>correlation</th></tr>"
        fmtstring = "<tr><td><tt>%-40s</tt> </td><td> %-15s </td><td> %-30s </td><td> %-30s </td><td> %-15s </td></tr>"
    else:
        what = "&Delta;x/&sigma;<sub>in</sub>, &sigma;<sub>out</sub>/&sigma;<sub>in</sub>";
        print "<tr><th>nuisance</th><th>background fit<br/>%s </th><th>signal fit<br/>%s</th><th>&rho;(&mu;, &theta;)</tr>" % (what,what)
        fmtstring = "<tr><td><tt>%-40s</tt> </td><td> %-15s </td><td> %-15s </td><td> %-15s </td></tr>"

names = table.keys()
names.sort()
highlighters = { 1:highlight, 2:morelight };
for n in names:
    v = table[n]
    if pmsub  != None: v = [ re.sub(pmsub[0],  pmsub[1],  i) for i in v ]
    if sigsub != None: v = [ re.sub(sigsub[0], sigsub[1], i) for i in v ]
    if (n,'b') in isFlagged: v[-3] = highlighters[isFlagged[(n,'b')]] % v[-3]
    if (n,'s') in isFlagged: v[-2] = highlighters[isFlagged[(n,'s')]] % v[-2]
    if options.format == "latex": n = n.replace(r"_", r"\_")
    #if options.absolute_values:
    #   print fmtstring % (n, v[0], v[1], v[2], v[3])
    #else:
    #   print fmtstring % (n, v[0], v[1], v[2])

if options.format == "latex":
    print " \\hline\n\end{tabular}"
elif options.format == "html":
    print "</table></body></html>"


if options.plotfile:
    import ROOT
    fout = ROOT.TFile(options.plotfile,"RECREATE")
    ROOT.gROOT.SetStyle("Plain")
    ROOT.gStyle.SetOptFit(1)
    histogram = ROOT.TH1F("pulls", "Pulls", 60, -3, 3)
    for pull in pulls:
        histogram.Fill(pull)
    canvas = ROOT.TCanvas("asdf", "asdf", 800, 800)
    if options.pullDef : histogram.GetXaxis().SetTitle("pull")
    else: histogram.GetXaxis().SetTitle("(#theta-#theta_{0})/#sigma_{pre-fit}")
    histogram.SetTitle("Post-fit nuisance pull distribution")
    histogram.SetMarkerStyle(20)
    histogram.SetMarkerSize(2)
    histogram.Draw("pe")
    fout.WriteTObject(canvas)
    canvas.SaveAs("PostFit_Pulls.pdf")

    year = ""; tag = ""; data = True
    if "pseudo" in file.GetName():
        data = False
    if   "2016"     in file.GetName():
        year = "2016"
        tag = year
    elif "2017"     in file.GetName():
        year = "2017"
        tag = year
    elif "2018pre"  in file.GetName():
        year = "2018A"
        tag = year
    elif "2018post" in file.GetName():
        year = "2018B"
        tag = year
    elif "Combo"    in file.GetName():
        year = "137.2 fb^{-1} (13 TeV)"
        tag = "Combo"

    canvas_nuis = ROOT.TCanvas("nuisances", "nuisances", 1800, 800)
    canvas_nuis.Divide(1,2); canvas_nuis.cd(1)
    XMin = 0;    XMax = 1; RatioXMin = 0; RatioXMax = 1 
    YMin = 0.529; YMax = 1; RatioYMin = 0; RatioYMax = 0.529
    PadFactor = (YMax-YMin) / (RatioYMax-RatioYMin)
    ROOT.gPad.SetPad(XMin, YMin, XMax, YMax)

    deltaPull = ROOT.TGraph()
    x1 = ROOT.Double(0.0); y1 = ROOT.Double(0.0)
    x2 = ROOT.Double(0.0); y2 = ROOT.Double(0.0)
    for i in xrange(0, gr_fit_b.GetN()):
        gr_fit_b.GetPoint(i, x1, y1)
        gr_fit_s.GetPoint(i, x2, y2) 
        deltaPull.SetPoint(i, (x1+x2)/2.0, y2-y1)

    hist_fit_e_s = hist_fit_s.Clone("errors_s")
    hist_fit_e_b = hist_fit_b.Clone("errors_b")
    #gr_fit_s = getGraph(hist_fit_s,-0.1)
    #gr_fit_b = getGraph(hist_fit_b, 0.1)
    fuchsia = ROOT.TColor.GetColor("#88258C")
    cornblue = ROOT.TColor.GetColor("#5CB4E8")
    gr_fit_s.SetLineColor(cornblue)
    gr_fit_s.SetMarkerColor(cornblue)
    gr_fit_b.SetLineColor(fuchsia)
    gr_fit_b.SetMarkerColor(fuchsia)
    deltaPull.SetLineColor(ROOT.kRed)
    deltaPull.SetMarkerColor(ROOT.kRed)
    gr_fit_b.SetMarkerStyle(20)
    gr_fit_s.SetMarkerStyle(20)
    deltaPull.SetMarkerStyle(20)
    gr_fit_b.SetMarkerSize(2.0)
    gr_fit_s.SetMarkerSize(2.0)
    deltaPull.SetMarkerSize(2.0)
    gr_fit_b.SetLineWidth(2)
    gr_fit_s.SetLineWidth(2)
    deltaPull.SetLineWidth(2)
    hist_prefit.SetLineWidth(2)
    hist_prefit.GetYaxis().SetTitleSize(0.1)
    hist_prefit.GetYaxis().SetTitleOffset(0.2)
    hist_prefit.GetYaxis().SetLabelSize(0.07)
    hist_prefit.GetXaxis().SetLabelSize(0.075)
    hist_prefit.GetXaxis().SetLabelOffset(0.012)
    hist_prefit.GetYaxis().SetTitle("N.P. Pull")
    hist_prefit.SetTitle("")
    hist_prefit.SetLineColor(ROOT.kBlack)
    hist_prefit.SetFillColor(ROOT.kGray)
    hist_prefit.SetMaximum(3.5)
    hist_prefit.SetMinimum(-3.5)
    hist_prefit.GetXaxis().SetRangeUser(1.0,26.0)
    if "Combo" in file.GetName(): hist_prefit.GetXaxis().SetRangeUser(4.0, 29.0)
    dummyPull = hist_prefit.Clone("dummyPull")
    dummyPull.Reset("ICESM")
    dummyPull.GetYaxis().SetRangeUser(-3.5,3.5)

    hist_prefit.Draw("E2")
    hist_prefit.Draw("histsame")
    gr_fit_b.Draw("EPsame")
    gr_fit_s.Draw("EPsame")
    ROOT.gPad.SetGridx()
    ROOT.gPad.RedrawAxis()
    ROOT.gPad.RedrawAxis('g')

    cmstext = ROOT.TLatex()
    cmstext.SetNDC(True)

    cmstext.SetTextAlign(31)
    cmstext.SetTextSize(0.070)
    cmstext.SetTextFont(42)
    cmstext.DrawLatex(1 - ROOT.gPad.GetRightMargin() + 0.08, 1 - (ROOT.gPad.GetTopMargin() - 0.017), year)

    np1 = ROOT.TPaveText(0.70,0.78,0.83,0.88, "NDC")
    np1.AddText("B-only N.P. #chi^{2} = %3.2f"%(bchi2))
    np1.SetTextAlign(31)
    np1.SetTextSize(0.07)
    np1.SetTextFont(62)
    np1.SetFillColor(ROOT.kWhite)
    np1.SetTextColor(fuchsia)
    np1.Draw("SAME")
    np2 = ROOT.TPaveText(0.70,0.70,0.83,0.80, "NDC")
    np2.AddText("S+B N.P. #chi^{2} = %3.2f"%(sbchi2))
    np2.SetTextSize(0.07)
    np2.SetTextAlign(31)
    np2.SetTextFont(62)
    np2.SetFillColor(ROOT.kWhite)
    np2.SetTextColor(cornblue)
    np2.Draw("SAME")

    #cmstext.SetTextAlign(31)
    #cmstext.SetTextFont(62)
    #cmstext.DrawLatex(0.83, 0.83, "#color[%d]{B-only NP #chi^{2} = %3.2f}"%(fuchsia, bchi2))
    #cmstext.DrawLatex(0.83, 0.75, "#color[%d]{S+B NP #chi^{2} = %3.2f}"%(cornblue, sbchi2))
    mark = ROOT.TLatex()
    mark.SetNDC(True)

    mark.SetTextAlign(11);
    mark.SetTextSize(0.065);
    mark.SetTextFont(61);
    mark.DrawLatex(-0.05 + ROOT.gPad.GetLeftMargin(), 1 - (ROOT.gPad.GetTopMargin() - 0.02), "CMS")
    mark.SetTextFont(52);
    if data:
        mark.DrawLatex(-0.05 + ROOT.gPad.GetLeftMargin() + 0.03, 1 - (ROOT.gPad.GetTopMargin() - 0.02), "Supplementary")
    else:
        if not options.approved: 
            mark.DrawLatex(-0.05 + ROOT.gPad.GetLeftMargin() + 0.03, 1 - (ROOT.gPad.GetTopMargin() - 0.02), "Simulation Supplementary")
        else:
            mark.DrawLatex(-0.05 + ROOT.gPad.GetLeftMargin() + 0.03, 1 - (ROOT.gPad.GetTopMargin() - 0.02), "Simulation")
      

    leg=ROOT.TLegend(0.85,0.7,0.94,0.89)
    leg.SetFillColor(0)
    leg.SetTextFont(42)
    leg.AddEntry(hist_prefit,"Prefit","FL")
    leg.AddEntry(gr_fit_b,"B-only fit","EPL")
    leg.AddEntry(gr_fit_s,"S+B fit"   ,"EPL")
    leg.Draw()
    fout.WriteTObject(canvas_nuis)
    ROOT.gPad.SetTopMargin(0.1)
    ROOT.gPad.SetBottomMargin(0.00)
    ROOT.gPad.SetRightMargin(0.02)
    ROOT.gPad.SetLeftMargin(0.05)

    canvas_nuis.cd(2)
    ROOT.gPad.SetPad(RatioXMin, RatioYMin, RatioXMax, RatioYMax)
    ROOT.gPad.SetTopMargin(0.0)
    ROOT.gPad.SetBottomMargin(0.20)
    ROOT.gPad.SetRightMargin(0.02)
    ROOT.gPad.SetLeftMargin(0.05)

    dummyPull.GetYaxis().SetTitleSize(0.10*PadFactor)
    dummyPull.GetYaxis().SetTitleOffset(0.2/PadFactor)
    dummyPull.GetYaxis().SetLabelSize(0.07*PadFactor)
    dummyPull.GetXaxis().SetLabelSize(0.075*PadFactor)
    dummyPull.GetXaxis().SetLabelOffset(0.012/PadFactor)
    dummyPull.GetYaxis().SetTitle("#Delta Pull (s+b - b)")

    dummyPull.Draw()
    deltaPull.Draw("EPsame")
    ROOT.gPad.SetGridx()

    if not options.approved:
        canvas_nuis.SaveAs("Nuisance_Pulls_%s_prelim.pdf"%(tag))
    else:
        canvas_nuis.SaveAs("Nuisance_Pulls_%s.pdf"%(tag))

    canvas_pferrs = ROOT.TCanvas("post_fit_errs", "post_fit_errs", 900, 600)
    for b in range(1,hist_fit_e_s.GetNbinsX()+1): 
        hist_fit_e_s.SetBinContent(b,hist_fit_s.GetBinError(b)/hist_prefit.GetBinError(b))
        hist_fit_e_b.SetBinContent(b,hist_fit_b.GetBinError(b)/hist_prefit.GetBinError(b))
        hist_fit_e_s.SetBinError(b,0)
        hist_fit_e_b.SetBinError(b,0)
    hist_fit_e_s.SetFillColor(ROOT.kRed)
    hist_fit_e_b.SetFillColor(ROOT.kBlue)
    hist_fit_e_s.SetBarWidth(0.4)
    hist_fit_e_b.SetBarWidth(0.4)
    hist_fit_e_b.SetBarOffset(0.45)
    hist_fit_e_b.GetYaxis().SetTitle("#sigma_{#theta}/(#sigma_{#theta} prefit)")
    hist_fit_e_b.SetTitle("Nuisance Parameter Uncertainty Reduction")
    hist_fit_e_b.SetMaximum(1.5)
    hist_fit_e_b.SetMinimum(0)
    hist_fit_e_b.Draw("bar")
    hist_fit_e_s.Draw("barsame")
    leg_rat=ROOT.TLegend(0.6,0.7,0.89,0.89)
    leg_rat.SetFillColor(0)
    leg_rat.SetTextFont(42)
    leg_rat.AddEntry(hist_fit_e_b,"B-only fit","F")
    leg_rat.AddEntry(hist_fit_e_s,"S+B fit"   ,"F")
    leg_rat.Draw()
    line_one = ROOT.TLine(0,1,hist_fit_e_s.GetXaxis().GetXmax(),1)
    line_one.SetLineColor(1); line_one.SetLineStyle(2); line_one.SetLineWidth(2)
    line_one.Draw()
    canvas_pferrs.RedrawAxis()
    canvas_pferrs.SaveAs("PostFit_Reduction.pdf")

    fout.WriteTObject(canvas_pferrs)
