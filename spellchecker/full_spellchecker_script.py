import hunspell
import gzip, os, re
from math import log


##########################################################
#### Функция для корректировки неправильной раскладки ####

#### Утилитарный словарь в глобальной переменной
LAYOUT = dict(zip(map(ord, "qwertyuiop[]asdfghjkl;'zxcvbnm,./`"
                           'QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>?~'),
                           "йцукенгшщзхъфывапролджэячсмитьбю.ё"
                           'ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,Ё'))

def turn_layout(word):
    return word.translate(LAYOUT)

    

#############################################################
#### Функции для сплита слипшихся слов на базе wordninja ####


class LanguageModel(object):
  def __init__(self, word_file):
    # Build a cost dictionary, assuming Zipf's law and cost = -math.log(probability).
    with gzip.open(word_file) as f:
      words = f.read().decode().split()
    self._wordcost = dict((k, log((i+1)*log(len(words)))) for i,k in enumerate(words))
    self._maxword = max(len(x) for x in words)
   

  def split(self, s):
    """Uses dynamic programming to infer the location of spaces in a string without spaces."""
    l = [self._split(x) for x in _SPLIT_RE.split(s)]
    return [item for sublist in l for item in sublist]


  def _split(self, s):
    # Find the best match for the i first characters, assuming cost has
    # been built for the i-1 first characters.
    # Returns a pair (match_cost, match_length).
    def best_match(i):
      candidates = enumerate(reversed(cost[max(0, i-self._maxword):i]))
      return min((c + self._wordcost.get(s[i-k-1:i].lower(), 9e999), k+1) for k,c in candidates)

    # Build the cost array.
    cost = [0]
    for i in range(1,len(s)+1):
      c,k = best_match(i)
      cost.append(c)

    # Backtrack to recover the minimal-cost string.
    out = []
    i = len(s)
    while i>0:
      c,k = best_match(i)
      assert c == cost[i]
      # Apostrophe and digit handling (added by Genesys)
      newToken = True
      if not s[i-k:i] == "'": # ignore a lone apostrophe
        if len(out) > 0:
          # re-attach split 's and split digits
          if out[-1] == "'s" or (s[i-1].isdigit() and out[-1][0].isdigit()): # digit followed by digit
            out[-1] = s[i-k:i] + out[-1] # combine current token with previous token
            newToken = False
      # (End of Genesys addition)

      if newToken:
        out.append(s[i-k:i])

      i -= k

    return reversed(out)

DEFAULT_LANGUAGE_MODEL = LanguageModel('russian.txt.gz')
_SPLIT_RE = re.compile("[^а-яА-Яa-zA-Z0-9']+")


def split(s):
  return DEFAULT_LANGUAGE_MODEL.split(s)




###############################################################################
########################## Сам скрипт Spellchecker-a ########################## 
###############################################################################


################################################################
#### Инициализация Hunspell-чекеров, должны быть глобальные ####

hobj_ru = hunspell.Hunspell(
    "Russian",
    hunspell_data_dir=os.getcwd() + '/Dictionaries/',
    disk_cache_dir=os.getcwd() + '/hunspell_cache/'
)
hobj_eng = hunspell.Hunspell(
    "English (American)",
    hunspell_data_dir=os.getcwd() + '/Dictionaries/',
    disk_cache_dir=os.getcwd() + '/hunspell_cache/'
)



def spellcheck(data):

    variants = {
        0 : [], 
        1 : [],
        2 : [], 
        3 : [],
    }
    
    
    for word in data.split(" "):    

        if word.isnumeric():
            for i in range(4):
                variants[i].append(word)
            continue

        suggest = hobj_ru.suggest(f'{word}') 

        if hobj_ru.spell(f'{word}') == False:
            if len(re.findall(r'[A-z]+', word )) > 0:

                suggest = hobj_eng.suggest(f'{word}')
                word_turned = turn_layout(word)

                if hobj_eng.spell(f'{word}'):
                    for i in range(4):
                        variants[i].append(word)
                    continue

                elif hobj_ru.spell(word_turned):
                    for i in range(4):
                        variants[i].append(word_turned)
                    continue

                elif len(suggest) > 0:
                    for i in range(len(suggest)):
                        if i > 3:
                            break
                        variants[i].append(suggest[i])
                    continue
                
                else:
                    word = word_turned
                    
            elif len(suggest) == 0: 
                splitted_words = " ".join(split(word))        
                for i in range(4):
                    variants[i].append(splitted_words)
        
        if len(suggest) > 0:
            for i in range(len(suggest)):
                if i > 3:
                    break
                variants[i].append(suggest[i])

    for i in range(4):
        variants[i] = " ".join(variants[i])
    return variants



###############################
#### Пример работы скрипта ####

data = "hello приветдрузбя rfr ltkf фыгня крил"

print(spellcheck(data))
