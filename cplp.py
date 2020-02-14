import selenium
import os
import time
import random
import json
from selenium.webdriver import Firefox
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup as bs

AGENT = ""
path = os.path.dirname(os.path.abspath(__file__))

def get_playlist_noapi(playlistid, executable_path = "./geckodriver"):
	# Generate a URL
	url = "https://www.youtube.com/playlist?list=" + playlistid
	print("Preparing a driver...")
	# Set browser to headless mode, set User-Agent to blank
	options = Options()
	options.headless = True
	options.set_preference("general.useragent.override", AGENT)
	# Get a driver
	driver = Firefox(executable_path = executable_path, options = options)
	# join url
	print("Connecting to youtube...")
	driver.get(url)
	# Check if there is "Load more" button
	while True:
		try:
			button = driver.find_element_by_class_name("yt-uix-load-more")
		except selenium.common.exceptions.NoSuchElementException:
			break
		print("Loading more videos...")
		button.click()
	# Get a list of the video
	print("Parsing video list...")
	soup = bs(driver.page_source, "html.parser")
	# idlist = [x['data-video-id'] for x in soup.find_all("tr", {"class": "pl-video"})]
	idlist = []
	for item in soup.find_all("tr", {"class": "pl-video"}):
		videoid = item['data-video-id']
		title = item['data-title']
		owner = item.find("div", {"class": "pl-video-owner"}).find("a").text
		tmpdict = {"id": videoid, "title": title, "owner": owner}
		idlist.append(tmpdict)
	print("Finished.")

	return idlist

def play(vidlist, executable_path = "./geckodriver", addon = None):
	# We will use embed page to play
	url = "https://www.youtube.com/watch?v=" + vidlist[0]['id'] + "?autoplay=1"
	# Set browser to headless mode, enable autoplay
	options = Options()
	options.headless = True
	options.set_preference("media.autoplay.default", 0)
	# get a driver
	driver = Firefox(executable_path = executable_path, options = options)
	if addon:
		driver.install_addon(addon)
	# Join URL
	driver.get(url)
	print("press Ctrl + C to play a next song.")
	for video in vidlist:
		print("Now Playing " + video['owner'] + " - " + video['title'])
		# Switch to first tab
		driver.switch_to.window(driver.window_handles[0])
		# Play a video and wait until it finishes
		driver.execute_script("document.getElementById('movie_player').loadVideoById('" + video['id'] + "')")
		status = True
		while True:
			# check if video has ended for every seconds
			if driver.execute_script("return document.getElementById('movie_player').getPlayerState()") == 0:
				break
			time.sleep(1)

cmd = input("Input your command: ")
splitcmd = cmd.split()
if splitcmd[0] == "save":
	if len(splitcmd) < 3:
		print("Not enouogh input")
		exit(1)
	idlist = get_playlist_noapi(splitcmd[1])
	idlist_json = json.dumps(idlist)
	print("Saving file...")
	with open(os.path.join(path, "playlist", splitcmd[2] + ".txt"), "w") as f:
		f.write(idlist_json)
elif splitcmd[0] == "play":
	vidlist = json.loads(open(os.path.join(path, "playlist", splitcmd[1] + ".txt")).read())
	if splitcmd[2] == "shuffle":
		random.shuffle(vidlist)
	play(vidlist, addon = os.path.join(path, "adblocker.xpi"))