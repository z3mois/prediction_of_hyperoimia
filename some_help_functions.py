from functools import lru_cache
import pymorphy2
from ruwordnet import RuWordNet
from tqdm import tqdm
import numpy as np
from collections import defaultdict
import time
def my_split(x):
    s = ""
    for i in x:
        if i!= "(" and i != ")":
            s +=i
        elif i  == ")":
            s += ""
        else:
            s += ","
    return s
def extractCtxW(links, categories):
    ctx = set()
    for link in links:
        ctx.add(" ".join([get_normal_form(word) for word in link.split()]))
    for elem in categories:
        ctx.add(" ".join([get_normal_form(word) for word in elem.split()]))
    return ctx
def extractCtxS(wn, lemma:str):
    #составляем контекст для слова из wordnet
    ctx_s = set()
    #synonymy
    for sense in wn.get_synsets(lemma):
        for synonymy in sense.senses:
            ctx_s.update(my_split(synonymy.lemma).split(","))
    #Hypernymy/Hyponymy
    for sense in wn.get_senses(lemma):
        for hypernyms in sense.synset.hypernyms:
            ctx_s.update(my_split(hypernyms.title).split(","))
    for sense in wn.get_senses(lemma):
        for hyponyms in sense.synset.hyponyms:
            ctx_s.update(my_split(hyponyms.title).split(","))
    #Sisterhood:
    for sense in wn.get_senses(lemma):
        for hypernyms in sense.synset.hypernyms:
            for sister in hypernyms.hyponyms:
                ctx_s.update(my_split(sister.title).split(","))
    return ctx_s
@lru_cache(maxsize=200000)
def get_normal_form(word):
    return morph_analizer.parse(word)[0].normal_form
def get_corted_canidates(dictSynsetId):
    #возможны повторения среди кандидатов, уадлим их
    def count1(value, array):
        count = 0
        for elem in array:
            if elem.page.id == value.page.id:
                count += 1
        return count
    for key in tqdm(dictSynsetId):
        tempList = []
        for elem in dictSynsetId[key]:
            if count1(elem, tempList) < 1 and not elem.page.meaningPage:
                tempList.append(elem)
        dictSynsetId[key] = tempList
    #sort candidates
    sorted_tuple = sorted(dictSynsetId.items(), key=lambda x: x[0])
    return dict(sorted_tuple)

def map_id_title_synset(): 
    dictIdTitle = {}
    for synset in wn.synsets:
        dictIdTitle[synset.id] = synset.title
    return dictIdTitle

def score(ctxS, ctxW):
    return len(ctxS.intersection(ctxW))

def cosin_distance(word, sentense, labse):
    word_embeding = labse.transform(word)
    sentense_embeding = labse.transform(sentense)
    return np.dot(word_embeding, sentense_embeding) / (sum(sentense_embeding ** 2) * sum(word_embeding ** 2))
def stage_4_preprocessing(dictDisplay):
    #собираем отображения  связанные с одним wordId
    print("Start stage_4_preprocessing")
    start = time.time()
    dict_wordId_in_display_and_key = defaultdict(list)
    for key, value in dictDisplay.items():
        dict_wordId_in_display_and_key[value.wordId].append((key,value))
    i  = 0
    for key, value in dict_wordId_in_display_and_key.items():
        if len(value) > 1:
            i+=len(value)
    #удалим из dictDisplay повторяющиеся wordId
    for key, value in dict_wordId_in_display_and_key.items():
        if len(value) > 1:
            for item in value:
                del dictDisplay[item[0]]
    #удалим из dict_wordId_in_display_and_key однозначные отображенния
    dict_wordId_in_display_and_key_new = defaultdict(list)
    for key, value in dict_wordId_in_display_and_key.items():
        if len(value) > 1:
            dict_wordId_in_display_and_key_new[key] = value
    print(f"End of stage_4_preprocessing,timework is {time.time()- start}")
    return dict_wordId_in_display_and_key_new, dictDisplay

morph_analizer = pymorphy2.MorphAnalyzer()
wn = RuWordNet(filename_or_session='D:\\lbase_data\\ruwordnet.db')