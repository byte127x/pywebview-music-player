/* Audio Player Wrapper */
class PlayList {
	constructor() {
		this.audio_stream = document.getElementById('media')
		this.audio_stream.addEventListener('timeupdate', () => {this.update_timeslider()})
		this.audio_stream.onended = () => {this.current_song_ended()}
		this.playlist_loaded = false

		this.prev_volume_y = 0
		this.new_volume_y = 0

		/* Updates Missing Song list every time the song loads */
		this.audio_stream.addEventListener('loadeddata', () => {
			pywebview.api.return_songs_with_missing_files().then((r) => {
				this.load_missing_song_list(r.data)
				
				/* Change Progressbar color if it's missing */
				if (this.missing_songs[this.index]) {
					document.getElementById('progress-blob').style.background = `rgba(224, 11, 57, 0.9)`
				} else {
					document.getElementById('progress-blob').style.background = `rgba(0, 124, 190, 0.9)`
				}
			})
		})

		document.getElementById('progress-bar').onclick = (event) => {this.progress_scrub(event)}
	}

	progress_scrub(event) {
		var percentage = event.offsetX / document.getElementById('progress-bar').offsetWidth
		console.log(this.audio_stream.duration)
		console.log(percentage)
		console.log(this.audio_stream.duration*percentage)
		this.audio_stream.currentTime = this.audio_stream.duration*percentage
	}

	update_timeslider(e) {
		let percentage = this.audio_stream.currentTime / this.audio_stream.duration
		document.getElementById('progress-blob').style.width = `${percentage*100}%`
	}


	load_playlist(playlist) {
		this.playlist = playlist
		if (!this.playlist_loaded) {
			this.index = 0
			this.load_audio_source(playlist[0])
		}
		this.playlist_loaded = true
	}

	load_missing_song_list(missing_songs) {
		this.missing_songs = missing_songs
	}

	/* Loads file into Audio */

	load_audio_source(song_id) {
		this.stop()
		console.log(this.playlist)
		pywebview.api.load_song_to_obj(song_id).then((resp) => {
			console.log(resp)
			
			/* Load song into HTML Audio */
			this.path = resp.path
			var mod_path = this.path.replace(/\\/g, '|')
			this.audio_stream.src = `${window.location.href}file_load/${mod_path}`

			/* Update Missing Song List */
			pywebview.api.return_songs_with_missing_files().then((r) => {
				this.load_missing_song_list(r.data)

				/* Change Progressbar color if it's missing */
				if (this.missing_songs[this.index]) {
					document.getElementById('progress-blob').style.background = `rgba(224, 11, 57, 0.9)`
				} else {
					document.getElementById('progress-blob').style.background = `rgba(0, 124, 190, 0.9)`
				}
			})

			/* Load Metadata to the Bar */
			document.getElementById('song-title').innerHTML = resp.title
			if (resp.type == "ClassSong") {
				pywebview.api.load_artist_to_obj(resp.artist_id).then((artist) => {
					document.getElementById('song-artist').innerHTML = artist.name
				})
				pywebview.api.load_album_to_obj(resp.album_id).then((album) => {
					document.getElementById('song-album').innerHTML = album.name
				})
			} else {
				document.getElementById('song-artist').innerHTML = resp.artist_id
				document.getElementById('song-album').innerHTML = resp.album_id
			}
			this.update_idx_to_python()
		})
	}

	/* Play/Pause and Stop buttons */

	toggle_playing() {
		if (this.audio_stream.paused) {
			this.force_play()
		} else {
			this.audio_stream.pause()
			document.getElementById('play-img').src = '/icon.play'
		}
	}

	force_play() {
		this.audio_stream.play()
		document.getElementById('play-img').src = '/icon.pause'
	}

	stop() {
		this.audio_stream.pause()
		this.audio_stream.currentTime = 0
		document.getElementById('play-img').src = '/icon.play'
	}

	/* Next/Previous Buttons */
	next() {
		this.index++
		if (this.index == this.playlist.length) {
			this.index--
		}
		this.load_audio_source(this.playlist[this.index])
		this.update_idx_to_python()
	}

	prev() {
		this.index--
		if (this.index == -1) {
			this.index++
		}
		this.load_audio_source(this.playlist[this.index])
		this.update_idx_to_python()
	}

	/* Other Utility Functions */
	current_song_ended() {
		console.log(this.playlist)
		if (this.index == this.playlist.length-1) {
			return
		}
		this.next()
	}

	update_idx_to_python() {
		pywebview.api.set_current_index(this.index).then((resp) => {
			this.force_play()
		})
	}
}

/* Change showing Album Art */
function injectNewAlbumArt(path) {
	pywebview.api.load_image(path).then((resp) => {
		formatted_data = resp.data.slice(2, -1)
		document.getElementById('songinfo_art').src = `data:image/jpeg;base64,${formatted_data}`
	})
}

/* Hide and Show Plus Button Menu */
function showPlusMenu(event) {
	document.getElementById('plus-menu').style.display = 'block'
	var height = document.getElementById('plus-menu').getBoundingClientRect().height
	document.getElementById('plus-menu').style.left = `${event.clientX}px`
	document.getElementById('plus-menu').style.top = `${event.clientY-height}px`

	setTimeout(
		() => {
			document.getElementById('plus-menu').style.filter = `blur(0px)`
			document.getElementById('plus-menu').style.opacity = 1
		}, 10
	)
}

function hidePlusMenu(event) {
	document.getElementById('plus-menu').style.filter = `blur(10px)`
	document.getElementById('plus-menu').style.opacity = 0
	setTimeout(
		() => {document.getElementById('plus-menu').style.display = 'none'},
		300
	)
}

/* First Steps */
var playlist = new PlayList()

function getUpdatedPlaylist() {
	pywebview.api.return_playlist().then((resp) => {
		var playlist_data = resp.data
		playlist.load_playlist(playlist_data)
	})
}

// Catalog Generator Functions
function CATALOG_albums() {
	document.getElementById('data-catalog').classList.remove(...document.getElementById('data-catalog').classList)
	document.getElementById('data-catalog').classList.add('data-albums')
	pywebview.api.get_library_lengths().then((resp) => {
		let album_index = 0
		while (album_index < resp.albums) {
			// Create Container
			let new_div = document.createElement('div')
			new_div.classList.add('album-object')

			// Make Info Elements
			let albumart = document.createElement('img')
			let albumtxt = document.createElement('b')
			let artisttxt = document.createElement('span')

			albumart.src = 'https://play-lh.googleusercontent.com/IeNJWoKYx1waOhfWF6TiuSiWBLfqLb18lmZYXSgsH1fvb8v1IYiZr5aYWe0Gxu-pVZX3'

			// Get Album Info
			pywebview.api.load_album_to_obj(album_index).then((response) => {
				albumtxt.innerHTML = response.name
				pywebview.api.load_album_to_obj(response.artist).then((artist_resp) =>{
					artisttxt.innerHTML = artist_resp.name
				})
			})

			// Push everything to Screen
			new_div.appendChild(albumart)
			new_div.appendChild(albumtxt)
			new_div.appendChild(artisttxt)
			document.getElementById('data-catalog').appendChild(new_div)

			// Continue Loop
			album_index++
		}
	})
}

function CATALOG_artists() {
	document.getElementById('data-catalog').classList.remove(...document.getElementById('data-catalog').classList)
	document.getElementById('data-catalog').classList.add('data-artists')
	pywebview.api.get_library_lengths().then((resp) => {
		let artist_index = 0
		while (artist_index < resp.artists) {
			// Create Container
			let new_div = document.createElement('div')
			new_div.classList.add('artist-object')

			// Make Info Elements
			let albumart = document.createElement('img')
			let artisttxt = document.createElement('span')

			albumart.src = 'https://play-lh.googleusercontent.com/IeNJWoKYx1waOhfWF6TiuSiWBLfqLb18lmZYXSgsH1fvb8v1IYiZr5aYWe0Gxu-pVZX3'

			// Get Album Info
			pywebview.api.load_artist_to_obj(artist_index).then((response) => {
				artisttxt.innerHTML = response.name
			})

			// Push everything to Screen
			new_div.appendChild(albumart)
			new_div.appendChild(artisttxt)
			document.getElementById('data-catalog').appendChild(new_div)

			// Continue Loop
			artist_index++
		}
	})
}

window.addEventListener('pywebviewready', function() {
	/* Make Buttons do stuff */
	document.getElementById('play-btn').onclick = () => {playlist.toggle_playing()}
	document.getElementById('stop-btn').onclick = () => {playlist.stop()}
	document.getElementById('back-btn').onclick = () => {playlist.prev()}
	document.getElementById('frwd-btn').onclick = () => {playlist.next()}

	document.getElementById('list-btn').onclick = () => {
		pywebview.api.view_playlist().then((resp) => {})
	}

	injectNewAlbumArt("C:\\Users\\iONSZ\\Music\\Allister\\[2010] Countdown to Nowhere\\Folder.jpg")
	getUpdatedPlaylist()

	/* Popup menu */
	document.getElementById('plus-btn').addEventListener('click', (event) => {showPlusMenu(event)})
	document.getElementById('menu-close').addEventListener('click', (event) => {hidePlusMenu()})
	document.getElementById('add-mp3').addEventListener('click', (event) => {
		pywebview.api.add_mp3_to_playlist().then((resp) => {
			getUpdatedPlaylist()
		})
	})

	/* Slider JS */
	const box = document.querySelector(".box")
	const bar = document.querySelector(".bar")

	let isDragging = false
	let offsetY = 0

	function startDragging(e) {
		isDragging = true
		offsetY = e.offsetY
		box.style.cursor = "grabbing"
	}

	function stopDragging() {
		isDragging = false
		box.style.cursor = "grab"
	}

	function moveBox(e) {
		if (isDragging) {
			const newTop = Math.min(
				Math.max(
					e.clientY - bar.getBoundingClientRect().top - offsetY, 0
				), 
				bar.clientHeight - box.clientHeight
			)

			box.style.transform = `translateY(${newTop}px)`

			const percentage = (newTop / (bar.clientHeight - box.clientHeight))
			document.querySelector(".bar-full").style.height = `${100-(percentage*100)}%`
			document.querySelector(".bar-full").style.top = `${(percentage*100)}%`
			playlist.audio_stream.volume = 1-percentage
		}
	}

	box.addEventListener("mousedown", startDragging)
	window.addEventListener("mouseup", stopDragging)
	window.addEventListener("mousemove", moveBox)

	// Generate Music Catalog
	var catalog_mode = 'albums'
	CATALOG_artists()
})