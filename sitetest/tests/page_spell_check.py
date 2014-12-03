# -*- coding: utf-8 -*-

import re
from bs4 import BeautifulSoup, SoupStrainer, Comment
import enchant
from enchant.tokenize import get_tokenizer
import string
import traceback        


CONTRACTION_LIST = ["aren't", "can't", "couldn't", 
    "didn't", "doesn't", "don't", "hadn't", "hasn't", 
    "haven't", "he'd", "he'll", "he's", "i'd", "i'll", 
    "i'm", "i've", "isn't", "let's", "mightn't", 
    "mustn't", "shan't", "she'd", "she'll", "she's", 
    "shouldn't", "that's", "there's", "they'd", 
    "they'll", "they're", "they've", "wasn't", "we'd", "we're", 
    "we've", "weren't", "what'll", "what're", "what's", 
    "what've", "where's", "who's", "who'll", "who're", 
    "who's", "who've", "won't", "wouldn't", "you'd", 
    "you'll", "you're", "you've", 
    "e.g", "i.e", 'et', 'al', 'n.d', 'p.m', 'a.m']


PREFIX_LIST = ['a', 'anti', 'arch', 'be', 'co', 'counter', 'de', 'dis', 'dis', 
'en', 'ex', 'fore', 'hind', 'mal', 'mid', 'midi', 'mini', 'mis', 'out', 'over', 
'post', 'pre', 'pro', 're', 'self', 'step', 'trans', 'twi', 'un', 'un', 'under', 
'up', 'with', 'Afro', 'ambi', 'amphi', 'an', 'ana', 'Anglo', 'ante', 'anti', 
'apo', 'astro', 'auto', 'bi', 'bio', 'circum', 'cis', 'con', 'contra', 'cryo', 
'crypto', 'de', 'demi', 'demo', 'deuter', 'di', 'dia', 'dis', 'du', 'eco', 
'electro', 'en', 'epi', 'Euro', 'ex', 'extra', 'Franco', 'geo', 'gyro', 
'hetero', 'hemi', 'homo', 'hydro', 'hyper', 'hypo', 'ideo', 'idio', 'in', 
'Indo', 'in', 'infra', 'inter', 'intra', 'iso', 'macro', 'maxi', 'mega', 'meta',
'micro', 'mono, mon', 'multi', 'neo', 'non', 'omni', 'ortho', 'paleo', 'pan', 
'para', 'ped', 'per', 'peri', 'photo', 'pod', 'poly', 'post', 'pre', 'preter', 
'pro', 'pro', 'pros', 'proto', 'pseudo', 'pyro', 'quasi', 'retro', 'semi', 
'socio', 'sub', 'super', 'supra', 'sur', 'syn', 'tele', 'trans', 'tri', 
'ultra', 'uni', 'vice']


def test_basic_spell_check(set, special_dictionary, verbose=False):
    """
    For each page, make sure that visible text is spelled correctly
    """

    if verbose:
        print "Spell check site using special_dictionary: %s"%(special_dictionary)

    lorem_ipsum_count = 0
    spelling_issue_count = 0

    d = enchant.Dict("en_US")
    tknzr = get_tokenizer("en_US")

    total = len(set.parsed_links)
    count = 0
    
    for link_url in set.parsed_links:
        link = set.parsed_links[link_url]

        if verbose:
            print "%s/%s"%(count, total)
        count += 1
        
        if link.is_internal() and not link.skip_test == True:
            link_html = link.html
            if link_html and '.xml' not in link_url:
                # try:
                soup = BeautifulSoup(link_html)

                #REMOVE COMMENTS:
                comments = soup.findAll(text=lambda text:isinstance(text, Comment))
                [comment.extract() for comment in comments]

                misspelled_words = []

                texts = soup.findAll(text=True)
                visible_texts = filter(visible, texts)
                
                #1. Check for Lorem Ipsum
                has_lorem_ipsum = False
                for text in visible_texts:
                    # print "text: %s - %s"%(text.parent.name, text)

                    if 'lorem' in text.lower():
                        has_lorem_ipsum = True
                        

                if has_lorem_ipsum:
                    lorem_ipsum_count += 1
                    message = "Lorem Ipsum found in <a href='#%s' class='alert-link'>%s</a>."%(link.internal_page_url, link_url)
                    link.add_warning_message(message)

                #2. Check for Spelling
                if has_lorem_ipsum == False:
                    for text in visible_texts:
                    
                        #replace curly quotes and emdashes, spaces, etc
                        text = text.replace(u"’", "'").replace(u"“", "\"").\
                            replace(u"”", "\"").replace(u"″","\"").\
                            replace(u"–","-").replace(u"‘","'").\
                            replace(u"’","'").replace(u"—","-").\
                            replace(u"…", '.').replace(u"™", "").\
                            replace(u"®", "").replace(u"&nbsp;", " ")

                        words = text.replace('-',' ').replace('/',' ').split(" ")
                        
                        char_list = u'*?:!.,;()[]"“”’\''
                        cleaned_words = [word.strip().rstrip(char_list).lstrip(char_list) for word in words]
                        depossessive_words = [word.replace(u"'s", "") for word in cleaned_words]
                        real_words = [word for word in depossessive_words if (word.strip() != '')]

                        #TODO: Handle
                        #‘term
                        #non–medically
                        #handle suffixes
                        #1–3
                        #it—so
                        #$2,500
                        #of…
                        #e.g
                        #mentor/mentee
                        #1990s

                        
                        #tokenized_words = [w for w in tknzr(text)]
                        #real_words = [w[0] for w in tokenized_words]
                        #print "Returned: %s"%(real_words)

                        for word in real_words: 

                            try:
                                word_exists = d.check(word) or check_special_dictionary(word, special_dictionary)
                            except Exception:        
                                print "Error checking word on %s: %s"%(link.url, traceback.format_exc())
                                word_exists = True

                            word_is_proper_noun = word[0].isupper()

                            deordinaled = word.lower().replace("st", "").replace("nd", "").replace("rd", "").replace("th", "")
                            denumbered = translate_non_alphanumerics(deordinaled)                            
                            is_numeric = denumbered == '' or denumbered == None \
                                or denumbered == 's' or denumbered == 'tb' or \
                                denumbered == 'gb' or denumbered == 'gbe' or \
                                denumbered == 'mb' or denumbered == 'k' or denumbered == 'ks'
                            is_prefix = word.lower() in PREFIX_LIST
                            


                            is_technological = (re.match(r"^[a-zA-Z0-9._]+\@[a-zA-Z0-9._]+\.[a-zA-Z]{3,}$", word) != None) or \
                                ('http' in word.lower() or 'www' in word.lower() or '.com' in word.lower() or '.org' in word.lower()) or \
                                (word[0].lower() == '@') or \
                                (word[0].lower() == '#')

                            money_regex = re.compile(r'^\$?(\d*(\d\.?|\.\d{1,2}))$')
                            is_money = money_regex.match(word.replace(",","")) 


                            is_contraction = word.lower().replace(u"’",u"'") in CONTRACTION_LIST     

                            if not word_exists and not word_is_proper_noun and not is_numeric and not is_technological and not is_contraction and not is_prefix and not is_money:
                                if word not in misspelled_words:
                                    message = "Word &ldquo;%s&rdquo; misspelled in <a href='#%s' class='alert-link'>%s</a>."%(word, link.internal_page_url, link_url)
                                    link.add_info_message(message)
                                    misspelled_words.append(word)

                                    spelling_issue_count += 1    
                else:
                    message = "Spell check skipped on this page because Lorem Ipsum was found"
                    link.add_info_message(message)
                                                
                        
                # except:
                #   pass

    if lorem_ipsum_count > 0:
        set.add_warning_message("%s pages were found to have Lorem Ipsum"%(lorem_ipsum_count), lorem_ipsum_count)

    if spelling_issue_count > 0:
        set.add_info_message("%s spelling issues found"%(spelling_issue_count), spelling_issue_count)


def check_special_dictionary(word, special_dictionary):
    for special_word in special_dictionary:
        if special_word.lower() == word.lower():
            return True
    return False


def translate_non_alphanumerics(to_translate, translate_to=u''):
    not_letters_or_digits = u'!"#%\'()*+,-./:;<=>?@[\]^_`{|}~0123456789'
    translate_table = dict((ord(char), translate_to) for char in not_letters_or_digits)
    return to_translate.translate(translate_table)

def visible(element):
    #print 'is element visible? %s'%(element)
    element_ascii = element.encode('ascii', 'ignore')
    if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
        return False
    elif re.match(u'<!--.*-->', str(element_ascii)):
        return False
    elif re.match(u'<!(|--)\[[^\]]+\]>.+?<!\[endif\](|--)>', str(element_ascii)):
        #print "Its a conditional comment!"
        return False
    return True