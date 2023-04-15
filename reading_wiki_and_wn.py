import re
import os
import bz2
from  extractor import Extractor
from tqdm import tqdm
from classes import Page, WnCtx
from some_help_functions import extractCtxS, get_normal_form, wn
from xml.dom import minidom
acceptedNamespaces = ['w', 'wiktionary', 'wikt']
templateNamespace = ''
tagRE = re.compile(r'(.*?)<(/?\w+)[^>]*>(?:([^<]*)(<.*?>)?)?')

def collect_pages(text):
    """
    :param text: the text of a wikipedia file dump.
    """
    # we collect individual lines, since str.join() is significantly faster
    # than concatenation
    page = []
    id = ''
    revid = ''
    last_id = ''
    inText = False
    redirect = False
    redirect_page = ''
    for line in text:
        if '<' not in line:     # faster than doing re.search()
            if inText:
                page.append(line)
            continue
        m = tagRE.search(line)
        if not m:
            continue
        tag = m.group(2)
        if tag == 'page':
            page = []
            redirect = False
        elif tag == 'id' and not id:
            id = m.group(3)
        elif tag == 'id' and id: # <revision> <id></id> </revision>
            revid = m.group(3)
        elif tag == 'title':
            title = m.group(3)
        elif tag == 'redirect':
            redirect = True
            redirectRE = re.compile(r'title=\"(.*?)\" />')
            redirect_page = re.findall(redirectRE, line)[0]
        elif tag == 'text':
            inText = True
            line = line[m.start(3):m.end(3)]
            page.append(line)
            if m.lastindex == 4:  # open-close
                inText = False
        elif tag == '/text':
            if m.group(1):
                page.append(m.group(1))
            inText = False
        elif inText:
            page.append(line)
        elif tag == '/page':
            colon = title.find(':')
            if (colon < 0 or (title[:colon] in acceptedNamespaces) and id != last_id and
                    not redirect and not title.startswith(templateNamespace)):
                yield (id, revid, title, page, redirect_page,redirect)
                last_id = id
            id = ''
            revid = ''
            page = []
            inText = False
            redirect = False
            redirect_page=''

def decode_open(filename, mode='rt', encoding='utf-8'):
    """
    Open a file, decode and decompress, depending on extension `gz`, or 'bz2`.
    :param filename: the file to open.
    """
    ext = os.path.splitext(filename)[1]
    if ext == '.gz':
        import gzip
        return gzip.open(filename, mode, encoding=encoding)
    elif ext == '.bz2':
        return bz2.open(filename, mode=mode, encoding=encoding)
    else:
        return open(filename, mode, encoding=encoding)
def extract_cat(text):
    matcher=re.compile(r"Категория:\s?([А-Яа-я\s?]+)")
    return matcher.findall(text)
def extract_links(text):
    matcher=re.compile(r"[\[\[]([А-Яа-я\s?]+)[\|,\]\]]")
    return matcher.findall(text)
def extract_first_links(text):
    matcher=re.compile(r"[\[\[]([А-Яа-я\s?]+)[\|,\]\]]")
    answer = []
    for elem in text.split("\n"):
        item = matcher.findall(elem)
        if len(item) > 0:
            answer.append(item[0])
    return answer

def collect_article(dump_path):
    input = decode_open(dump_path)
    dictRedirect = {}
    pages = []
    redirectcount = 0
    dictPageRedirect = {}
    for id, revid, title, page, redirect_page, redirect in tqdm(collect_pages(input), desc='Read dump Wiki'):
        text = ''.join(page)
        text_lower = text.lower()
        multiPage = False
        if text_lower.find('{{другие значения') != -1:
            multiPage = True
        elif title.find("(") != -1 and (not "значения" in title.lower())and (not "значение" in title.lower()):
            multiPage = True
        elif text_lower.find("{{перенаправление") != -1:
            multiPage = True
        elif text_lower.find("{{другое значение") != -1:
            multiPage = True
        elif text_lower.find("{{значения") != -1:
            multiPage = True
        elif text_lower.find("{{redirect-multi") != -1:
            multiPage = True
        elif text_lower.find("{{redirect-multi") != -1:
            multiPage = True
        elif text_lower.find("{{see also") != -1:
            multiPage = True
        elif text_lower.find("{{о|") != -1:
            multiPage= True
        elif text_lower.find("{{список однофамильцев}}") != -1:
            multiPage= True
        categories = extract_cat(text)
        
        meaningPage = False
        if ("значения" in title.lower()) or ("значение" in title.lower()):
            meaningPage = True
        elif text_lower.find('{{неоднозначность') != -1:
            meaningPage = True
        elif text_lower.find('{{многозначность') != -1:
            meaningPage = True
        elif text_lower.find('{{disambig') != -1:
            meaningPage = True
        # redirects = extract_redirects(text)
        links =[]
        if not meaningPage:
            links = extract_links(text)
        else:
            links = extract_first_links(text)
        first_sentense = ""
        if not redirect_page:
            ext = Extractor(id,revid,"",title,page)
            first_sentense = "\n".join(ext.clean_text(text)).split(".")[0]
            
        if len(redirect_page) > 0:
            if redirect_page not in dictRedirect:
                dictRedirect[redirect_page] = []
                dictPageRedirect[redirect_page] = []
            dictPageRedirect[redirect_page].append(Page(id,revid,title,meaningPage,multiPage,categories,links,redirect,first_sentense))
            dictRedirect[redirect_page].append(title)
            redirectcount +=1 
        pages.append(Page(id,revid,title,meaningPage,multiPage,categories,links,redirect,first_sentense))
    input.close()
    return pages, dictPageRedirect, dictRedirect
def collect_info_wn(xml_path):
    mydoc = minidom.parse(xml_path)
    items = mydoc.getElementsByTagName('sense')
    countWn = 0
    dictWn = {}
    for elem in tqdm(items, desc='Read Wn sense'):
        countWn +=1
        text = elem.attributes['name'].value
        text_id = elem.attributes["id"].value
        lemma = elem.attributes["lemma"].value
        ctx_s = extractCtxS(wn, lemma)
        ctx = set()
        for elem in ctx_s:
            ctx.add(" ".join([get_normal_form(word) for word in elem.split()]))
        dictWn[text_id] = WnCtx(text_id, ctx, lemma, text)
    return dictWn, countWn