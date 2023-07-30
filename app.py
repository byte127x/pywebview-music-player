import webview, os, base64, configparser, music_tag, pickle
import webview.menu as wm
from flask import Flask, render_template, Response
from tkinter import Tk, filedialog

settings = configparser.ConfigParser()
settings.read('data/settings.ini')
app_server = Flask(__name__, template_folder='')

# Server stuff
@app_server.route('/')
def index():
	return render_template('index.html', token=webview.token)

@app_server.route('/file_load/<path>')
def file_loader(path):
	path = path.replace('|', '\\')
	try:
		with open(path, 'rb') as file:
			resp = Response(file.read())
			resp.headers['Accept-Ranges'] = 'bytes'
			return resp
	except FileNotFoundError:
		if path.split('.')[-1] in ('wav', 'mp3', 'flac', 'ogg', 'opus', 'aac'):
			if len(api.songs_with_missing_files) != 0:
				api.songs_with_missing_files = []
			for song_id in api.playlist:
				try:
					with open(songs[song_id].file_path, 'rb'):
						api.songs_with_missing_files.append(False)
				except FileNotFoundError:
					api.songs_with_missing_files.append(True)
			with open(settings['SFX']['FileNotFound'], 'rb') as file:
				return file.read()

@app_server.route('/icon.<name>')
def icon(name):
	path = f'img\\{name}.png'
	with open(path, 'rb') as file:
		return file.read()

@app_server.route('/playlist.view')
def playlist_view():
	return render_template('playlistview.html', token=webview.token)

# Media Collection Types
class Song:
	def __init__(self, file_path, title, artist=None, album=None):
		self.file_path = file_path
		self.title = title
		self.artist = artist
		self.album = album
		self.hearted = False

	def conv_to_dict(self):
		return {
			'path': self.file_path,
			'title': self.title,
			'artist_id': self.artist,
			'album_id': self.album,
			'hearted': self.hearted
		}

class Album:
	def __init__(self, name, artist=None, setlist=tuple()):
		self.setlist = setlist
		self.artist = artist
		self.name = name

	def conv_to_dict(self):
		return {
			'name': self.name,
			'setlist': self.setlist,
			'artist': self.artist
		}

class Artist:
	# DISCOG = DISCOGRAPHY
	def __init__(self, name, discog=tuple()):
		self.name = name
		self.discog = discog

	def conv_to_dict(self):
		return {
			'name': self.name,
			'discog': self.discog
		}

class ID3Song:
	def __init__(self, file_path):
		global artists
		self.file_path = file_path
		self.hearted = False
		tag = music_tag.load_file(self.file_path)
		
		self.title = str(tag['title'])
		self.artist = str(tag['artist'])
		self.album = str(tag['album'])

		if not self.title:
			self.title = file_path.split('\\')[-1]
		if not self.artist:
			self.artist = 'Unknown Artist'
		if not self.album:
			self.album = 'Unknown Album'

		for eye_d, artist_obj in enumerate(artists):
			if artist_obj.name == self.artist:
				self.artist = eye_d
		for eye_d, album_obj in enumerate(albums):
			if album_obj.name == self.album:
				self.album = eye_d

	def conv_to_dict(self):
		return {
			'path': self.file_path,
			'title': self.title,
			'artist_id': self.artist,
			'album_id': self.album,
			'hearted': self.hearted
		}


# Javascript API
class Api:
	def __init__(self):
		self.icons = {}
		self.songs_with_missing_files = []
		self.playlist = [
			5,
			8,
			1,
			0,
			2,
			3,
			6,
			4,
			7
		]
		self.playlist_index = 0
		self.playlist_view = None
		with open('img/MusicIcon.png', 'rb') as file:
			self.icons['music'] = str(base64.b64encode(file.read()))

	def remove_from_playlist(self, idx):
		print(idx)
		print(self.playlist[int(idx)])
		del self.playlist[int(idx)]
		if self.playlist_view != None:
			self.playlist_view.evaluate_js('update_window()')
		window.evaluate_js(f'''
			getUpdatedPlaylist()
		''')

	def add_mp3_to_playlist(self):
		invis_win = Tk()
		invis_win.withdraw()
		filetypes = (('MPEG-3 Audio (*.mp3)', '*.mp3'), ('FLAC Audio (*.flac)', '*.flac'), ('WAV Audio (*.wav)', '*.wav'), ('OGG Vorbis Audio (*.ogg)', '*.ogg'), ('All Files', '*.*'))
		file_path = filedialog.askopenfilename(parent=invis_win, title='Open Audio File', filetypes=filetypes)
		invis_win.destroy()
		if file_path == '':
			return
		api.add_anoynomus_song(file_path.replace('/', '\\'))
		if self.playlist_view != None:
			self.playlist_view.evaluate_js('update_window()')

	def add_anoynomus_song(self, path):
		global songs
		my_cool_idx = len(songs)
		s = ID3Song(path)
		print('\n\n'+str(s.conv_to_dict())+'\n\n')
		songs.append(s)
		self.playlist.append(my_cool_idx)

	def set_current_index(self, idx):
		self.playlist_index = idx
		if self.playlist_view != None:
			self.playlist_view.evaluate_js('update_window()')
		
	def get_current_index(self):
		return {'index': self.playlist_index}

	def return_songs_with_missing_files(self):
		return {'data': self.songs_with_missing_files}

	# Returns Playlist as Song IDs
	def return_playlist(self):
		return {'data': self.playlist}

	# Python Classes to JSON-Hashable Dictionaries
	def load_song_to_obj(self, id=0):
		# Turns Song into a KeyDict
		returner = songs[id].conv_to_dict()
		if (type(songs[id].artist) == str) or (type(songs[id].album) == str):
			returner['type'] = 'ID3Song'
		else:
			returner['type'] = 'ClassSong'
		return returner

	def load_artist_to_obj(self, id=0):
		# Turns Song into a KeyDict
		if type(id) == str:
			return {'name': id}
		resp = artists[id].conv_to_dict()
		resp['index'] = id
		return resp

	def load_album_to_obj(self, id=0):
		# Turns Song into a KeyDict
		if type(id) == str:
			return {'name': id}
		return albums[id].conv_to_dict()

	# Loader Functions
	def load_audiostream(self, path):
		with open(path, 'rb') as file:
			loaded_wave = base64.b64encode(file.read())
		return {'data': str(loaded_wave)}

	def load_image(self, path):
		with open(path, 'rb') as file:
			loaded_img = base64.b64encode(file.read())
		return {'name': 'Guy McFailure', 'data': str(loaded_img)}

	def load_icon(self, id):
		return {'data': self.icons[id]}


	# External Windows
	def view_playlist(self):
		self.playlist_view = webview.create_window('Appity', 'playlist.view', js_api=self)
		self.playlist_view.events.closed += self.close_playlist
		return {}

	def close_playlist(self):
		save_db()
		if self.playlist_view != None:
			try:
				self.playlist_view.destroy()
			except:
				pass
			self.playlist_view = None

	def get_library_lengths(self):
		return {
			'songs': len(songs),
			'artists': len(artists),
			'albums': len(albums)
		}


# Menu Functions
def menu_play():
	x = window.evaluate_js('''
		playlist.toggle_playing()
	''')

def menu_stop():
	x = window.evaluate_js('''
		playlist.stop()
	''')

# Music Library
''' DEFAULT EXAMPLE
songs = [
	Song('C:\\Users\\iONSZ\\Music\\Allister\\[2010] Countdown to Nowhere\\08 - Yearbook.mp3', title='Yearbook', artist=0, album=0),
	Song('C:\\Users\\iONSZ\\Music\\Peyton Willey\\7 (2023)\\06 - Summer Sky.wav', title='Summer Sky', artist=1, album=1),
	Song('C:\\Users\\iONSZ\\Music\\Allister\\[2010] Countdown to Nowhere\\02 - Run Away.mp3', title='Run Away', artist=0, album=0),
	Song('C:\\Users\\iONSZ\\Music\\Peyton Willey\\7 (2023)\\09 - Season Coming To An End.wav', title='Season Coming To An End', artist=1, album=1),
	Song('C:\\Users\\iONSZ\\Music\\Peyton Willey\\7\\Forker.wav', title='Forker', artist=1, album=1),
	Song('C:\\Users\\iONSZ\\Music\\Allister\\[2002] Last Stop Suburbia\\01 - Scratch.mp3', title='Scratch', artist=0, album=2),
	Song('C:\\Users\\iONSZ\\Music\\Allister\\[2002] Last Stop Suburbia\\02 - Radio Player.mp3', title='Radio Player', artist=0, album=2),
	Song('C:\\Users\\iONSZ\\Music\\Allister\\[2002] Last Stop Suburbia\\12 - Westbound.mp3', title='Westbound', artist=0, album=2),
	Song('C:\\Users\\iONSZ\\Downloads\\01-Grabify.flac', title='Grabify', artist=1, album=2),
]
artists = [
	Artist(name='Allister', discog=(0, 2)),
	Artist(name='Peyton Willey', discog=(1,))
]
albums = [
	Album(name='Countdown to Nowhere', artist=1, setlist=(0, 2)),
	Album(name='7', artist=2, setlist=(1, 3, 4)),
	Album(name='Last Stop Suburbia', artist=1, setlist=(5, 6, 7)),
]
'''

with open('data/library.pkl', 'rb') as file:
	pkl = pickle.load(file)

	songs = pkl['songs']
	artists = pkl['artists']
	albums = pkl['albums']

def save_db():
	# .malf = MusicApp Library File
	with open('data/library.pkl', 'wb') as file:
		pickle.dump({
			'songs': songs,
			'artists': artists,
			'albums': albums
		}, file, protocol=pickle.HIGHEST_PROTOCOL)

if __name__ == '__main__':
	icons = {}
	api = Api()

	menu = [
		wm.Menu('Playlist', [
			wm.MenuAction('Play/Pause', menu_play),
			wm.MenuAction('Stop', menu_stop),
		])
	]
	window = webview.create_window('Appity', app_server, js_api=api)
	window.events.closed += api.close_playlist
	webview.start(user_agent='IceWolf', debug=True, http_server=True, menu=menu) 
