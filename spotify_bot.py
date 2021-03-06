"""spotify_bot.py

A TeamTalk controller for Spotify.
Only works with premium accounts.
Also requires another TeamTalk instance capable of routing system audio. The 
process for doing so is out of the scope of these notes. It is my hope that 
this will someday be unnecessary, however.

Consult the readme for comprehensive setup instructions.
Basically just run this script, edit the generated configuration file, then run again.
"""

help = """Every parameter enclosed in brackets ([]) is optional
play [uri]: Starts playback. If uri is provided, starts playing from the specified spotify link, can start with http:// or spotify:.
pause: Pauses playback.
previous/next: Cycles between tracks.
volume percentage: Sets the output volume (between 0 and 100).
track query: Searches for and plays a track.
artist query: Searches for and plays tracks by an artist.
playlist query: Searches for and plays tracks from a playlist.
queue query: Searches for and adds the next track to the playback queue.
shuffle yes/on/1|no/off/0: Enables or disables shuffling.
playing: Displays info about the currently playing track.
If on mac OS, send the word mac to the channel to receive a PM"""


## authentication
client_id = "52569438780b4497bdd72a09954d1030"
client_secret = "f090e040c95842e3a31f26d86bf627a8"
redirect_uri = "http://localhost:9999"
scopes = "user-modify-playback-state user-read-currently-playing user-read-playback-state user-read-private"
cache_path = "spotify.cache"
client_name = "TeamTalkBotClient"


import sys
import os.path
import datetime
import time
import json
import configparser
import spotipy
import teamtalk
import utils
from utils import *
from spotipy.oauth2 import SpotifyOAuth

spec = """# TeamTalk Spotify Bot Configuration
# Sections starting with # are comments and not processed directly
# Uncomment (remove the # from) every line that is not an explanation

[general]
# The server's address
# host = example.com
# The server's TCP port
# port = 10333
# Login Info
# nickname = Spotify Bot
# username = me
# password = password
# a list of users disallowed from sending messages for abuse prevention
# example: ["bob", "Alice"]
# banned_users = []
# The case sensative name, or ID, of a channel to join on login
# /Stereo/ or 1 are valid
# autojoin = 
# The password for the channel that will be automatically joined
# autojoin_pass = 

[advanced]
# Only edit if you know what you're doing, as things can break easily
# client_id = 
# client_secret = 
# redirect_uri = 
# cache_path = 
"""

# Globals
config = None
## Config sections for convenience
general = None
advanced = None

banned_users = None
t = teamtalk.TeamTalkServer()


def load_config(file):
	global config, general, advanced, banned_users
	try:
		config = configparser.ConfigParser()
	except configobj.Error as exc:
		print("There was an error validating the config")
		print(exc)
	loaded = config.read(file)
	if not loaded:
		print(file + " does not exist")
		# messy but gets the job done for now
		with open(file, "w") as f:
			f.write(spec)
		print("Created a configuration file")
		print("Edit it and try running again")
		sys.exit(1)
	if not "general" in config.sections() or not "advanced" in config.sections():
		print("Malformed configuration file. Fix or delete it and try again.")
		sys.exit(1)
	general = config["general"]
	advanced = config["advanced"]
	# check for only the bare minimum required to run
	if (
		not general.get("host")
		or not general.get("port")
		or not general.get("nickname")
	):
		print("Some required values were not found in the configuration. Fix or delete it and try again.")
		sys.exit(1)
	# Expand to a list
	# hack: Since configparser doesn't support lists automatically, try feeding to json
	banned_users = json.loads(general.get("banned_users", "[]"))


class SpotifyBot:
	def __init__(self):
		self.auth = None
		self.spotify = None
		self.device = None
		self.device_id = None

	def init_spotify(self):
		self.auth = SpotifyOAuth(
			client_id=advanced.get("client_id", client_id),
			client_secret=advanced.get("client_secret", client_secret),
			redirect_uri=advanced.get("redirect_uri", redirect_uri),
			scope=scopes,
			cache_path=advanced.get("cache_path", cache_path),
		)
		self.spotify = spotipy.Spotify(auth_manager=self.auth)

	def find_device(self):
		"""Blocks until a device becomes available for playback."""
		devices = None
		while not devices:
			devices = self.spotify.devices()["devices"]
			time.sleep(1)
		return devices

	def select_device(self):
		"""Selects a device to be used for playback"""
		devices = self.spotify.devices()["devices"]
		if not devices:
			print("No playback devices found")
			print("Waiting for one to become available")
			devices = self.find_device()
		items = []
		for device in devices:
			items.append(device["name"] + ": " + str(device["volume_percent"]) + "%")
		i = menu("Select a device: ", items)
		self.device = devices[i]
		self.device_id = self.device["id"]
		print(self.device["name"] + " selected")

	def get_info(self, track):
		if "item" in track:
			item = track["item"]
		else:  # not current_user_playing_track
			item = track
		name = item["name"]
		# present if the passed track was obtained from a playback method
		if "progress_ms" in track:
			elapsed = datetime.timedelta(seconds=int(track["progress_ms"] / 1000))
		else:
			elapsed = "0:00:00"
		duration = datetime.timedelta(seconds=int(item["duration_ms"] / 1000))
		artists = [i["name"] for i in item["artists"]]
		artists = ", ".join(artists)
		return f"{artists} - {name} ({elapsed} - {duration})"

	@preserve_tracebacks
	def command_play(self, val=None):
		if val:
			# start_playback doesn't support passing tracks by context_uri for some dumb reason
			if is_track(val):
				self.spotify.start_playback(uris=[val], device_id=self.device_id)
			else:
				self.spotify.start_playback(context_uri=val, device_id=self.device_id)
		else:
			self.spotify.start_playback(device_id=self.device_id)
		return "playing"

	@preserve_tracebacks
	def command_pause(self, val=None):
		self.spotify.pause_playback(device_id=self.device_id)
		return "paused"

	@preserve_tracebacks
	def command_previous(self, val=None):
		self.spotify.previous_track(device_id=self.device_id)

	@preserve_tracebacks
	def command_next(self, val=None):
		self.spotify.next_track(device_id=self.device_id)

	@preserve_tracebacks
	def command_volume(self, val):
		if not val:
			return str(self.spotify.current_playback()["device"]["volume_percent"]) + "%"
		val = val.replace("%", "")
		if not val.isdigit():
			return "percentage argument must be a digit"
		val = int(val)
		if val < 0 or val > 100:
			return "percentage must be between 0 and 100, inclusive"
		self.spotify.volume(val, device_id=self.device_id)
		return "volume set"

	@preserve_tracebacks
	def command_artist(self, val):
		results = self.spotify.search(q=val, type="artist")
		items = results["artists"]["items"]
		if len(items) > 0:
			item = items[0]
			self.spotify.start_playback(device_id=self.device_id, context_uri=item["uri"])
			return "playing " + item["name"]
		else:
			return "unable to find an artist by that name"

	@preserve_tracebacks
	def command_track(self, val):
		results = self.spotify.search(q=val, type="track")
		items = results["tracks"]["items"]
		if len(items) > 0:
			# context_uri doesn't accept tracks for some reason
			item = items[0]
			self.spotify.start_playback(device_id=self.device_id, uris=[item["uri"]])
			return "playing " + self.get_info(item)
		else:
			return "unable to find a track by that name"

	@preserve_tracebacks
	def command_playlist(self, val):
		results = self.spotify.search(q=val, type="playlist")
		playlists = results["playlists"]["items"]
		if len(playlists) > 0:
			item = playlists[0]
			self.spotify.start_playback(context_uri=item["uri"], device_id=self.device_id)
			return f"playing {item['name']} by {item['owner']['display_name']}\n{item['description']}"

	@preserve_tracebacks
	def command_queue(self, val):
		if not val:
			return "no track provided"
		item = None
		if not is_track(val):
			results = self.spotify.search(q=val, type="track")
			items = results["tracks"]["items"]
			if len(items) > 0:
				item = items[0]
				val = item["uri"]
			else:
				return "unable to find a track by that name"
		self.spotify.add_to_queue(val, device_id=self.device_id)
		if not item:
			item = self.spotify.track(val)
		return "queued " + self.get_info(item)

	@preserve_tracebacks
	def command_playing(self, val=None):
		track = self.spotify.current_user_playing_track()
		return self.get_info(track)

	@preserve_tracebacks
	def command_shuffle(self, val):
		if val == "":
			return "value must be yes/no, on/off, etc"
		state = to_bool(val)
		self.spotify.shuffle(state, device_id=self.device_id)
		if state:
			return "now shuffling"
		else:
			return "shuffling disabled"


@t.subscribe("messagedeliver")
def message(server, params):
	content = params["content"]
	user = server.get_user(params["srcuserid"])
	nickname = user["nickname"]
	username = user["username"]
	if params["type"] == teamtalk.CHANNEL_MSG:
		if content.lower().strip() == "mac":
			server.user_message(user, "Ok. Type help for a list of commands.")
	if params["type"] != teamtalk.USER_MSG:
		return  # nothing to do
	if username in banned_users:
		server.user_message(user, "You do not currently have permission to use this bot")
		return
	parsed = str(content).split(" ")
	# our command parsing assumes a single message needs to be sent
	# due to TeamTalk message size constraints, we need to split these up
	if parsed[0].lower() == "help":
		for line in help.splitlines():
			# spam
			server.user_message(user, line)
		return
	func = getattr(sp, "command_" + parsed[0].lower(), None)
	if callable(func):
		res = func(" ".join(parsed[1:]))
		if res:
			server.user_message(user, res)
	else:
		server.user_message(user, "unrecognized command, type help for options")


def main():
	global sp
	path = "config.ini"
	if len(sys.argv) > 1:
		path = sys.argv[1]
		if not os.path.isfile(path):
			print("The provided configuration file does not exist")
			print("Dry run for config.ini")
			sys.exit(1)
	load_config(path)
	sp = SpotifyBot()
	sp.init_spotify()
	sp.select_device()
	print("Connecting to server...")
	t.set_connection_info(general.get("host"), general.get("port"))
	t.connect()
	t.login(
		general.get("nickname"),
		general.get("username", ""),
		general.get("password", ""),
		client_name,
	)
	print("login success")
	autojoin = general.get("autojoin")
	autojoin_pass = general.get("autojoin_pass", "")
	if autojoin != None:
		# ID
		if autojoin.isdigit():
			autojoin = int(autojoin)
		t.join(autojoin, password=autojoin_pass)
	t.handle_messages(1)


# the Spotify bot object
sp = None
if __name__ == "__main__":
	main()
