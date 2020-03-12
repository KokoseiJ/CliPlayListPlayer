import os
import json
import requests
from base64 import b64encode

PATH = os.path.dirname(os.path.abspath(__file__))

def get_token():
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

def get_playlist(playlistid):
    """
    Get playlist from spotify API, form it as 'artists - song name' style and return it
    as I can't find a way to play from spotify directly in a command line.
    Should be rewritten to get song IDs from spotify when I somehow find a way to do it
    """
    token = get_token()
    vidlist = []
    url = f"https://api.spotify.com/v1/playlists/{playlistid}/tracks?fields=items(track(name, id, artists)), next"
    while True:
        r = requests.get(url, headers = {"Authorization": "Bearer " + token})
        response = json.loads(r.text)
        for item in response['items']:
            item = item['track']
            track = {
                "type": "spotify",
                "title": item['name'],
                "owner": ", ".join([artist['name'] for artist in item['artists']]),
                "id": item["id"]
            }
            vidlist.append(track)
        if response['next']:
            url = response['next']
        else:
            break
    playlist = {
        "type": "spotify",
        "id": playlistid,
        "list": vidlist
    }
    return playlist

def convert_playlist(playlist):
    return None