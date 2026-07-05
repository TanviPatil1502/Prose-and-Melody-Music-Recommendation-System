from dotenv import load_dotenv
import os
import base64
import json
import requests
from requests import post, get
from pprint import pprint
import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from flask_pymongo import PyMongo
from pymongo import MongoClient
from bson import ObjectId
import datetime
from collections import defaultdict
mongo_uri=os.getenv("MONGO_URI")
dbname=os.getenv("MONGO_DBNAME")
client = MongoClient(mongo_uri)
db = client[dbname] 

class BookMusicRecommender:
    def __init__(self):
        load_dotenv()
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.yt_api = os.getenv("API_KEY")
        self.token = self.get_token()
        self.title = ''
        self.dictionary = { ... }  # Keep your big genre dictionary here
        self.subjects = []
        self.final_book = []
        self.narrowed_music = []
        self.final_music=[]
        self.s = -1
        self.y = -1
        self.s_stack = []
        self.y_stack = []
        self.current_user=None
        self.db = db
        self.fav_genre = db["fav_genre"]
        self.recent_genre = db["recent_genre"]

    def get_token(self):
        auth_string = self.client_id + ":" + self.client_secret
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        result = post(url, headers=headers, data=data)
        json_result = json.loads(result.content)
        return json_result["access_token"]

    def get_auth_header(self):
        return {"Authorization": "Bearer " + self.token}

    def book_genre(self, title):
        search_url = f'https://openlibrary.org/search.json?title={title}'
        search_response = requests.get(search_url)
        subjects = []
        if search_response.status_code == 200:
            search_data = search_response.json()
            if 'docs' in search_data and search_data['docs']:
                book = search_data['docs'][0]
                work_key = book.get('key', None)
                if work_key:
                    editions_url = f'https://openlibrary.org{work_key}/editions.json'
                    editions_response = requests.get(editions_url)
                    if editions_response.status_code == 200:
                        editions_data = editions_response.json()
                        if 'entries' in editions_data and editions_data['entries']:
                            first_isbn = None
                            for edition in editions_data['entries']:
                                isbn_13 = edition.get('isbn_13', [])
                                isbn_10 = edition.get('isbn_10', [])
                                if isbn_13:
                                    first_isbn = isbn_13[0]
                                    break
                                elif isbn_10:
                                    first_isbn = isbn_10[0]
                                    break
                            if first_isbn:
                                isbn_url = f'https://openlibrary.org/api/books?bibkeys=ISBN:{first_isbn}&format=json&jscmd=data'
                                isbn_response = requests.get(isbn_url)
                                if isbn_response.status_code == 200:
                                    isbn_data = isbn_response.json()
                                    book_data = isbn_data.get(f'ISBN:{first_isbn}', {})
                                    subjects = [subject['name'] for subject in book_data.get('subjects', [])]
        self.subjects = subjects
        return subjects
    def load_genre_dictionary(self):
        """
        Loads genre-keyword mapping from MongoDB into a dictionary.
        Assumes each document in the collection has one genre as the key.
        """
        collection = self.db.books  # Replace with your actual collection name
        dictionary = {}
        for doc in collection.find({}, {'_id': 0}):
            for genre, keywords in doc.items():
                if genre in dictionary:
                    dictionary[genre].extend(keywords)
                else:
                    dictionary[genre] = keywords

        # Remove duplicates
        for genre in dictionary:
            dictionary[genre] = list(set(dictionary[genre]))

        self.dictionary = dictionary

    def narrowdown_book(self):
        
        self.load_genre_dictionary()
        genre_count = {genre: 0 for genre in self.dictionary}
        for genre, genre_keywords in self.dictionary.items():
            for subject in self.subjects:
                for keyword in genre_keywords:
                    if keyword in subject.lower():
                        genre_count[genre] += 1
        max_count = max(genre_count.values())
        self.final_book = [genre for genre, count in genre_count.items() if count > 0 and max_count > 0]
        return self.final_book if self.final_book else ["Unknown Genre"]

    def get_music_genre(self):
        if self.final_book[0] == "Unknown Genre":
            return []
        music_genres = []
        for genre in self.final_book:
            m = self.db.musics.find_one({genre: {"$exists": True}},{genre: 1, "_id": 0})
            music_genres += m.get(genre, [])
        self.narrowed_music = music_genres
        return self.narrowed_music

    def searching_playlist(self, genre, platform, instrumental=False, language='English'):
        """
        Search for a playlist based on genre, platform (Spotify or YouTube),
        and optional preferences for instrumental and language.
        """

        # Construct query string
        query_parts = [genre]
        if instrumental:
            query_parts.append("instrumental")
        if language:
            query_parts.append(language)
        search_query = " ".join(query_parts)

        if platform == 'spotify':
            print("spotify genre:",genre)
            url = "https://api.spotify.com/v1/search"
            headers = self.get_auth_header()
            query = f"q={search_query}&type=playlist&limit=5"
            query_url = url + "?" + query
            result = get(query_url, headers=headers)
            json_result = json.loads(result.content)
            try:
                final=json_result['playlists']['items']
                print("final lists:",final)
                for i in final:
                    print("inside value",i)
                    if i!=None and 'stories' not in i['name'].lower() and 'story' not in i['name'].lower() and 'movies' not in i['name'].lower():
                        link = i["external_urls"]["spotify"]
                        return link
            except (KeyError, IndexError):
                return None

        else:  # YouTube
            search_url = 'https://www.googleapis.com/youtube/v3/search'
            search_params = {
                'part': 'snippet',
                'maxResults': 5,
                'q': f'{search_query} playlist',
                'type': 'playlist',
                'key': self.yt_api
            }
            search_response = requests.get(search_url, params=search_params)
            playlists = search_response.json()

            for item in playlists.get('items', []):
                title = item['snippet']['title'].lower()
                if 'season' not in title:
                    playlist_id = item['id']['playlistId']
                    return 'https://www.youtube.com/playlist?list=' + playlist_id

            return None

    def forward(self, platform,instrumental=False,language='English'):
        new_playlist_id='End of playlist'
        if platform.lower() == 'spotify' and self.s<len(self.final_music)-1:
            self.s += 1
            print("sending genre: ",self.final_music[self.s])
            new_playlist_id = self.searching_playlist(self.final_music[self.s], 'spotify',instrumental,language)
            self.s_stack.append(new_playlist_id)
        elif platform.lower()=='youtube' and self.y<len(self.final_music)-1:
            self.y += 1
            new_playlist_id = self.searching_playlist(self.final_music[self.y], 'youtube',instrumental,language)
            self.y_stack.append(new_playlist_id)
        return new_playlist_id

    def previous(self, platform):
        if platform == 'spotify' and len(self.s_stack) > 1:
            self.s -= 1
            self.s_stack.pop()
            prev = self.s_stack[-1]
        elif platform == 'youtube' and len(self.y_stack) > 1:
            self.y -= 1
            self.y_stack.pop()
            prev = self.y_stack[-1]
        else:
            return -1
        return prev

    def OnSpot(self,genre, platform):
        if platform.lower() == 'spotify':
            return self.searching_playlist(genre, 'spotify')
        elif platform.lower()=='youtube':
            return self.searching_playlist(genre, 'youtube')
        return -1
    def recommend_for_book(self, search_genre):
        """
        Recommends music genres based on collaborative filtering using users' favorite genres.
        
        :param search_genre: list of genres from get_music()
        :return: list of recommended genres
        """

        # Fetch all user favorite genres
        all_users = list(self.fav_genre.find())

        if not all_users:
            # Special case: No users in database yet
            self.final_music=search_genre
            return search_genre

        # Prepare user-genre DataFrame
        user_ids = []
        genre_data = []

        for user in all_users:
            user_ids.append(user['user_id'])
            genre_row = {}
            for genre in user.get('Genre', []):
                genre_row[genre] = 1
            genre_data.append(genre_row)

        df = pd.DataFrame(genre_data, index=user_ids).fillna(0)

        # Adding a pseudo-user for the current search_genre
        pseudo_user = {}
        for genre in search_genre:
            pseudo_user[genre] = 1

        df = pd.concat([df, pd.DataFrame([pseudo_user])], ignore_index=True)
        df=df.fillna(0)
        # print(df)
        # Apply SVD
        svd = TruncatedSVD(n_components=min(12, df.shape[1]-1))  # avoid error if features are small
        matrix = svd.fit_transform(df)

        # Calculate correlation
        corr_matrix = np.corrcoef(matrix)
        pseudo_idx = df.index[-1]  # last one is pseudo-user

        corr_scores = corr_matrix[-1][:-1]  # exclude pseudo-user itself
        

        top_indices = np.where(corr_scores > 0.4)[0]
        if len(top_indices)==0:
            top_indices = corr_scores.argsort()[::-1][:3]
        # Collect genres from similar users
        recommended_genres = set()
        for idx in top_indices:
            user_genres = df.iloc[idx]
            recommended_genres.update(user_genres[user_genres > 0].index.tolist())
        # Exclude genres already in search_genre
        final_rec = list(recommended_genres - set(search_genre))
        # Ensure minimum 5 items
        if len(final_rec) < 10:
            filler = [g for g in search_genre if g not in final_rec]
            final_rec.extend(filler[:10 - len(final_rec)])
        self.final_music = final_rec  # limit to 5
        return self.final_music

    
    def basic_recommendation(self, userid):
        """
        Recommend Spotify and YouTube genres based on recent searches using SVD.
        Returns two lists: [spotify_genres], [youtube_genres]
        """

        all_users = list(self.fav_genre.find())
        if not all_users:
            return []

        user_recent = self.db.recent_genre.find_one({"user_id": userid})

        # Fallback to most common genres if no recent
        if not user_recent or not user_recent.get("Recent"):
            genre_counter = {}
            for user in all_users:
                for genre in user.get("Genre", []):
                    genre_counter[genre] = genre_counter.get(genre, 0) + 1
            recent_flat = sorted(genre_counter, key=genre_counter.get, reverse=True)[:5]
        else:
            recent_flat = user_recent["Recent"]

        user_ids = []
        genre_data = []

        for user in all_users:
            user_ids.append(user['user_id'])
            genre_row = {genre: 1 for genre in user.get('Genre', [])}
            genre_data.append(genre_row)

        df = pd.DataFrame(genre_data, index=user_ids).fillna(0)

        # Ensure pseudo_user has same columns as df
        pseudo_user = {genre: 1 for genre in recent_flat}
        pseudo_df = pd.DataFrame([pseudo_user])
        pseudo_df = pseudo_df.reindex(columns=df.columns, fill_value=0)
        df = pd.concat([df, pseudo_df], ignore_index=True)

        if df.shape[1] < 2:
            return recent_flat[:5]

        svd = TruncatedSVD(n_components=min(12, df.shape[1] - 1))
        matrix = svd.fit_transform(df)

        corr_matrix = np.corrcoef(matrix)
        corr_scores = corr_matrix[-1][:-1]
        top_indices = np.where(corr_scores > 0.6)[0]

        recommended_genres = set()
        for idx in top_indices:
            user_genres = df.iloc[idx]
            recommended_genres.update(user_genres[user_genres > 0].index.tolist())

        final_rec = list(recommended_genres - set(recent_flat))

        # Fill up to at least 5 recommendations
        if len(final_rec) < 5:
            fill_from = [g for g in recent_flat if g not in final_rec]
            final_rec.extend(fill_from[:5 - len(final_rec)])
        print(final_rec)
        return final_rec[:5]
    def bookSearch(self,title):
        # print("Searching genres")
        self.book_genre(title)
        if self.subjects==[]:
            return "No such book found"
        # print('Narrowing down')
        self.narrowdown_book()
        if self.final_book==['Unknown Genre']:
            return "Unfamiliar with the book"
        # print("getting music genre")
        search=self.get_music_genre()
        # print("narrowing down music")
        self.recommend_for_book(search)
        self.s=self.y=-1
        return True

        
class MongoCalls:
    def __init__(self):
        self.users = db.users
        self.recent_playlists = db.recents
        self.favorite_playlists = db.favourites
        self.favorite_genres = db.fav_genre
        self.recent_genres = db.recent_genre

    def add_user(self, user_data):
        user_data['createdAt'] = datetime.datetime.utcnow()
        result = self.users.insert_one(user_data)
        return str(result.inserted_id)

    def get_user_by_email(self, email,password):
        user = self.users.find_one({"email": email,"password":password})
        if user:
            return user['_id']
        return None

    def add_recent_playlist(self, recent_data):
        recent_data['createdAt'] = datetime.datetime.utcnow()
        user_id = ObjectId(recent_data.get('user_id'))
        recents = recent_data.get('Recents')
        recent_data['user_id']=ObjectId(recent_data['user_id'])
        # print(user_id,recents)
        # Prevent duplicate playlist
        exists = self.recent_playlists.find_one({
            "user_id": user_id,
            "Recents": recents
        })
        # print(exists)
        if exists:
            return "Already Done"

        # Save genre if provided
        if len(recents) >= 3:
            self.add_recent_genre_internal(user_id, recents[3])  # assuming genre at index 2

        result = self.recent_playlists.insert_one(recent_data)
        return "Done"

    def get_recent_playlists_by_user_id(self, user_id):
        recent_playlists = self.recent_playlists.find({"user_id": ObjectId(user_id)}).sort("createdAt", -1)
        # print(recent_playlists)
        grouped = defaultdict(list)
        for item in recent_playlists:
            book, play, rest,rest1 = item['Recents']
            grouped[book].append(play)
        print("got values:",grouped)
        return dict(grouped)

    def add_favorite_playlist(self, favorite_data):
        favorite_data['createdAt'] = datetime.datetime.utcnow()
        user_id = ObjectId(favorite_data.get('user_id'))
        recents = favorite_data.get('Favourites')
        favorite_data['user_id']=ObjectId(favorite_data['user_id'])

        exists = self.favorite_playlists.find_one({
            "user_id": user_id,
            "Recents": recents
        })
        if exists:
            return "Already Done"

        # Save genre if provided
        if len(recents) >= 3:
            self.add_favorite_genre_internal(user_id, recents[3])

        result = self.favorite_playlists.insert_one(favorite_data)
        return "Done"

    def get_favorite_playlists_by_user_id(self, user_id):
        favorite_playlists = self.favorite_playlists.find({"user_id": ObjectId(user_id)})
        grouped = defaultdict(list)
        # print(favorite_playlists)
        for item in favorite_playlists:
            print(item)
            book, play, platform,genre = item['Favourites']
            grouped[book].append(play)
        print("got fav",grouped)
        return dict(grouped)

    def add_favorite_genre_internal(self, user_id, genre):
        self.favorite_genres.update_one(
            {"user_id": user_id},
            {"$addToSet": {"Genre": genre}, "$setOnInsert": {"createdAt": datetime.datetime.utcnow()}},
            upsert=True
        )

    def add_recent_genre_internal(self, user_id, genre):
        self.recent_genres.update_one(
            {"user_id": user_id},
            {"$addToSet": {"Genre": genre}, "$setOnInsert": {"createdAt": datetime.datetime.utcnow()}},
            upsert=True
        )

    def get_favorite_genres_by_user_id(self, user_id):
        genre_doc = self.favorite_genres.find_one({"user_id": ObjectId(user_id)})
        return genre_doc.get("Genre", []) if genre_doc else []

    def get_recent_genres_by_user_id(self, user_id):
        genre_doc = self.recent_genres.find_one({"user_id": ObjectId(user_id)})
        return genre_doc.get("Genre", []) if genre_doc else []
    
    def get_user(self,user_id):
        user_details=self.users.find_one({'_id':ObjectId(user_id)},{'_id':0,'password':0,'createdAt':0})
        print(user_details.get('name'),user_details.get('email'))
        return dict(user_details)
