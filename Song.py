import os
from mutagen.mp3 import MP3


def song_length(path):
    try:
        audio = MP3(path)
        length = audio.info.length
        print("Length of song: ", length)
        return length
    except Exception as e:
        print(f"Error while getting song length: {e}")
        return None


def get_location(artist, title, genre, year):
    genre = genre.lower()
    filename = f'{artist} - {title}.mp3'
    ignore_genre = ["pop"]
    ignore_year = ["rock"]
    folder = f'z:\\songs\\{genre}\\{year}\\'.lower()
    if genre in ignore_year:
        folder = f'z:\\songs\\{genre}\\'.lower()
    if genre in ignore_genre:
        folder = f'z:\\songs\\{year}\\'.lower()
    if genre == "domoljubne":
        folder = f'z:\\songs\\cro\\domoljubne\\'
    if genre == "religijske":
        folder = f'z:\\songs\\religiozne\\'
    return os.path.join(folder, filename)


class Song:
    def __init__(self, input_data, genres, decades, tempos):
        # print(input_data)
        self.id = input_data[0]
        self.artist_id = input_data[1]
        self.title = input_data[2]
        self.genre_01_id = input_data[3]
        self.genre_01_name = genres[self.genre_01_id]
        self.genre = self.genre_01_name
        self.genre_02_id = input_data[4]
        self.genre_02_name = genres[self.genre_02_id]
        self.genre_03_id = input_data[5]
        self.genre_03_name = genres[self.genre_03_id]
        self.genre_04_id = input_data[6]
        self.genre_04_name = decades[self.genre_04_id]
        self.genre_05_id = input_data[7]
        self.genre_05_name = tempos[self.genre_05_id]
        self.genres_all = f'{self.genre_01_name}/{self.genre_02_name}/{self.genre_03_name} - {self.genre_04_name} -' \
                          f' {self.genre_05_name}'
        self.decade = self.genre_04_name
        self.year = input_data[8]
        self.enabled = input_data[12]
        self.auto_play = input_data[13]
        self.duration = input_data[14]
        self.location = input_data[20]
        self.location_local = self.location.lower().replace('b:', 'z:')
        self.composer = input_data[24]
        self.album = input_data[25]
        self.isrc = input_data[27]
        self.publisher = input_data[32]
        self.artist = input_data[36]
        self.exists = os.path.isfile(self.location.lower().replace("b:", "z:"))
        self.location_correct = get_location(self.artist, self.title, self.genre, self.year)

    def basic_data(self):
        print(f'Artist: {self.artist}, Title: {self.title}, Album: {self.album}')

    def id3_data(self):
        print(f'Artist: {self.artist}, Title: {self.title}, Composer: {self.composer}, Album: {self.album}, '
              f'Year: {self.year}, Genres: {self.genres_all}, Publisher: {self.publisher}, ISRC: {self.isrc}, '
              f'ID: {self.id}', f'Duration: {self.duration} seconds')


class SongID3:
    def __init__(self, artist, title, composer, album, year, genre, publisher, isrc, duration, error):
        self.artist = artist
        self.title = title
        self.composer = composer
        self.album = album
        self.year = year
        self.genre = genre
        self.publisher = publisher
        self.isrc = isrc
        self.duration = duration
        self.error = error
        if self.error == "":
            self.error = "No error"
