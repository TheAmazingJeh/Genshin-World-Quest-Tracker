import urllib.parse

def get_wiki_url_from_name(name, conversionRef):
    baseurl = 'https://genshin-impact.fandom.com/wiki/'
    # Construct the URL and url-encode the name
    url = baseurl + urllib.parse.quote_plus(conversionRef[name])
    url = url.replace('+', '_')
    # Return the URL
    return url

if __name__ == '__main__':
    name = "The Adventurer's Guild's Affairs"
    url = get_wiki_url_from_name(name)
    print(url)