##################### Imports #####################
from flask import Flask, jsonify, request

from application import config
import os
from flask_cors import CORS
from datetime import datetime
from flask_pymongo import PyMongo, ObjectId
import logging
import json
from datetime import datetime
import pymongo
from werkzeug.utils import secure_filename


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


##################### observation part #####################

@app.route('/observation', methods=['GET'])
def get_observation():
    day = request.args.get('day')
    month = request.args.get('month')
    year = request.args.get('year')
    if year is not None:
        if month is not None:
            if day is not None:
                date = datetime(int(year), int(month), int(day), 1)
            else:
                date = datetime(int(year), int(month), 1, 1)
        else:
            date = datetime(int(year), 1, 1, 1)
    else:
        return get_all_observations()

    observations = mongo.db.observation.find({"uploaded_at": {"$gt": date}})#.sort('uploaded_at',pymongo.DESCENDING)
    output = []
    for ob in observations:
        output.append(ob)
    app.logger.info('Observations send successfully.')
    return JSONEncoder().encode(output)


@app.route('/observations', methods=['GET']) 
def get_all_observations():
    observations = mongo.db.observation.find()
    output = []
    for observation in observations:
        output.append(observation) 
    app.logger.info('Observations send successfully.')
    return JSONEncoder().encode(output)


@app.route('/observation', methods=['POST'])
def post_observation():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        app.logger.warning("Failed to decode JSON object.")
        return jsonify(error="Failed to decode JSON object."), 400 
    data.update({'created_at':datetime.strptime(data['created_at'],'%Y-%m-%dT%H:%M:%S.%fZ'),
        'uploaded_at':datetime.strptime(data['uploaded_at'],'%Y-%m-%dT%H:%M:%S.%fZ')})
    _id = mongo.db.observation.insert_one(data).inserted_id
    app.logger.info('Observation %s generated successfully.', str(_id))
    return jsonify({'id':str(_id), 'ok': True, 'msg': 'Observation created successfully.'}), 201 


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

@app.route('/image', methods=['POST'])
def post_image():
    if 'file' not in request.files:
        app.logger.warning("Not image send.")
        return jsonify(error="Not image send."), 400 
    file = request.files['file']
    if file.filename == '':
        app.logger.warning("No selected file.")
        return jsonify(error="No selected file."), 400 
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        app.logger.info("File %s saved properly.",filename)
        return jsonify(info="File saved properly."), 200 
    else:
        app.logger.warning("Extension not admited.")
        return jsonify(error="Extension not admited."), 400


# curl -X POST -F "file=@a.png" localhost:5000/image
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
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

