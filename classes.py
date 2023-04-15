from dataclasses import dataclass
import json

@dataclass
class Page:
    id: int
    revid: int
    title:str
    meaningPage: bool
    multiPage: bool
    categories: list
    links: list
    redirect:bool
    first_sentence:str
    def __eq__(self, other):
        return (self.id, self.revid, self.title, self.meaningPage,
                self.multiPage, self.categories, self.links, 
                self.redirect) == (other.id, other.revid, 
                other.title, other.meaningPage,
                other.multiPage, other.categories, other.links, 
                other.redirect)
class PageEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Page):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)
    
@dataclass
class WnCtx:
    id: int
    ctx: set
    lemmaInWn: str
    name: str
class WnCtxEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, WnCtx):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)
@dataclass
class WikiSynset():
    def __init__(self, page:Page):
        self.page = page
        self.synset = [page]

    def append(self, redirect_title:Page):
        self.synset.append(redirect_title)


@dataclass
class display:
    id:int
    revid:int
    title:str
    lemma:str
    wordId:int
    ctxW:set
    first_sentense:str
class displayEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, display):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)