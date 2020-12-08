import os

def parseSignificance(sigs):
    for s in sigs:
        os.system("rm Parsed{}".format(s))

        with open(s) as f:
            lines = f.readlines()
            words = []
            for l in lines:
                for word in l.split(" "):
                    words.append(word)
            f.close()

        with open("Parsed{}".format(s), "w") as g:
            temp = ""
            card = False
            sig = False        
            i = 0

            for word in words:
                if(word.find(".txt") != -1):
                    temp += word[:-5]
                    card = True
                if(word.find("Significance:") != -1):
                    temp += ": " + words[i + 1]
                    sig = True
                if(card and sig):
                    g.write(temp)
                    temp = ""
                    card = False
                    sig = False
                i += 1
            g.close()

if __name__ == "__main__":
    sigs = ["Significance_TopSeed_Cards.txt",
            "Significance_OldSeed_Cards.txt",
            "Significance_Njet_Cards.txt"]

    parseSignificance(sigs)   
