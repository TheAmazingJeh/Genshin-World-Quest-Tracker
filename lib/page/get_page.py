import requests, os, time
from bs4 import BeautifulSoup

def get_local_page(url: str, cachePath:str, refresh: bool = False, retryAmount: int = 10):
    # Get the base path of the project
    # Convert the URL to a filename. preserve the directory structure
    filename = os.path.join(cachePath, f"{url.replace('https://genshin-impact.fandom.com/', '').replace('/', '_')}.html")
        
    if not refresh and os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        while retryAmount > 0:
            response = requests.get(url)
            # Check response status code
            if response.status_code == 200: break
            else:
                retryAmount -= 1
                for i in range(10, 0, -1):
                    print(f"Error: {response.status_code} for {url}. Retrying in {i} seconds...", end='\r')
                    time.sleep(1)
                print("Retrying...                                                      ")
        if retryAmount == 0: raise TimeoutError("Failed to get the page after 10 retries.")

        response = response.text
        

        # Parse the HTML content
        soup = BeautifulSoup(response, 'lxml')
        
        # Detect if there is "There is currently no text in this page." in the page
        if soup.find('div', class_='noarticletext'):
            print(f"Page {url} does not exist.")
            raise Exception(f"Page {url} does not exist.")

        # Convert relative URLs to absolute URLs
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.startswith('/'):
                a_tag['href'] = f'https://genshin-impact.fandom.com{href}'

        # Remove unwanted formatting tags
        for tag in ['b', 'strong', "i", "em", "mark", "small", "del", "ins", "sub", "sup"]:
            for tag_2 in soup.select(tag):
                tag_2.unwrap()

        # Remove edit sections
        for tag in soup.select('span[class="mw-editsection"]'):
            tag.decompose()

        # Get the modified HTML as a string
        modified_html = str(soup)

        # Write the modified HTML content to the file
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(modified_html)

        return modified_html
