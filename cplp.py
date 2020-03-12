import os
import json
import time
import module
import random
import argparse
import keyinput
from selenium.webdriver import Firefox
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.firefox.options import Options 

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
    return printtxt, pos

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
parser_get.add_argument("-p", "--processes", nargs = "?", default = 4, type = int, 
                        help = "Amounts of processes to be used while performing parallel\
                        functions. default is 4.")

if __name__ == "__main__":
    args = parser.parse_args()

    if args.mode == "play":
        playlist = [video for alias in args.list
                        for video in json.load(
                            open(os.path.join(
                                PATH, "playlist", f"{alias}.playlist")))['list']]
        options = Options()
        options.headless = args.debug
        options.set_preference("media.autoplay.default", 0)
        driver = Firefox(options = options, executable_path = DRIVER)
        try:
            open(os.path.join(PATH, "adblocker.xpi"))
            driver.install_addon(os.path.join(PATH, "adblocker.xpi"))
        except:pass
        tab = {}
        # This will be used to add different tabs used by providers
        module.youtube.play.prepare_tab(driver)
        tab['youtube'] = driver.current_window_handle
        printtxt = ""
        while True:
            if args.shuffle:
                random.shuffle(playlist)
            num = 0
            while num < len(playlist):
                video = playlist[num]
                printtxt_prev = printtxt
                printtxt = f"\rNow Playing {video['title']} by {video['owner']}"
                printtxt += " " * (len(printtxt_prev.encode()) - len(printtxt.encode()))
                print(printtxt)
                provider = getattr(module, video['type']).play
                driver.switch_to.window(tab[video['type']])
                provider.prepare_play(video['id'], driver)

                pos = 0
                status = 0
                playing = True 
                fulltime = provider.get_duration(driver)

                while not provider.is_finished(driver):
                    curtime = provider.get_current_time(driver)
                    printtxt_prev = printtxt
                    printtxt, pos = status_text(video['title'], pos, curtime, fulltime, playing)
                    printtxt += " " * (len(printtxt_prev.encode()) - len(printtxt.encode()))
                    print(printtxt, end = "")
                    key = keyinput.listen_key(1)
                    if key != None:
                        key = key.upper()
                        if key == " ":
                            if playing:
                                provider.pause(driver)
                                playing = False
                            else:
                                provider.play(driver)
                                playing = True
                        elif key == "Q":
                            status = 1
                            break
                        elif key == "E":
                            break
                provider.prepare_finish(driver)
                if status == 1:
                    num -= 1
                else:
                    num += 1

            if not args.repeat:
                break

    elif args.mode == "get":
        if not "playlist" in os.listdir():
            os.mkdir("playlist")
        """
        check if there's at least 1 argument and every argument contains :
        """
        if not (args.youtube or args.spotify):
            parser_get.error("You have to input at least 1 playlist")
        if args.youtube:
            for playlistinfo in args.youtube:
                print("Getting", playlistinfo, "...")
                split = playlistinfo.split(":")
                if len(split) == 1:
                    parser_get.error("Alias must be specified in playlist")
                elif len(split) != 2:
                    parser_get.error("Alias can't contain character ':'")
                playlistid, alias = split
                playlist = module.youtube.get.get_playlist(playlistid)
                json.dump(playlist, open(os.path.join(PATH, "playlist", f"{alias}.playlist"), "w"),
                          indent = 4)
        if args.spotify:
            for playlistinfo in args.spotify:
                print("Getting", playlistinfo, "...")
                split = playlistinfo.split(":")
                if len(split) == 1:
                    parser_get.error("Alias must be specified in playlist")
                elif len(split) != 2:
                    parser_get.error("Alias can't contain character ':'")
                playlistid, alias = split
                playlist = module.spotify.get.get_playlist(playlistid)
                #rtnlist = [search_youtube_noapi(query) for query in searchlist] <= Without multiprocessing
                playlist = module.youtube.get.convert_playlist(playlist, args.processes)
                json.dump(playlist, open(os.path.join(PATH, "playlist", f"{alias}.playlist"), "w"),
                          indent = 4)