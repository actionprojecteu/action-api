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


##################### Token part #####################

@app.before_request
def before_request():
    if request.method != 'GET':
        if 'Authorization' not in request.headers:
            app.logger.warning("No auth sended.")
            return jsonify(error="No auth send."), 401
        if mongo.db.token.count_documents({"token":request.headers['Authorization']}) == 0 :
            app.logger.warning("Token: %s not valid.", request.headers['Authorization'])
            return jsonify(error="Token not valid."), 401


##################### observation part #####################

@app.route('/observations', methods=['GET'])
def get_list_observation():
    limit = request.args.get('limit', default = 5, type=int)
    page = request.args.get('page', default = 1, type=int)

    try:
        begin_date = to_date(request.args.get('begin_date', default='0001-01-01'))
        finish_date = to_date(request.args.get('finish_date', default = date.max.strftime('%Y-%m-%d')))
    except ValueError as ex:
        return jsonify({'error': str(ex)}), 400

    if 'project' in request.args:
        observations = mongo.db.observation.find({"created_at": {"$gt": begin_date, "$lt":finish_date},
            "project":request.args.get('project')}).skip(int(limit)*(int(page)-1)).limit(int(limit)).sort('uploaded_at',pymongo.DESCENDING)
    else:
        observations = mongo.db.observation.find({"created_at": {"$gt": begin_date, 
            "$lt":finish_date}}).skip(int(limit)*(int(page)-1)).limit(int(limit)).sort('uploaded_at',pymongo.DESCENDING)


    output = []
    for ob in observations:
        output.append(ob)
    app.logger.info('Observations send successfully.')
    return JSONEncoder().encode(output)


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
        data['created_at'] = "0001-01-02T00:00:00.000000Z"
    if 'uploaded_at' not in data:
        data['uploaded_at'] =  datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    data.update({'created_at':datetime.strptime(data['created_at'],'%Y-%m-%dT%H:%M:%S.%fZ'),
        'uploaded_at':datetime.strptime(data['uploaded_at'],'%Y-%m-%dT%H:%M:%S.%fZ')})
    _id = mongo.db.observation.insert_one(data).inserted_id
    app.logger.info('Observation %s generated successfully.', str(_id))
    if 'image' not in data:
        return jsonify({'id':str(_id),'warning':'no image key in the observarion'}), 201 
    return jsonify({'id':str(_id)}), 201


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


@app.route('/observations/<observation_id>', methods=['PUT'])
def put_observation(observation_id):
    try:
        data = request.get_json(force=True)
    except Exception as e:
        app.logger.warning("Failed to decode JSON object.")
        return jsonify(error="Failed to decode JSON object."), 400
    try:
        success = mongo.db.observation.update({"_id": ObjectId(observation_id)}, {"$set": data})
    except Exception as e:
        app.logger.warning("Not a correct observation id: %s .", observation_id)
        return jsonify(error="Not a correct observation id."), 400
    if success.get('updatedExisting') is False:
        app.logger.info('Observation %s not found.', observation_id)
        return jsonify({'ok': False, 'msg': 'Observation '+ observation_id + ' not found.'})
    app.logger.info('Observation %s updated successfully.', observation_id)
    return jsonify({'id':observation_id, 'ok': True, 'msg': 'Observation updated successfully.'})


##################### image part #####################

@app.route('/images', methods=['GET'])
def get_list_images():
    limit = request.args.get('limit', default = 5, type=int)
    page = request.args.get('page', default = 1, type=int)
    observations = mongo.db.image.find().skip(int(limit)*(int(page)-1)).limit(int(limit))
    output = []
    for ob in observations:
        output.append(ob)
    app.logger.info('Images send successfully.')
    return JSONEncoder().encode(output)


@app.route('/images', methods=['POST'])
def post_image():
    if 'image' not in request.files:
        app.logger.warning("Not image send.")
        return jsonify(warning="Not image send."), 200 
    file = request.files['image']
    if file.filename == '':
        app.logger.warning("No selected file.")
        return jsonify(error="No selected file."), 400 
    if not allowed_file(file.filename):
        app.logger.warning("Extension not admited.")
        return jsonify(error="Extension not admited."), 400
    
    name = ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=6))
    filename = secure_filename(file.filename)
    name = date.today().strftime('%Y-%m-%d') + '-' + name + '-' + filename
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], name))
    app.logger.info("File %s saved properly.",name)
    data = {'id':name,'status':'pending','timestamp':datetime.utcnow()}
    _id = mongo.db.image.insert_one(data).inserted_id
    app.logger.info('image %s with id in mongodb: %s created successfully.', name, str(_id))
    return jsonify({'id':name}), 201


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'jpe', 'gif', 'jfif', 'jif', 
    'jfi', 'tiff', 'tiff', 'psd', 'pdf', 'eps', 'ai', 'indd', 'raw', 'svg', 
    'heif', 'webp'])
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

