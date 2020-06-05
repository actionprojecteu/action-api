##################### Imports #####################
from flask import Flask, jsonify, request

from application import config
import os
from flask_cors import CORS
from datetime import datetime
from flask_pymongo import PyMongo, ObjectId
import logging
import json
from datetime import date,datetime
import pymongo
from werkzeug.utils import secure_filename
import random
import string

from PIL import Image
from PIL.ExifTags import TAGS,GPSTAGS


##################### Initialize #####################

app = Flask(__name__)
app.config.from_object(config)

cors = CORS(app)
mongo = PyMongo(app)


##################### logging part #####################

logging.basicConfig(filename='log/log.log', filemode='w', level=logging.INFO
    , format='%(asctime)s %(levelname)s %(name)s : %(message)s')
logging.info('This will get logged to a file')


##################### Test part #####################

@app.route('/')
def hello_world():
    return 'Hello World!'


##################### Token part #####################

listOfTokens = ['Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1ODk5NzEyOTgsIm5iZiI6MTU4OTk3MTI5OCwianRpIjoiYTE5MzM2MTUtZmQ5NS00ODFlLWJmY2YtMjkyYTUxZDRiNGU0IiwiZXhwIjoxNTkyNTYzMjk4LCJpZGVudGl0eSI6IlBydWViYSIsImZyZXNoIjpmYWxzZSwidHlwZSI6ImFjY2VzcyJ9.ZJrBt9R0v0ZcKc9kI_6jwFCbRZECvmM6h24jafPx7m8',
    'Bearer APiary123456']

@app.before_request
def before_request():
    if request.method == 'POST':
        if 'Authorization' not in request.headers:
            app.logger.warning("No auth sended.")
            return jsonify(error="No auth send."), 401
        if request.headers['Authorization'] not in listOfTokens :
            app.logger.warning("Token: %s not valid.", request.headers['Authorization'])
            return jsonify(error="Token not valid."), 401


##################### observation part #####################

@app.route('/observations', methods=['GET'])
def get_list_observation():
    limit = request.args.get('limit', default = 5, type=int)
    page = request.args.get('page', default = 1, type=int)

    try:
        begin_date = to_date(request.args.get('begin_date', default = date.min.strftime('%Y-%m-%d')))
        finish_date = to_date(request.args.get('finish_date', default = date.max.strftime('%Y-%m-%d')))
    except ValueError as ex:
        return jsonify({'error': str(ex)}), 400

    if 'project' in request.args:
        observations = mongo.db.observation.find({"uploaded_at": {"$gt": begin_date, "$lt":finish_date},
            "project":request.args.get('project')}).skip(int(limit)*(int(page)-1)).limit(int(limit)).sort('uploaded_at',pymongo.DESCENDING)
    else:
        observations = mongo.db.observation.find({"uploaded_at": {"$gt": begin_date, 
            "$lt":finish_date}}).skip(int(limit)*(int(page)-1)).limit(int(limit)).sort('uploaded_at',pymongo.DESCENDING)


    output = []
    for ob in observations:
        output.append(ob)
    app.logger.info('Observations send successfully.')
    return JSONEncoder().encode(output)


@app.route('/observations/<observation_id>', methods=['GET'])
def get_observation(observation_id):
    try:
        observation = mongo.db.observation.find_one({'_id': ObjectId(observation_id)})
    except Exception as e:
        app.logger.warning("Not a correct observation id.")
        return jsonify(error="Not a correct observation id."), 400
    if observation is None:
        app.logger.warning('Observation %s not found.', observation_id)
        return jsonify({'error': 'Observation ' + observation_id + 'not found.'}), 404
    app.logger.info('Received %s observation successfully.', observation_id)
    return JSONEncoder().encode(observation)


@app.route('/observations', methods=['POST'])
def post_observation():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        app.logger.warning("Failed to decode JSON object.")
        return jsonify(error="Failed to decode JSON object."), 400 
    if 'project' not in data:
        return jsonify(error="Not project in the observation."), 400 
    if 'created_at' not in data:
        return jsonify(error="Not created_at in the observation."), 400 
    if 'uploaded_at' not in data:
        return jsonify(error="Not uploaded_at in the observation."), 400 
    data.update({'created_at':datetime.strptime(data['created_at'],'%Y-%m-%dT%H:%M:%S.%fZ'),
        'uploaded_at':datetime.strptime(data['uploaded_at'],'%Y-%m-%dT%H:%M:%S.%fZ')})
    _id = mongo.db.observation.insert_one(data).inserted_id
    app.logger.info('Observation %s generated successfully.', str(_id))
    return jsonify({'id':str(_id)}), 201 


### Observation example:
#{
#    "ec5_uuid": "e9e7ed13-aa20-4b74-8cd8-521bf7097d16",
#    "created_at": "2019-10-12T20:57:41.479Z",
#    "uploaded_at": "2019-10-12T22:22:46.000Z",
#    "title": "e9e7ed13-aa20-4b74-8cd8-521bf7097d16",
#    "1_Share_your_nick_wi": "AAM-TB",
#    "2_Date": "12/10/2019",
#    "3_Time": "22:56:37",
#    "4_Location": {
#        "latitude": 41.646183,
#        "longitude": -0.885127,
#        "accuracy": 6,
#        "UTM_Northing": 4612654,
#        "UTM_Easting": 676120,
#        "UTM_Zone": "30T"
#    }
#}


##################### image part #####################

@app.route('/images', methods=['POST'])
def post_image():
    if 'image' not in request.files:
        app.logger.warning("Not image send.")
        return jsonify(warning="Not image send."), 200 
    file = request.files['image']
    if file.filename == '':
        app.logger.warning("No selected file.")
        return jsonify(error="No selected file."), 400 
    if file and allowed_file(file.filename):
        name = ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=6))
        filename = secure_filename(file.filename)
        name = date.today().strftime('%Y-%m-%d') + '-' + name + '-' + filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], name))
        app.logger.info("File %s saved properly.",name)
        return jsonify({'id':name}), 201
    else:
        app.logger.warning("Extension not admited.")
        return jsonify(error="Extension not admited."), 400

@app.route('/test', methods=['POST'])
def process_image():
    #f = Image.open('./img/6uYT02action-street-spectra_1.jfif')
    #exif = { ExifTags.TAGS[k]: v for k, v in f._getexif().items() if k in ExifTags.TAGS }
    exif = get_exif('./img/6uYT02action-street-spectra_1.jfif')
    print(exif)

    labeled = get_labeled_exif(exif)
    print(labeled)

    geotags = get_geotagging(exif)
    print(geotags)

    return jsonify(ok="ok."), 200

def get_exif(filename):
    image = Image.open(filename)
    image.verify()
    return image._getexif()

def get_labeled_exif(exif):
    labeled = {}
    for (key, val) in exif.items():
        labeled[TAGS.get(key)] = val
    return labeled


def get_geotagging(exif):
    if not exif:
        raise ValueError("No EXIF metadata found")

    geotagging = {}
    for (idx, tag) in TAGS.items():
        if tag == 'GPSInfo':
            if idx not in exif:
                raise ValueError("No EXIF geotagging found")

            for (key, val) in GPSTAGS.items():
                if key in exif[idx]:
                    geotagging[val] = exif[idx][key]

    return geotagging

#exif = get_exif('image.jpg')
#geotags = get_geotagging(exif)
#print(geotags)


# curl -X POST -F "file=@a.png" localhost:5000/image
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'jfif'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS



##################### Resources (class) #####################

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.__str__()
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


def to_date(date_string): 
    try:
        return datetime.strptime(date_string, '%Y-%m-%d')
    except ValueError:
        raise ValueError('{} is not valid date in the format YYYY-MM-DD'.format(date_string))

