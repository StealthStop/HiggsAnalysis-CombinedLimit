#include "TString.h"
#include "TFile.h"
#include "TH1F.h"
#include "TGraph.h"

void count_toys(const int nToys = 10, const TString& mass = "350", const TString& seed = "123456", const TString& path = "./")
{
    gSystem->Load("libHiggsAnalysisCombinedLimit.so");
    double max_significance_in_data = 7.35;
    TFile* sigFile = TFile::Open("higgsCombine_sig.MultiDimFit.mH"+mass+"."+seed+".root","RECREATE");
    TH1D* sigHisto = new TH1D("sig","sig",1500, 0.0, 15.0);
    TH2D* r_sigHisto = new TH2D("r_sig","r_sig",200,0.0,2.0, 1500,0.0,15.0);

    for(int itoy=1; itoy<nToys+1; itoy++)
    {
        //if(hello>=0 && itoy!=hello) continue; 
        TCanvas c("c","c",1000,500); 
        TString stoy = "toy_"; stoy+=itoy;

        Float_t deltaNLL, r;
        Double_t nll, nll0;
        TFile fbfit(path+"/higgsCombine_bfit_"+stoy+".MultiDimFit.mH"+mass+"."+seed+".root");
        TFile fscan(path+"/higgsCombine_"+stoy+".MultiDimFit.mH"+mass+"."+seed+".root");

        TTree* t = (TTree*)fbfit.Get("limit");
        t->SetBranchAddress("r",&r);
        t->SetBranchAddress("deltaNLL",&deltaNLL);
        t->SetBranchAddress("nll",&nll);
        t->SetBranchAddress("nll0",&nll0);

        double nll_bfit = 0;
        Long_t nentries = t->GetEntries();
        for (Int_t i = 0; i<1; i++) 
        {
            t->GetEntry(i);
            nll_bfit = nll+nll0;
        }
        t = (TTree*)fscan.Get("limit");
        t->SetBranchAddress("r",&r);
        t->SetBranchAddress("deltaNLL",&deltaNLL);
        t->SetBranchAddress("nll",&nll);
        t->SetBranchAddress("nll0",&nll0);

        //Calculate sig for each toy and r value
        TGraph hsignif(0);	
        hsignif.GetXaxis()->SetRangeUser(0,3);
        nentries = t->GetEntries();
        double sig_max = -1, r_max;
        for (Int_t i = 0; i<nentries; i++) 
        {
            t->GetEntry(i);
            double rel_nll = nll+nll0+deltaNLL - nll_bfit; if(rel_nll>0) rel_nll=0;
            double sig = sqrt(2*fabs(rel_nll));
            if(sig>5) continue;
            hsignif.Set(i+1);
            hsignif.SetPoint(i, r, sig);
            r_sigHisto->Fill(r, sig);
        }
        hsignif.Sort();
        for(int i=1; i< hsignif.GetN(); i++)
        {
            double x, y; hsignif.GetPoint(i, x, y);
            if(y>=sig_max)
            { 
                sig_max=y; r_max=x;
            }
        }

        //Fill the sig histo with max sig for each toy
        sigHisto->Fill(sig_max);

        //Plot sig for each toy as a function of r
        c.cd();
        TH1F htmp("htmp","htmp",100,0,3);
        htmp.SetMaximum(10);
        htmp.SetMinimum(0);
        htmp.SetTitle("; m_{X} (GeV); Q = #sqrt{-2#Delta ln L}");
        htmp.SetStats(0);
        htmp.Draw();
        hsignif.Draw("LP");
        TString ssig = TString::Format("Q_{max} = %.2f",sig_max);
        TLatex tsig;
        tsig.SetNDC();
        tsig.SetTextSize(0.06);
        if(sig_max>=max_significance_in_data) tsig.SetTextColor(kRed);
        tsig.DrawLatex(0.17,0.85, ssig.Data());

        TLine *lh = new TLine(0,max_significance_in_data, 2, max_significance_in_data);
        lh->SetLineStyle(kDashed);
        lh->Draw();

        c.SaveAs("scan_signif_"+stoy+(sig_max<max_significance_in_data?".png":"_red.png"));
        //if(hello<=0)break;
    }

    //Write output histograms
    sigFile->cd();
    sigHisto->Write();
    r_sigHisto->Write();
}
