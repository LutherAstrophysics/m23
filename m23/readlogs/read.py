import requests
from bs4 import BeautifulSoup

def getFilesList(url = "http://10.30.5.4:3000/" ):
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    return [item.get('href') for item in soup.find_all('a')]

if __name__ == "__main__":
    print(getFilesList())
