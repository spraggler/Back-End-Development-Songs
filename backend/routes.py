from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/health")
def get_health():
    return {"status": "OK"}

@app.route("/count")
def get_count():
    count = db.songs.count_documents({})
    return {"count": count}

@app.route("/song", methods=['Get'])
def songs():
    songs = list(db.songs.find({}))
    for song in songs:
        song['_id'] = str(song['_id'])
    return jsonify({"songs": songs}), 200

@app.route("/song/<id>", methods=['Get'])
def get_song_by_id(id):
    song = db.songs.find_one({"id": int(id)})
    if song:
        song['_id'] = str(song['_id'])
        return jsonify(song), 200
    return {"message": "song with id not found"}, 404

@app.route("/song", methods=['Post'])
def create_song():
    song_data = request.get_json()

    if song_data:
        song = db.songs.find_one({"id": song_data['id']})
        if song:
            return {"Message": f"song with id {song['id']} already"}, 302
        resp = db.songs.insert_one(song_data)
        return jsonify({"insertd id": f"{resp}"}), 201

@app.route("/song/<int:id>", methods=['Put'])
def update_song(id):
    song_data = request.get_json()

    if song_data:
        song = db.songs.find_one({"id": id})
        if not song:
            return {"message": "song not found"}, 404

        updated_song = db.songs.update_one({"id": id}, {"$set": song_data})
        if updated_song.modified_count > 0:
            return {"message": "Song updated successfully"}, 202
        else:
            return {"message": "song found, but nothing updated"}, 200

@app.route("/song/<int:id>", methods=['Delete'])
def delete_song(id):
    # song = db.songs.find_one({"id": id})
    # if not song:
    #     return {"message": "song not found"}, 404

    deleted_song = db.songs.delete_one({"id": id})
    if deleted_song.deleted_count > 0:
        return {"message": "Song deleted successfully"}, 204
    else:
        return {"message": "song not found"}, 404