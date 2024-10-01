from bs4 import BeautifulSoup

from lib.quest_data.quest_data_series import QuestSeries
from lib.quest_data.quest_data_single import QuestSingle
from lib.quest_data.quest_data_act import QuestAct

from lib.page.get_page import get_local_page
from lib.page.get_wiki_url_from_name import get_wiki_url_from_name


def getQuest(name:str, questsDict:dict, basepath:str, conversionRef:dict) -> QuestSeries|QuestSingle|QuestAct:
    
    quest_url = get_wiki_url_from_name(name, conversionRef)
    html = get_local_page(quest_url, basepath)

    # Parse the HTML content with Beautiful Soup
    soup = BeautifulSoup(html, 'lxml')
    soup = soup.select_one('div[class="page-header__categories"]')
    # Find all <a> tags in the page
    tags = soup.find_all('a')
    # Loop through all <a> tags
    for tag in tags:
        if "World Quest Series" in tag.text:
            return QuestSeries(name, basepath, conversionRef)
        if "World Quest Acts" in tag.text:
            #return QuestSeries(name, basepath)
            return QuestAct(name, basepath, questsDict, conversionRef)
        elif "World Quest" in tag.text:
            return QuestSingle(name, basepath, conversionRef)

    raise Exception(f"\"{name}\" isn't a World Quest or World Quest Series")