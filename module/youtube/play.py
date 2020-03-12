IS_PLAYABLE = True
PLAYER = "document.getElementById('movie_player')"

def prepare_tab(driver):
    # I mean, Some videos can't be played in /embed somehow and I can't find a way to fix it
        # So let's just use Rick Astley - Never Gonna Give You Up's page to play it lol
        # If something bad happens this will end up rickrolling the user
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    driver.get(url)
    while driver.execute_script(f"return {PLAYER}.getPlayerState()") != 1:pass
    driver.execute_script(f"{PLAYER}.pauseVideo()")
    return

def prepare_play(videoid, driver):
    driver.execute_script(f"{PLAYER}.loadVideoById('{videoid}')")

def get_duration(driver):
    duration = None
    while not duration:
        duration = driver.execute_script(f"return {PLAYER}.getDuration()")
    return duration

def get_current_time(driver):
    return driver.execute_script(f"return {PLAYER}.getCurrentTime()")

def pause(driver):
    return driver.execute_script(f"{PLAYER}.pauseVideo()")

def play(driver):
    return driver.execute_script(f"{PLAYER}.playVideo()")

def prepare_finish(driver):
    driver.execute_script(f"{PLAYER}.playVideo()")
    driver.execute_script(f"{PLAYER}.pauseVideo()")

def is_finished(driver):
    return driver.execute_script(f"return {PLAYER}.getPlayerState()") == 0
