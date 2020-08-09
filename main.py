"""
Spotify Downloader
"""
from __future__ import unicode_literals
import os
import json
import argparse
import time
import random
from youtubesearchpython import SearchVideos
import youtube_dl
from youtube_dl.utils import DownloadError
from youtube_dl.utils import ExtractorError
import spotipy
import logging

import discogs_client

from config import CLIENT_ID
from config import CLIENT_SECRET
from config import DISCOGS_TOKEN

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_connection(client_name):
    """
    Creates a connection to the Discogs API
    """
    conn = discogs_client.Client(client_name, user_token=DISCOGS_TOKEN)
    return conn.identity()


def search_stuff(conn, artist, title):
    """
    Search Discogs for artist title and youtube link if it exists.
    """
    results = conn.search(artist=artist, track=title)
    for result in results:
        try:
            if result.videos:
                logger.info(','.join(result.video))
                for video in result.videos:
                    return video.url
        except:  # TODO: add proper exception
            logger.info("no videos")
    return False


def discogs(client_name, artist, title):
    """
    Discogs entrypoint
    """
    con = create_connection(client_name)
    return search_stuff(con.client, artist, title)


def get_args():
    """
    Parse Arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--spotiuri', action='store',
                        help='Playlist\'s  Spotify Uri')
    parser.add_argument('-p', '--spotiplaylistId', action='store',
                        help='Playlist\'s  Spotify id')
    parser.add_argument('-d', '--dir_name', required=False, action='store',
                        help='Directory name')
    my_args = parser.parse_args()

    if not(my_args.spotiuri or my_args.spotiplaylistId):
        parser.error('Need URI or ID')

    return my_args


def changenames(dir_name):
    """
    Fix names of downloaded music and move them to output directory.
    """
    songs = [i for i in [s for s in os.listdir("./")
                         if os.path.isfile(os.path.join("./", s))]
             if "mp3" in i]

    count_song = 0
    for song in songs:
        # [''.join(s.split('-')[0:-1]) + ".mp3" for s in songs ]
        count_song += 1
        new_s = f"{count_song:02d}-" + ''.join(song.split('-')[0:-1]) + ".mp3"
        os.rename(os.path.join("./", song), os.path.join(dir_name, new_s))


def create_dir(dir_name):
    """
    Creates dir if it does not exist
    """
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def download_songs(spotify_info):
    """
    Download song
    """
    failed = list()
    print("\nDownloading songs...\n")
    counter = 0
    for item in spotify_info["items"]:
        song_name = item["track"]["artists"][0]["name"]
        song_artist = item["track"]["name"]
        wholename = "%s %s" % (song_name, song_artist)
        counter += 1
        print("%s)\t%s" % (counter, wholename))
        time.sleep(random.random()*10)
        track = discogs('rb', song_artist, song_name)
        if not track:
            logger.warning("No release found on discogs, searching only youtube")
            track = get_yt_link(song_artist, song_name)

        if track:
            if not yt_dl(track):
                logger.error(f"This track failed: {wholename}")
                failed.append(f"{song_artist} {song_name}")
        else:
            logger.error(f"This track failed: {wholename}")
            failed.append(f"{song_artist} {song_name}")


def yt_dl(vid):
    """
    Download yt music

    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': 'True',
        'no-playlist': 'True',
        'audio-format': 'best',
        'extract-audio': 'True',
        'addmetadata': 'True',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320'
        }]}

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([vid])
        except DownloadError as dl_e:
            logger.error(f"Couldn't download: {dl_e}")
            return False
        except ExtractorError as extract_e:
            logger.error(f"Couldn't extract: {extract_e}")
            return False
        return True


def get_yt_link(artist, song):
    """
    Return YT Link to download
    """
    search = SearchVideos(str(artist + " " + song),
                          offset=1,
                          mode="json",
                          max_results=1)
    try:
        return search.links[0]
    except IndexError as err:
        logger.warning(f"No videos to download found: {err}")


def main():
    """
    main function
    """
    args = get_args()
    dir_name = args.dir_name

    if args.spotiuri:
        playlist_id = args.spotiuri.split(":")[len(args.spotiuri.split(":"))-1]

    if args.spotiplaylistId:
        playlist_id = args.spotiplaylistId

    if not dir_name:
        dir_name = 'output'

    tok = spotipy.oauth2.SpotifyClientCredentials(client_id=CLIENT_ID,
                                                  client_secret=CLIENT_SECRET)

    access_token = tok.get_access_token(as_dict=False)

    result = os.popen('curl -s -X GET "https://api.spotify.com/v1/playlists/'
                      + playlist_id + '/tracks" -H "Authorization: Bearer '
                      + access_token + '"').read()
    create_dir(dir_name)
    download_songs(json.loads(result))
    changenames(dir_name)


if __name__ == "__main__":
    main()
