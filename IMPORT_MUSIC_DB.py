import pickle

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


with open('data/library.pkl', 'rb') as file:
	print(pickle.load(file))