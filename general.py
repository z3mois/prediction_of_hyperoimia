from some_help_functions import get_normal_form, wn, extractCtxW, score, cosin_distance
from tqdm import tqdm
from chekers import includeTitleInWn, unambiguousDisplay, getKeyForId, getLemmaForSynsets 
from classes import WikiSynset, display
from collections import defaultdict


def coolect_wiki_synset(pages, dictPageRedirect):
    """
        собиарем викисинсет
    """
    wiki = []
    meaningPageCounter = 0
    multiPageCounter = 0
    includeTitle = 0
    all_senses = set([' '.join([get_normal_form(w).upper() for w in s.lemma.split()]) for s in wn.senses])
    hashDict = {}
    for index in tqdm(range(len(pages)), desc='Do hash'):
        hashDict[pages[index].title.lower()] = index
    #пройтись по всем значения со страницы-значения и всем значения поставить мульти
    i = 0
    for index in tqdm(range(len(pages)),desc='Add multiPage'):
        if pages[index].meaningPage:
            for link in pages[index].links:
                if link.lower() in hashDict:
                    pages[hashDict[link.lower()]].multiPage = True
                    i += 1
    for page in tqdm(pages,desc='Create WikiSynset'):
        if page.redirect:
            if includeTitleInWn(all_senses, page.title):
                includeTitle += 1
            continue
        wikiSyn = WikiSynset(page)
        if page.title in dictPageRedirect:
            for redirect in dictPageRedirect[page.title]:
                wikiSyn.append(redirect)
        if page.meaningPage:
            meaningPageCounter += 1
        if page.multiPage:
            multiPageCounter += 1
        wiki.append(wikiSyn)
        if includeTitleInWn(all_senses, page.title):
            includeTitle += 1
    return wiki, meaningPageCounter, multiPageCounter, includeTitle
def unambiguity_resolution(wiki, dictWn):
    """
        связываем однознаннчные статьи для которых однозначен тезаурус
    """
    dictDisplay = {} # словарь отображений
    new_wiki = [] #будут все викисинсеты, кроме однозначных
    for wikisyn in tqdm(wiki, desc='unambiguity_resolution'):
        if len(wikisyn.synset) != 1:
            new_wiki.append(wikisyn)
            continue
        one = unambiguousDisplay(wikisyn.page.title)
        if  (not wikisyn.page.meaningPage) and (not wikisyn.page.multiPage) and (getKeyForId(wikisyn.page.title) in dictWn) and one[0] :
            temp = wn.get_synsets(one[1])[0].id
            dictDisplay[wikisyn.page.title] = (display(wikisyn.page.id,wikisyn.page.revid,wikisyn.page.title,one[1], temp,
                                                    extractCtxW(wikisyn.page.links, wikisyn.page.categories), wikisyn.page.first_sentence))
        else:
            new_wiki.append(wikisyn)
    return dictDisplay, new_wiki

def expanding_candidates_by_lemmas(wiki):
    """
        создаем словарь из леммы в статьи
    """
    dictLemmaInIndex = {}
    for index in tqdm(range(len(wiki)), desc= 'take more candidates for lemmas'):
        lemma = getLemmaForSynsets(wiki[index].page.title)
        if lemma != "":
            if not lemma in dictLemmaInIndex:
                dictLemmaInIndex[lemma] = []
            dictLemmaInIndex[lemma].append(index)
        else:
            for elem in wiki[index].synset:
                lemma1 = getLemmaForSynsets(elem.title)
                if lemma1 != "":
                    if not lemma1 in dictLemmaInIndex:
                        dictLemmaInIndex[lemma1] = []
                    dictLemmaInIndex[lemma1].append(index)
    return dictLemmaInIndex
def adding_multi_label(wiki, dictLemmaInIndex):
    """
        добавляем метки неоднозанчной статьи, если лемма названия не однозначна
    """
    dictTitleInIndex = {}
    for index in tqdm(range(len(wiki))):
        dictTitleInIndex[wiki[index].page.title] = index
    tempCount = 0
    for key in dictLemmaInIndex:
        for elem in dictLemmaInIndex[key]:
            if not wiki[elem].page.multiPage:
                if len(dictLemmaInIndex[key])>1:
                    wiki[dictTitleInIndex[wiki[elem].page.title]].page.multiPage = True
                    tempCount +=1
    return wiki, tempCount
def accounting_for_redirects(new_wiki, dictDisplay):
    """
        проведем 2 этап связывания - учитывание редиректов статей
        вовзращает все многозначные викисинсеты и словарь отображение, количество добавленных связей на данном этапе
    """
    wiki3 = [] # будут только многозначные
    countN = 0
    for w in tqdm(new_wiki):
        flag = False
        if not w.page.meaningPage and not w.page.multiPage:
            for d in w.synset:
                one = unambiguousDisplay(d.title)
                if  one[0] and "N" in wn.get_synsets(one[1])[0].id:
    #                 if w.page.title == "Abbath":
    #                     print(d.title)
                    flag = True
                    countN += 1
                    idd = wn.get_synsets(one[1])[0].id
                    p = display(w.page.id,w.page.revid,w.page.title,one[1], idd,
                                extractCtxW(w.page.links, w.page.categories), w.page.first_sentence)
                    dictDisplay[w.page.title]=p
                    break
        if not flag:
            wiki3.append(w)
    return wiki3, dictDisplay, countN

def getting_candidates_for_stage_3(wiki3, dictWn, dictLemmaInIndex):
    #собираем кандидатов
    dictSynsetId = defaultdict(list)
    for index in tqdm(range(len(wiki3)), desc="getting_candidates_for_stage_3"):
        w = wiki3[index]
        if not w.page.meaningPage:
            lemma = getLemmaForSynsets(w.page.title)
            #если нашли лемму из ворднета и она существительное
            if lemma != "" and getKeyForId(lemma) in dictWn:
                for synset in wn.get_synsets(lemma):
                    dictSynsetId[synset.id].append(w)
        else:
            lemmaTitle = getLemmaForSynsets(w.page.title)
            for link in w.page.links:
                lemma = getLemmaForSynsets(link)
                if lemma in dictLemmaInIndex:
                    #если нашли лемму многозначной статьи из ворднета и она существительное
                    if lemmaTitle != "" and getKeyForId(lemmaTitle) in dictWn:
                        for synset in wn.get_synsets(lemmaTitle):
                            for indexElem in dictLemmaInIndex[lemma]:
                                dictSynsetId[synset.id].append(wiki3[indexElem])
    return dictSynsetId

def resolution_of_ambiguity(sortCandidates, dictIdTitle, labse, dictDisplay, dictWn):
    badlemma = []
    baddenominator = []
    badmaxP = []
    badsynsetlemma = []
    badidWn = []
    dictSortCandidates = {}
    for key in tqdm(sortCandidates, desc="stage 3"):
        if len(sortCandidates[key]) == 1:
                w = sortCandidates[key][0]
                p = display(w.page.id,w.page.revid,w.page.title,dictIdTitle[key], key,extractCtxW(w.page.links, w.page.categories), w.page.first_sentence)
                dictDisplay[w.page.title]=p
                dictSortCandidates[key] = [(sortCandidates[key][0], 1)]
        else:
            maxP = -1
            maxagrument = 0
            lemmaSynset = getLemmaForSynsets(dictIdTitle[key])
            dictSortCandidates[key] = []
            if lemmaSynset != "":
                idWn = wn.get_senses(lemmaSynset)[0].id
                if "N" in idWn: #почему-то иногда для синсета существительного сенс не существительное
                    for elem in sortCandidates[key]:
                        ctxw = extractCtxW(elem.page.links, elem.page.categories)
                        lemma = getLemmaForSynsets(elem.page.title)
                        if lemma != "":
                            numerator = score(dictWn[idWn].ctx, ctxw)
                            denominator = 0
                            for item in sortCandidates[key]:
                                addctxw = extractCtxW(item.page.links, item.page.categories)
                                denominator +=score(dictWn[idWn].ctx, addctxw)
                        else:
                            badlemma.append(elem.page.title)
                        temp_distance = cosin_distance(lemmaSynset, elem.page.first_sentence, labse)
                        if denominator != 0:
                            temp_p = numerator / denominator +  temp_distance 
                            dictSortCandidates[key].append((elem, temp_p))                           
                            if  temp_p > maxP:
                                maxP = temp_p
                                maxagrument = elem
                        else:
                            if  temp_distance > maxP:
                                maxP = temp_distance
                                maxagrument = elem
                            baddenominator.append(elem.page.title)
                            dictSortCandidates[key].append((elem, temp_distance))
                else:
                    badidWn.append(wn.get_senses(lemmaSynset)[0].id)
            else:
                badsynsetlemma.append(dictIdTitle[key])
            if maxP != - 1:
                w = maxagrument
                p = display(w.page.id,w.page.revid,w.page.title,dictIdTitle[key], key,
                            extractCtxW(w.page.links, w.page.categories), w.page.first_sentence)
                dictDisplay[w.page.title]=p
            else:
                badmaxP.append(key)   
    return dictSortCandidates, dictDisplay, len(badlemma), len(baddenominator), len(badmaxP), len(badsynsetlemma), len(badidWn)
    