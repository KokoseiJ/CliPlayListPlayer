import os
import sys
import json
import time
import queue
import random
import argparse
import keyinput
import requests
import selenium
import textwrap
import multiprocessing
from base64 import b64encode
from bs4 import BeautifulSoup as bs
from selenium.webdriver import Firefox
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.firefox.options import Options    

def clear_line():
    print(" " * os.get_terminal_size().columns, end = "\r")
    return

def sec_convert(sec):
    if sec > 3600:
        return time.strftime("%H:%M:%S", time.gmtime(sec))
    else:
        return time.strftime("%M:%S", time.gmtime(sec))

def status_text(songname, pos, curtime, fulltime, playing, name_length = 15):
    percent = int(curtime / fulltime * 20)
    if len(songname) > name_length:
        nametxt = (songname + "  " + songname)[pos:pos + name_length]
        pos += 1
        if pos == len(songname) + 2:
            pos = 0
    else:
        nametxt = songname
    if playing:
        status = "Playing"
    else:
        status = "Paused"
    statusbar = "[" + "=" * percent + "-" * (20 - percent) + "]"
    printtxt = f"\r{nametxt} {statusbar} {sec_convert(curtime)}/{sec_convert(fulltime)} {status}"
    printtxt += " " * (os.get_terminal_size().columns - len(printtxt))
    print(printtxt, end = "")
    return pos

def search_youtube_noapi(query):
    """
    Searches the query from youtube website(not API),
    grabs first result, form it nicely and return it.
    """
    print(query)
    url = f"https://youtube.com/results?search_query={query}"
    r = requests.get(url)
    soup = bs(r.text, "html.parser")
    try:
        playlist = soup.find("ol", {"class": "item-section"}).find_all("div", {"class": "yt-lockup"})
        vid = playlist[0]
        title = vid.find("h3", {"class": "yt-lockup-title"})
        title.find("span").extract()
        tempdict = {}
        tempdict['type'] = "youtube"
        tempdict['title'] = title.text
        tempdict['owner'] = vid.find("div", {"class":"yt-lockup-byline"}).find("a").text
        tempdict['id'] = vid['data-context-item-id']
        return tempdict
    except:
        print("An error has occured. Retrying...")
        time.sleep(1)
        return search_youtube_noapi(query)
def get_token_spotify():
    """
    get an access token from spotify API by using Client ID/Secret.
    also, it stores ID as ClientID:Secret format and reuses in next usage.
    I did my best to get access token in CLI app so do not blame me please.
    """
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
                      headers = {"Authorization": f"Basic {cli_b64}"})
    token = json.loads(r.text)['access_token']
    return token

def get_playlist_spotify(token, playlistid):
    """
    Get playlist from spotify API, form it as 'artists - song name' style and return it
    as I can't find a way to play from spotify directly in a command line.
    Should be rewritten to get song IDs from spotify when I somehow find a way to do it
    """
    rtnlist = []
    url = f"https://api.spotify.com/v1/playlists/{playlistid}/tracks?fields=items(track(name, artists)), next"
    while True:
        r = requests.get(url, headers = {"Authorization": "Bearer " + token})
        res = json.loads(r.text)
        playlist = res['items']
        for item in playlist:
            title = item['track']['name']
            artists = ", ".join([artist['name'] for artist in item['track']['artists']])
            searchstr = artists + " - " + title
            if not searchstr in rtnlist:
                rtnlist.append(artists + " - " + title)
        if res['next']:
            url = res['next']
        else:
            break
    return rtnlist

def get_playlist_yt_noapi(driver, playlistid):
    """
    Connect to the playlist page, press "Load more" button until that button
    doesn't exist anymore, make a dictionary out of it and save it as a text
    file.
    """
    url = f"https://www.youtube.com/playlist?list={playlistid}"
    driver.get(url)
    while True:
        try:
            button = driver.find_element_by_class_name("yt-uix-load-more")
        except selenium.common.exceptions.NoSuchElementException:
            break
        button.click()
    soup = bs(driver.page_source, "html.parser")
    playlist = []
    for vid in soup.find_all("tr", {"class": "pl-video"}):
        tempdict = {}
        tempdict['type'] = "youtube"
        tempdict['title'] = vid['data-title']
        tempdict['owner'] = vid.find("div", {"class": "pl-video-owner"}).find("a").text
        tempdict['id'] = vid['data-video-id']
        playlist.append(tempdict)
    
    rtndict = {
        "type": "youtube",
        "id": playlistid,
        "list": playlist
    }
    return rtndict

def play_yt(driver, video):
    """
    Switch to first tab, get youtube player and use loadVideoById function to load video,
    use getPlayerState function to check if video has finished and return if true.
    """
    driver.execute_script(f"document.getElementById('movie_player').loadVideoById('{video['id']}')")
    rtnvalue = 0
    playing = True
    pos = 0
    # getDuration() value will return 0 while loading metadata and that causes the Exception
    # This will prevent it from being 0
    fulltime = 0
    while not fulltime:
        fulltime = driver.execute_script("return document.getElementById('movie_player').getDuration()")
    while True:
        if driver.execute_script("return document.getElementById('movie_player').getPlayerState()") == 0:
            break
        curtime = driver.execute_script("return document.getElementById('movie_player').getCurrentTime()")
        pos = status_text(video['title'], pos, curtime, fulltime, playing)
        key = keyinput.listen_key(1)
        if key != None:
            key = key.upper()
            if key == " ":
                if playing:
                    driver.execute_script("document.getElementById('movie_player').pauseVideo()")
                    playing = False
                else:
                    driver.execute_script("document.getElementById('movie_player').playVideo()")
                    playing = True
            elif key == "Q":
                rtnvalue = 1
                break
            elif key == "E":
                rtnvalue = 0
                break
    # Workaround to stop autoplay.
    driver.execute_script("document.getElementById('movie_player').playVideo()")
    driver.execute_script("document.getElementById('movie_player').pauseVideo()")
    return rtnvalue

PATH = os.path.dirname(os.path.abspath(__file__))

if os.name == "nt":
    DRIVER = os.path.join(PATH, "geckodriver.exe")
else:
    DRIVER = os.path.join(PATH, "geckodriver")

parser = argparse.ArgumentParser(
            description = "Load playlist from various sites and play it using youtube.")
subparsers = parser.add_subparsers(required = True,
                                   dest = "mode",
                                   metavar = "MODE",
                                   help = "Sets mode of the program.\
                                   Use 'get' to get the playlist,\
                                   Use 'play' to play the playlist.")

parser_play = subparsers.add_parser('play', help = "Plays Playlist")
parser_play.add_argument("list", nargs = "+", metavar = "LIST",
                         help = "List of the playlist to play. You can input multiple lists.")
parser_play.add_argument("-r", "--repeat", action = "store_true",
                         help = "This flag will repeatedly play the list.")
parser_play.add_argument("-s", "--shuffle", action = "store_true",
                         help = "This flag will shuffle the playlist.\
                         If repeat is enabled, list will be reshuffled\
                         after the every loop.")
parser_play.add_argument("-d", "--debug", action = "store_false",
                    help = "flag for debugging. this will disable headless option in browser.")

parser_get = subparsers.add_parser('get', help = "Gets playlist from youtube/spotify.\
                                   You must use 'playlistid:alias' form to specify the\
                                   alias of the playlist.")
parser_get.add_argument("-y", "--youtube", nargs = "*",
                        help = "Lists of youtube playlists to get.")
parser_get.add_argument("-s", "--spotify", nargs = "*",
                        help = "Lists of spotify playlists to get.")

if __name__ == "__main__":
    args = parser.parse_args()

    if args.mode == "play":
        playlist = [video for alias in args.list
                        for video in json.load(
                            open(os.path.join(
                                PATH, "playlist", f"{alias}.playlist")))['list']]
        # I mean, Some videos can't be played in /embed somehow and I can't find a way to fix it
        # So let's just use Rick Astley - Never Gonna Give You Up's page to play it lol
        # If something bad happens this will end up rickrolling the user
        url_yt = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        options = Options()
        options.headless = args.debug
        options.set_preference("media.autoplay.default", 0)
        driver = Firefox(options = options, executable_path = DRIVER)
        try:
            open(os.path.join(PATH, "adblocker.xpi"))
            driver.install_addon(os.path.join(PATH, "adblocker.xpi"))
        except:pass
        driver.get(url_yt)
        driver.execute_script("document.getElementById('movie_player').pauseVideo()")

        while True:
            if args.shuffle:
                random.shuffle(playlist)
            num = 0
            while num < len(playlist):
                video = playlist[num]
                printtxt = f"\rNow Playing {video['title']} by {video['owner']}"
                printtxt += " " * (os.get_terminal_size().columns - len(printtxt))
                print(printtxt)
                rtn = play_yt(driver, video)
                if rtn == 1:
                    if num == 0:
                        num = len(playlist)
                    num -= 1
                else:
                    num += 1
            if not args.repeat:
                break

    # TODO: use same driver for every loop of "get" thing
    elif args.mode == "get":
        """
        check if there's at least 1 argument and every argument contains :
        """
        if not (args.youtube or args.spotify):
            parser_get.error("You have to input at least 1 playlist")
        if args.youtube:
            options = Options()
            options.headless = True
            options.set_preference("general.useragent.override", "")
            driver = Firefox(executable_path = DRIVER, options = options)
            for playlist in args.youtube:
                print("Getting", playlist, "...")
                split = playlist.split(":")
                if len(split) == 1:
                    parser_get.error("Alias must be specified in playlist")
                elif len(split) != 2:
                    parser_get.error("Alias can't contain character ':'")
                playlistid, alias = split
                rtndict = get_playlist_yt_noapi(driver, playlistid)
                json.dump(rtndict, open(os.path.join(PATH, "playlist", f"{alias}.playlist"), "w"),
                          indent = 4)
        if args.spotify:
            delay = 0
            for playlist in args.spotify:
                print("Getting", playlist, "...")
                playlistid, alias = playlist.split(":")
                token = get_token_spotify()
                searchlist = get_playlist_spotify(token, playlistid)
                #rtnlist = [search_youtube_noapi(query) for query in searchlist] <= Without multiprocessing
                rtnlist = multiprocessing.Pool(100).map(search_youtube_noapi, searchlist)
                rtndict = {
                    "type": "spotify",
                    "id": playlistid,
                    "list": rtnlist
                }
                json.dump(rtndict, open(os.path.join(PATH, "playlist", f"{alias}.playlist"), "w"),
                          indent = 4)
