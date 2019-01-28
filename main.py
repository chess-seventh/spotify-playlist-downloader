import os
import sys
import json
import argparse


def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('-a', '--access_token', required=True, action='store', help='Access token')
	parser.add_argument('-u', '--spotiuri', required=True, action='store', help='Playlist\'s  Spotify Uri')
	parser.add_argument('-d', '--dir_name', required=True, action='store', help='Directory name')
	my_args = parser.parse_args()
	return my_args

def create_dir(dir_name):
	if not os.path.exists(dir_name):
		os.makedirs(dir_name)


def download_songs(spotify_info, dir_name):
	print("\nDownloading songs...\n")
	counter = 0
	for item in spotify_info["items"]:
		song_name, song_artist = item["track"]["name"],item["track"]["artists"][0]["name"]
		wholename = "%s by %s" % (song_name, song_artist)
		counter += 1
		os.system('cd '+dir_name+' && instantmusic -s "'+wholename+'" -q  > /dev/null 2>&1')
		print ("%s)\t%s" %(counter, wholename))

def main():
	aux_playlist_id = sys.argv[2].split(":")
	playlist_id = aux_playlist_id[len(aux_playlist_id)-1]
	
	args = get_args()
	access_token = args.access_token
	playlist_id = args.spotiuri.split(":")[len(args.spotiuri.split(":"))-1]
	dir_name = args.dir_name 
	result = os.popen('curl -s -X GET "https://api.spotify.com/v1/playlists/'+playlist_id+'/tracks" -H "Authorization: Bearer '+access_token+'"').read()
	create_dir(dir_name)
	download_songs(json.loads(result), dir_name)

if __name__ == "__main__":
	main()