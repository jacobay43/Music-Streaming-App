import deezer #deezer API 
import sys
import threading
import requests
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import PyQt5.QtMultimedia as qtmm

#should show properties of each track in a QTableWidget: artist, album, duration, year, etc
##
"""
t = deezer.Client().get_track(num)
t.title
t.artist.name
t.album.title
t.duration returns (secs)
t.release_date
Improvements:
    t.album.cover_medium
    use QThread rather than threading.Thread to avoid crash when thread operation fails
    improve UI
"""
##
#handle requests.exceptions.ConnectionError for when timeout occurs
class MainWindow(qtw.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Music Streamer-Deezer')
        widget = qtw.QWidget()
        #widget.setMinimumSize(780,80)
        self.setCentralWidget(widget)
        main_layout = qtw.QGridLayout()
        widget.setLayout(main_layout)
        self.search_edit = qtw.QLineEdit(placeholderText='Search by Artiste')
        self.search_btn = qtw.QPushButton('Search for Tracks',clicked=self.on_search_clicked)
        self.retrieving_bar = qtw.QProgressBar(minimum=0,maximum=100)
        self.tracks_list = qtw.QListWidget()
        self.tracks_list.itemDoubleClicked.connect(self.play_track)
        self.tracks_list.sizeHint = lambda: qtc.QSize(570,30) #track list widget should occupy more space than the widgets on its left
        self.tracks_list.setSizePolicy(qtw.QSizePolicy.MinimumExpanding,qtw.QSizePolicy.MinimumExpanding)
        self.track_details = qtw.QTableWidget(rowCount=1,columnCount=5)
        self.track_details.setHorizontalHeaderLabels(['Title','Artiste','Album','Duration','Release Date'])
        self.track_details.sizeHint = lambda: qtc.QSize(760,30)
        self.track_details.setSizePolicy(qtw.QSizePolicy.MinimumExpanding,qtw.QSizePolicy.Fixed)
        self.client = deezer.Client() #client for accessing objects from the deezer API
        self.player = qtmm.QMediaPlayer()
        self.position = qtw.QSlider(minimum=0,orientation=qtc.Qt.Horizontal)
        self.player.stateChanged.connect(self.on_player_state_changed)
        self.player.positionChanged.connect(self.position.setSliderPosition)
        self.player.durationChanged.connect(self.position.setMaximum)
        self.position.sliderMoved.connect(self.player.setPosition)
        self.play_button = qtw.QPushButton('Play',clicked=self.on_playbutton)
        self.tracks = {} #dictionary for keeping track of music tracks loaded from the search
        main_layout.addWidget(self.search_edit,1,0,1,1)
        main_layout.addWidget(self.tracks_list,1,1,3,3)
        main_layout.addWidget(self.search_btn,2,0,1,1)
        main_layout.addWidget(self.retrieving_bar,3,0,1,1)
        main_layout.addWidget(self.play_button,4,1,1,1)
        main_layout.addWidget(self.position,6,0,1,4)
        main_layout.addWidget(self.track_details,5,0,1,4)
        self.show()
    def on_search_clicked(self):
        self.retrieving_bar.setMaximum(0) #busy indicator to indicate the artiste's tracks are being searched for
        self.thread = threading.Thread(target=self.get_tracks,kwargs={'artiste':self.search_edit.text()}) #asynchronously search for tracks made by the artiste specified
        self.thread.start() #set on a thread so it does not affect GUI main loop
    def get_tracks(self,artiste):
        try:
            self.tracks = self.client.advanced_search({"artist":artiste}) #retrieve publicly available track objects for this artiste
            self.tracks = {track.title:track for track in self.tracks} #map track name to track object
            #print(self.tracks)
            if self.tracks: #if any track was retrieved
                self.tracks_list.clear() #clear the current contents of the track list widget and .
                self.tracks_list.addItems((track_title for track_title in self.tracks.keys())) #map the new tracks to it
            else:
                qtw.QMessageBox.information(None,'No Tracks','No tracks found')
        except requests.exceptions.ConnectionError:
            qtw.QMessageBox.critical(None,'Network Error','Could not retrieve results from the network')
        finally:
            self.retrieving_bar.setMaximum(100) #indicate completion
    def on_playbutton(self):
        if self.player.state() == qtmm.QMediaPlayer.PlayingState:
            self.play_button.setText('Play')
            self.player.stop()
        elif self.player.state() == qtmm.QMediaPlayer.StoppedState and self.player.playlist(): #ensure button is not toggling if no playlist has been loaded
            self.play_button.setText('Stop')
            self.player.play()
    def play_track(self,item):
        #play the track  [while simultaneously caching it for future playback]-
        track = self.tracks.get(item.text(),'') #attempt to retrieve the corresponding track object with this track's title as the dictionary key
        if track:
            url = qtc.QUrl(track.preview) #return the URL to the track music file and load it into the playlist; essentially streaming it
            self.update_details(track) #show the track details in the table
            self.set_file(url)
    def set_file(self,url):
        if url.scheme() == '':
            url.setScheme('http') #this is only for remote music files
        #self.current_song_lb.setText(url.fileName())
        content = qtmm.QMediaContent(url)
        self.playlist = qtmm.QMediaPlaylist()
        self.playlist.addMedia(content)
        self.playlist.setCurrentIndex(1)
        self.player.setPlaylist(self.playlist)
        self.on_playbutton() #double clicking on the track from the list should play it automatically
        #self.loop_cb.setChecked(False)
    def update_details(self,track):
        try:
            self.track_details.setItem(0,0,qtw.QTableWidgetItem(track.title))
            self.track_details.setItem(0,1,qtw.QTableWidgetItem(track.artist.name))
            self.track_details.setItem(0,2,qtw.QTableWidgetItem(track.album.title))
            minutes = track.duration // 60
            seconds = track.duration % 60
            self.track_details.setItem(0,3,qtw.QTableWidgetItem(f'{minutes:0>2}:{seconds:0>2}')) #format secs to MM:SS format
            self.track_details.setItem(0,4,qtw.QTableWidgetItem(track.release_date))
        except AttributeError as e:
            print(e)
    def on_player_state_changed(self,state):
        if state == qtmm.QMediaPlayer.PlayingState:
            self.play_button.setText('Stop')
        else:
            self.play_button.setText('Play')
if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    app.setStyle(qtw.QStyleFactory.create('Fusion'))
    mw = MainWindow()
    sys.exit(app.exec())