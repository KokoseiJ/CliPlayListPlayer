import os
import time
import requests
import selenium
import multiprocessing
from bs4 import BeautifulSoup as bs
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from googleapiclient.discovery import build

PATH = os.path.dirname(os.path.abspath(__file__))
BASEPATH = os.path.join(PATH, "..", "..")
KEYPATH = os.path.join(PATH, "api_key")
if os.name == "nt":
    DRIVER = os.path.join(BASEPATH, "geckodriver.exe")
else:
    DRIVER = os.path.join(BASEPATH, "geckodriver")

def get_key():
    try:
        key = open(KEYPATH).read()
    except:
        print(f"Can't find {KEYPATH}. Creating one...")
        key = input("Enter your API Key here. type \"noapi\" to use noapi method instead.: ")
        print("Saving api_key...")
        open(KEYPATH, "w").write(key)
    return key

def get_playlist(playlistid):
    key = get_key()
    if key == "noapi":
        return get_playlist_noapi(playlistid)
    else:
        return get_playlist_api(playlistid, key)

def get_playlist_api(playlistid, key):
    youtube = build("youtube", "v3", developerKey = key)
    pageToken = ""
    vidlist = []
    while True:
        request = youtube.playlistItems().list(
            part = "snippet",
            maxResults = 50,
            pageToken = pageToken,
            playlistId = playlistid
        )
        response = request.execute()
        for vidinfo in response['items']:
            vidinfo = vidinfo['snippet']
            video = {
                "type": "youtube",
                "title": vidinfo['title'],
                "owner": vidinfo['channelTitle'],
                "id": vidinfo['resourceId']['videoId']
            }
            vidlist.append(video)
        try:
            pageToken = response['nextPageToken']
        except KeyError:
            break
    playlist = {
        "type": "youtube",
        "id": playlistid,
        "list": vidlist
    }
    return playlist

def get_playlist_noapi(playlistid):
    url = f"https://www.youtube.com/playlist?list={playlistid}"
    options = Options()
    options.headless = True
    options.set_preference("general.useragent.override", "")
    driver = Firefox(executable_path = DRIVER, options = options)
    driver.get(url)
    while True:
        try:
            button = driver.find_element_by_class_name("yt-uix-load-more")
        except selenium.common.exceptions.NoSuchElementException:
            break
        button.click()
    soup = bs(driver.page_source, "html.parser")
    vidlist = []
    for vidinfo in soup.find_all("tr", {"class": "pl-video"}):
        """
        tempdict = {}
        tempdict['type'] = "youtube"
        tempdict['title'] = vidinfo['data-title']
        tempdict['owner'] = vidinfo.find("div", {"class": "pl-video-owner"}).find("a").text
        tempdict['id'] = vidinfo['data-video-id']
        """
        video = {
            "type": "youtube",
            "title": vidinfo['data-title'],
            "owner": vidinfo.find("div", {"class": "pl-video-owner"}).find("a").text,
            "id": vidinfo['data-video-id']
        }
        vidlist.append(video)
    
    playlist = {
        "type": "youtube",
        "id": playlistid,
        "list": vidlist
    }
    return playlist

def convert_playlist(playlist, processes):
    # TODO: deploy api method
    searchlist = [f"{video['owner']} - {video['title']}" for video in playlist['list']]
    vidlist = multiprocessing.Pool(processes).map(search_noapi, searchlist)
    playlist['list'] = vidlist
    return playlist

def search_noapi(query):
    """
    Searches the query from youtube website(not API),
    grabs first result, form it nicely and return it.
    """
    url = f"https://youtube.com/results?search_query={query}"
    r = requests.get(url)
    soup = bs(r.text, "html.parser")
    try:
        playlist = soup.find("ol", {"class": "item-section"}).find_all("div", {"class": "yt-lockup"})
        vidinfo = playlist[0]
        title = vidinfo.find("h3", {"class": "yt-lockup-title"})
        title.find("span").extract()
        video = {
            'type' : "youtube",
            'title' : title.text,
            'owner' : vidinfo.find("div", {"class":"yt-lockup-byline"}).find("a").text,
            'id' : vidinfo['data-context-item-id']
        }
        return video
    except:
        print(f"An error has occured while searching {query}. Retrying...")
        time.sleep(1)
        return search_noapi(query)