import selenium
import os
import time
import random
import json
import sys
import argparse
import textwrap
import requests
from selenium.webdriver import Firefox
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup as bs
from base64 import b64encode

def get_token_spotify():
    # Implemented just in case
    try:
        cli = open(os.path.join(PATH, "spotify_client")).read()
    except:
        print("spotify_client file was not found. creating new one...")
        cli_id = input("Client ID: ")
        cli_secret = input("Client Secret: ")
        print("Saving...", end = "")
        cli = cli_id + ":" + cli_secret
        open(os.path.join(PATH, "spotify_client"), "w").write(cli)
        print("Done.")
    cli_b64 = b64encode(cli.encode()).decode()
    r = requests.post("https://accounts.spotify.com/api/token",
                      data = {"grant_type": "client_credentials"},
                      headers = {"Authorization": "Basic {}".format(cli_b64)})
    token = json.loads(r.text)['access_token']
    return token

def get_playlist_spotify(token, playlistid):
    searchlist = []
    url = "https://api.spotify.com/v1/playlists/{}/tracks?fields=items(track(name, artists)), next".format(playlistid)
    while True:
        r = requests.get(url, headers = {"Authorization": "Bearer " + token})
        print(r.text)
        res = json.loads(r.text)
        playlist = res['items']
        for item in playlist:
            title = item['track']['name']
            artists = ", ".join([artist['name'] for artist in item['track']['artists']])
            searchstr = artists + " - " + title
            if not searchstr in searchlist:
                searchlist.append(artists + " - " + title)
        if res['next']:
            url = res['next']
        else:
            break
    print(searchlist)

def get_playlist_yt_noapi(playlistid, alias):
    """
    Set User-Agent value to 0, Connect to the playlist page, press "Load more"
    button until that button doesn't exist anymore, make a dictionary out of it
    and save it as a text file.
    """
    url = "https://www.youtube.com/playlist?list=" + playlistid
    print("Preparing a driver...")
    options = Options()
    options.headless = True
    options.set_preference("general.useragent.override", "")
    driver = Firefox(executable_path = DRIVER, options = options)
    print("Connecting to youtube...")
    driver.get(url)
    while True:
        try:
            button = driver.find_element_by_class_name("yt-uix-load-more")
        except selenium.common.exceptions.NoSuchElementException:
            break
        print("Loading more videos...")
        button.click()
    print("Parsing video list...")
    soup = bs(driver.page_source, "html.parser")
    vidlist = []
    for vid in soup.find_all("tr", {"class": "pl-video"}):
        tempdict = {}
        tempdict['title'] = vid['data-title']
        tempdict['owner'] = vid.find("div", {"class": "pl-video-owner"}).find("a").text
        tempdict['id'] = vid['data-video-id']
        vidlist.append(tempdict)
    rtndict = {
        "type": "youtube",
        "id": playlistid,
        "list": vidlist
    }
    print("Saving it...")
    with open(os.path.join(PATH, "playlist", alias + ".playlist"), "w") as f:
        f.write(json.dumps(rtndict))
    print("Finished.") 

def play(vidlist, shuffle = False, repeat = False, debug = False):
    url = "https://www.youtube.com/watch?v=" + vidlist[0]['id']
    options = Options()
    if not debug:
        options.headless = True
    options.set_preference("media.autoplay.default", 0)
    driver = Firefox(executable_path = DRIVER, options = options)
    try:
        open(os.path.join(PATH, "adblocker.xpi"))
        driver.install_addon(os.path.join(PATH, "adblocker.xpi"))
    except:
        print("adblocker addon was not found. Running without adblock...")
    driver.get(url)
    while True:
        if shuffle:
            print("Shuffling the list...")
            random.shuffle(vidlist)
        for video in vidlist:
            print("Now Playing: " + video['title'] + " by " + video['owner'])
            driver.switch_to.window(driver.window_handles[0])
            driver.execute_script("document.getElementById('movie_player').loadVideoById('" + video['id'] + "')")
            status = True
            while True:
                if driver.execute_script("return document.getElementById('movie_player').getPlayerState()") == 0:
                    break
                time.sleep(1)
        if repeat:
            continue
        else:
            break

PATH = os.path.dirname(os.path.abspath(__file__))
if sys.platform in ["win32", "cygwin"]:
    DRIVER = os.path.join(PATH, "geckodriver.exe")
else:
    DRIVER = os.path.join(PATH, "geckodriver")

parser = argparse.ArgumentParser(
            formatter_class = argparse.RawDescriptionHelpFormatter,
            description = textwrap.dedent("""\
            Load playlist from various sites and
            play it using youtube.

            Examples:
              # This will play both 'citypop' and 'mashup' list with repeat/shuffle on.
              %(prog)s play citypop mashup --repeat --shuffle
              # This will save first playlist as 'citypop', second one as 'mashup'
              %(prog)s get [playlistid1] [playlistid2] --alias citypop mashup"""))

parser.add_argument("mode", choices = ["get", "play"], metavar = "MODE",
                    help = "Sets mode of the program. Use 'get' to get the playlist,\
                    Use 'play' to play the playlist.")
parser.add_argument("list", nargs = "+", metavar = "LIST",
                    help = "List of the playlist to play. You can type single or multiple lists\
                    to play. Use alias in 'play' mode, Use playlist id in 'get' mode.")
parser.add_argument("-Y", "--youtube", action = "store_true",
                    help = "Use this flag to get the playlist from youtube. This is the default.\
                    ignored in 'play' mode.")
parser.add_argument("-S", "--spotify", action = "store_true",
                    help = "Use this flag to get the playlist from spotify. ignored in 'play' mode.")
parser.add_argument("-A", "--alias", nargs = "*",
                    help = "Use this flag to pre-define the alias of the list. You can define multiple\
                    aliases. You can also use 'playlistid:alias' form in the LIST argument,\
                    arguments of this flag will be ignored in that list. Ignored in 'play' mode.")
parser.add_argument("-r", "--repeat", action = "store_true",
                    help = "This flag will repeatedly play the list. If shuffle is enabled,\
                    it will reshuffle the list after the every loop. Ignored in 'get' mode.")
parser.add_argument("-s", "--shuffle", action = "store_true",
                    help = "This flag will shuffle the playlist. Ignored in 'get' mode.")
parser.add_argument("-d", "--debug", action = "store_true",
                    help = "flag for debugging. this will disable headless option.")
if __name__ == "__main__":
    args = parser.parse_args()

    if args.mode == "play":
        vidlist = [vid for alias in args.list
                    for vid in json.load(
                        open(os.path.join(PATH, "playlist", alias + ".playlist")))['list']]
        play(vidlist, args.shuffle, args.repeat, debug = args.debug)

    # TODO: use same driver for every loop of "get" thing

    elif args.mode == "get":
        if not (args.youtube or args.spotify):
            youtube = True
        else:
            youtube = args.youtube
        if youtube:
            for plid, alias in zip(args.list, args.alias):
                get_playlist_noapi(plid, alias)
        elif args.spotify:
            token = get_token_spotify()
            for plid in args.list:
                get_playlist_spotify(token, plid)
