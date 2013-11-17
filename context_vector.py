#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, codecs
from xml.dom.minidom import parse
import math
import tempfile


#############
#PARAMETERS#
###########

#texts
SRCFILE = "./ziggurat/data/corpus_breast_cancer/tmp_sc_fr/corpus.lem.utf8.tmp"
TARGFILE = "./ziggurat/data/corpus_breast_cancer/tmp_sc_en/corpus.lem.utf8.tmp"

#used to store a clean version of the texts (stopwords removed, etc...)
#these files will be created by this program.
SRCCLEAN = "./src_clean.txt"
TARGCLEAN = "./targ_clean.txt"

#lists of stopwords
SRCSTOPWORDS = "./src_stopwords.txt"
TARGSTOPWORDS = "./targ_stopwords.txt"

#bilingual dictionnary
DICFILE = "./ziggurat/dico/elra_utf8.final"

#XML file with translations
GOLDFILE = "./ziggurat/data/corpus_breast_cancer/ts.xml"

############
#FUNCTIONS#
##########

def importdictFromFile(filename):
    srcdict = dict()
    with codecs.open(filename, "r", "utf-8")  as dicfile:
        for line in dicfile.readlines():
            linecontent = line.split("::")
            if not linecontent[0] in srcdict:
                srcdict[linecontent[0]] = [linecontent[1]]
            else:
                srcdict[linecontent[0]].append(linecontent[1])
    return srcdict


def importdictFromFileInv(filename):
    srcdict = dict()
    with codecs.open(filename, "r", "utf-8")  as dicfile:
        for line in dicfile.readlines():
            linecontent = line.split("::")
            if not linecontent[1] in srcdict:
                srcdict[linecontent[1]] = [linecontent[0]]
            else:
                srcdict[linecontent[1]].append(linecontent[0])
    return srcdict

#removes stopwords and some punctuations
def cleanText(filename, stopwordsfile, newfilename):
    stopwords = dict()
    with codecs.open(filename, "r", "utf-8") as textcontent:
        with codecs.open(stopwordsfile, "r", "utf-8") as stopwordscontent:
            with codecs.open(newfilename, "w", "utf-8") as resfile:
                for stopword in stopwordscontent.readlines():
                    stopwords[stopword[0:-1]] = 1
                for line in textcontent.readlines():
                    res = ""
                    for word in line.split():
                        lemma = getLemma(word)
                        if lemma not in stopwords.keys() and lemma not in [',', "'", ';', ':', '_'] and not lemma.isdigit():
                            res += word.lower() + " "
                    resfile.write(res + "\n")

    tmpfile = tempfile.NamedTemporaryFile()
    with codecs.open(newfilename, "r", "utf-8") as cleantext:
        tmpfile.write(bytes(cleantext.read(), "utf-8"))
    
    with codecs.open(newfilename, "r", "utf-8") as redofile:
        print("Start apax")
        pairs = {}
        for line in redofile.readlines():
            for word in line.split():
                if word in pairs:
                    pairs[word] += 1
                else:
                    pairs[word] = 1
    print("Apax found")
    with codecs.open(newfilename, "w", "utf-8") as reredofile:
        tmpfile.seek(0)
        for line in tmpfile.readlines():
            res = ""
            for word in line.split():
                if pairs[word.decode("utf-8")] > 1 :
                    res += word.decode("utf-8") + " "
            reredofile.write(res + "\n")
    tmpfile.close()
    
#returns a list of every word that doesn't have a translation in the dictionnary
def findmissingtranslations(srcfilename, srcdic):
    wordstotrans = list()
    with codecs.open(srcfilename, "r", "utf-8") as srcfile:
        for line in srcfile.readlines():
            words = line.split(" ")
            for word in words:
                fullword = getFullWord(word)
                lemma = getLemma(word)
                if fullword not in srcdic and lemma not in srcdic and fullword not in wordstotrans:
                    if not lemma.isdigit() and lemma not in [',', "'", ';', ':', '_'] and len(lemma) > 3:
                        if getPOS(word) in ['NN', 'SBC', 'ADJ', 'JJ']:
                            wordstotrans.append(fullword)
    return wordstotrans

#returns a list of the terms contained in the xml file
def getMissingTrans(cheatfile):
    res = []
    dom = parse(cheatfile)
    for node in dom.getElementsByTagName('TRAD'):
        if node.attributes['valid'].value == 'yes':
            fr = node.childNodes[1].childNodes[1].childNodes[0].data
            res.append(fr)
    return res
            
#returns the lemma of a word
def getLemma(word):
    if word.isspace() or len(word.split('/')) == 1 :
        return word
    #french punctuation
    if len(word.split('/')) == 2 :
        return word.split('/')[1]
    else:
        return word.split('/')[2].split(':')[0]

#returns the full word (getting rid of the lemma and stem)
def getFullWord(word):
    return word.split('/')[0]

#returns the Part of Speech of a term
def getPOS(word):
    return word.split('/')[1].split(':')[0]


# returns the correct translation of a term
def getGoldTrans(term, resfile):
    dom = parse(resfile)
    for node in dom.getElementsByTagName('TRAD'):
        if node.attributes['valid'].value == 'yes' and  node.childNodes[1].childNodes[1].childNodes[0].data == term:
            return node.childNodes[3].childNodes[1].childNodes[0].data

#returns the number of found translations
def checkResults(termcandidates, resfile):
    corr = 0
    wrong = 0
    for term in termcandidates:
        trans = getGoldTrans(term, resfile)
        if trans in (i for  i,_  in termcandidates[term]):
            corr += 1
        else:
            wrong += 1
    print("res = " + str(corr) + " / " + str((corr + wrong)), " -> ", corr / (corr+wrong) * 100)

#Slides the window on all the text (not limited to sentenced windows)
def createvectors_c(filename, windowsize):
    contextvector = dict()
    text = ""
    with codecs.open(filename, "r", "utf-8") as srcfile:
        for line in srcfile.readlines():
            text += line
        start = - windowsize
        end = windowsize
        words = text.split(" ")
        for word in words:
            fullword = getFullWord(word)
            lemma = getLemma(word)
            i = start
            while end > len(words) -1:
                end -= 1
            while i < end:
                i  =  0 if (i < 0) else i 
                currentwindowterm = getFullWord(words[i])
                if fullword not in contextvector:
                    contextvector[fullword] = dict()
                    contextvector[fullword][currentwindowterm] = 1
                elif currentwindowterm not in contextvector[fullword]:
                    contextvector[fullword][currentwindowterm] = 1
                else:
                    contextvector[fullword][currentwindowterm] += 1
                i += 1
            start = start + 1
            end = end if end+1 > len(words) - 1 else end +1 
                        
    return contextvector
            


#Uses a sentenced window.
def createvectors(filename, windowsize):
    contextvector = dict()
    with codecs.open(filename, "r", "utf-8") as srcfile:
        for line in srcfile.readlines():
            start = - windowsize
            end = windowsize
            words = line.split(" ")
            for word in words:
                fullword = getFullWord(word)
                lemma = getLemma(word)
                i = start
                while end > len(words) -1:
                    end -= 1
                while i < end:
                    i  =  0 if (i < 0) else i 
                    currentwindowterm = getFullWord(words[i])
                    if fullword not in contextvector:
                        contextvector[fullword] = dict()
                        contextvector[fullword][currentwindowterm] = 1
                    elif currentwindowterm not in contextvector[fullword]:
                        contextvector[fullword][currentwindowterm] = 1
                    else:
                        contextvector[fullword][currentwindowterm] += 1
                    i += 1
                start = start + 1
                end = end if end+1 > len(words) - 1 else end +1 
                        
    return contextvector

#returns the translation of a vector. If a word has no translation it is translated "???"
# this could be nefast, but the idea is that counting the number of "complicated" words
# that appear near a word isn't that stupid.
def translatevector(aVector, aDict):
    t_vector = dict()
    for entry, vector in aVector.items():
        if entry not in t_vector:
            t_vector[entry] = dict()
        for word, count in vector.items():
            if word in aDict:
                t_words = aDict[word]
            else:
                t_words = ["???"]
            for t_word in t_words:
                if t_word not in t_vector[entry]:
                    t_vector[entry][t_word] = count
                else:
                    t_vector[entry][t_word] += count
    return t_vector

#borrowed from StackOverflow answer http://stackoverflow.com/questions/15173225/how-to-calculate-cosine-similarity-given-2-sentence-strings-python
def get_cosine(vec1, vec2):
     intersection = set(vec1.keys()) & set(vec2.keys())
     numerator = sum([vec1[x] * vec2[x] for x in intersection])

     sum1 = sum([vec1[x]**2 for x in vec1.keys()])
     sum2 = sum([vec2[x]**2 for x in vec2.keys()])
     denominator = math.sqrt(sum1) * math.sqrt(sum2)

     if not denominator:
        return 0.0
     else:
         return float(numerator) / denominator

# get the list of target terms that best matches the source term vector
# nb_candidates is the size of the list
def getCandidates(word_vector, targ_src_vectors, nb_candidates):
    #initialize an "empty" result list
    reslist = [('?',0.0)] *10
    for entry, vector in targ_src_vectors.items():
        score = get_cosine(word_vector, vector)
        lscores = list((lscore for _,lscore in reslist))
        minscore = min(lscores)
        #replace the least score in the list by the new term/score pair
        if (score > minscore):
            minindex = lscores.index(minscore)
            reslist[minindex] = (entry, score)
    return reslist

def getFreq(wordlist, filename):
    res = {}
    with codecs.open(filename, "r", "utf-8") as searchfile:
        for line in searchfile.readlines():
            for word in line.split():
                word = getLemma(word)
                if word in wordlist:
                    if word in res:
                        res[word] += 1
                    else:
                        res[word] = 1
    print(res)


def main():

    #get the dict in a variable
    srcdict = importdictFromFile(DICFILE)
    targetdict = importdictFromFileInv(DICFILE)

    print("Dictionnary compiled")

    #find french words that have no translation
    #wordstotrans = findmissingtranslations("./ziggurat/data/corpus_breast_cancer/tmp_sc_fr/corpus.lem.utf8.tmp", srcdict)
    wordstotrans = getMissingTrans(GOLDFILE)
    print(len(wordstotrans), " words to translate found")
    

    #remove stopwords from files
    cleanText(SRCFILE, SRCSTOPWORDS, SRCCLEAN)
    cleanText(TARGFILE, TARGSTOPWORDS, TARGCLEAN)

    print("Cleaned texts by removing stopwords")
    
    #create the vectors
    src_vectors = createvectors_c(SRCCLEAN, 3)
    targ_vectors = createvectors_c(TARGCLEAN, 3)
    
    print("Vectors created")
    
    #translates a target vector to the source language via a dict
    targ_src_vector = translatevector(targ_vectors, targetdict)
    src_targ_vector = translatevector(src_vectors, srcdict)
    print("Target vector translated")
    
    candidates = dict()

    i=0
    #get the candidates for each word to translate
    for word in wordstotrans:
        if word in src_vectors.keys():
            i += 1
            print(i)
            candidates[word] = getCandidates(src_vectors[word] , targ_src_vector, 10)

    print("Candidates selected")

    #for word in candidates:
    #    print(word , " -> ", candidates[word])
    

    checkResults(candidates, GOLDFILE)


if __name__ == "__main__":
    main()
