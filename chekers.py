from some_help_functions import my_split, get_normal_form, wn

def includeTitleInWn(all_senses, title):
    title = title.upper()
    title = title.replace("—", "-")
    title = title.replace(",", "")
    if title in all_senses:
        return True
    if "(" in title:
        text = my_split(title).split(",")
        if text[0] in all_senses:
            return True
    text = my_split(title).split(",")
    lemmatized = " ".join([get_normal_form(word)
                for word in text[0].split()])
    if lemmatized.upper() in all_senses:
        return True
    if "Ё" in title:
        return includeTitleInWn(all_senses, title.replace("Ё","Е"))
    return False

def unambiguousDisplay(title):
    title = title.upper()
    title = title.replace("—", "-")
    title = title.replace(",", "")
    if len(wn.get_synsets(title)) == 1:
        return [True, title]
    if "(" in title:
        text = my_split(title).split(",")
        if len(wn.get_synsets(text[0])) == 1:
            return [True, text[0]]
    text = my_split(title).split(",")
    lemmatized = " ".join([get_normal_form(word)
                for word in text[0].split()])
    if len(wn.get_synsets(lemmatized.upper())) == 1:
        return [True, lemmatized.upper()]
    if "Ё" in title:
        return unambiguousDisplay(title.replace("Ё","Е"))
    return [False, ""]

def getKeyForId(key):
    if len(wn.get_senses(key)) > 0:
        # print(1)
        return wn.get_senses(key)[0].id
    if "(" in key:
        text = my_split(key).split(",")
        if  len(wn.get_senses(text[0])) > 0:
            # print(2)
            return wn.get_senses(text[0])[0].id
    text = my_split(key).split(",")
    lemmatized = " ".join([get_normal_form(word) for word in text[0].split()])
    if len(wn.get_senses(lemmatized)) > 0:
        # print(3)
        return wn.get_senses(lemmatized)[0].id
    if "ё" in key:
        return getKeyForId(key.replace("ё",'е'))
    return ""
def getLemmaForSynsets(title):
    title = title.upper()
    title = title.replace("—", "-")
    title = title.replace(",", "")
    ch = " " 
    if len(wn.get_synsets(title))>0:
        return title
    if "(" in title:
        text = my_split(title).split(",")
        if len(wn.get_synsets(text[0]))>0:
            if text[0][len(text[0]) - 1] == " ":
                text[0] = text[0].rstrip(ch)
            return text[0]
    text = my_split(title).split(",")
    lemmatized = " ".join([get_normal_form(word) for word in text[0].split()])
    if len(wn.get_synsets(lemmatized))>0:
        if lemmatized[len(lemmatized) - 1] == " ":
            lemmatized = lemmatized.rstrip(ch)
        return lemmatized
    if "Ё" in title:
        return getLemmaForSynsets(title.replace("Ё","Е"))
    return ""

def helpForCheck(d, title):
    d = d.upper()
    d = d.replace("—", "-")
    d = d.replace(",", "")
    if d == title:
        return True
    if "(" in d:
        text = my_split(d).split(",")
        if title == text[0]:
            return True
    text = my_split(d).split(",")
    lemmatized = " ".join([get_normal_form(word) for word in text[0].split()])
    if lemmatized == title:
        return True
    if "Ё" in d:
        return helpForCheck(d.replace("Ё","Е"), d)
    return False

def check(wn, lemma, d):
    for sense in wn.get_synsets(lemma):
        if helpForCheck(d, sense.title):
            return [True, sense]
    return [False, "ф"]