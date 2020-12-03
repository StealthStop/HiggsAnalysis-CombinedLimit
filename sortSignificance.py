import operator

def readFile(path):
    with open("Parsed{}".format(path)) as f:
        lines = f.readlines()
        words = []
        for l in lines:
            words.append(l.split(" "))
        for w in words:
            w[1] = float(w[1][:-1])

        f.close()
    return words

def sortBySig(words):
    return sorted(words, key=operator.itemgetter(1), reverse=True)

def sortAlpha(words):
    return sorted(words, key=operator.itemgetter(0))

def writeFile(words, s):
    with open("sorted{}".format(s), 'w') as f:
        i = 1
        for w in words:
            f.write("[" + str(i) + "] " + w[0] + " " + str(w[1]) + "\n")
            i += 1

    f.close()
def main():
    sigs = ["Significance_TopSeed_Cards.txt",
            "Significance_OldSeed_Cards.txt",
            "Significance_Njet_Cards.txt"]

    for s in sigs:
        #Read in txt file and split
        words = readFile(s)
        #Sort by largest
        words = sortBySig(words)
        #Write new file
        writeFile(words, s)

if __name__ == "__main__":
    main()
