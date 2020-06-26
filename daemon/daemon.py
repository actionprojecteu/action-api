##################### Imports #####################

import logging
from pymongo import MongoClient

from PIL import Image
from PIL.ExifTags import TAGS,GPSTAGS


##################### logging part #####################

logging.basicConfig(filename='log/daemon.log', filemode='w', level=logging.INFO
	, format='%(asctime)s %(levelname)s %(name)s : %(message)s')
logging.info('This will get logged to a file')


##################### mongo part #####################

MONGO_URI = 'mongodb://192.168.123.245:27017/'
#MONGO_URI = 'mongodb://localhost:27017/'
client = MongoClient(MONGO_URI)


##################### image part #####################

def process_image(filename,db):
    data = db.observation.find_one({"image":filename})
    filename = './img/'+ filename
    exif = get_exif(filename)
    if not exif:
        return -2
    labeled = get_labeled_exif(exif)
    if not labeled:
        return -3
    data.update({'image_info':labeled})
    db.observation.update_one({'_id':data['_id']},{"$set":data})

    return 0, labeled

def get_exif(filename):
    image = Image.open(filename)
    #image.verify()
    image.load()
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


##################### main part #####################

def main():
    db = client.get_database('observation')
    logging.info('Daemon starts')
    for image in db.image.find({"status":"pending"}):
        if db.observation.count_documents({"image":image['id']}) != 0:
            logging.info('Processing image: %s',image['id'])
            status,labeled = process_image(image['id'],db)
            if status == 0:
                image.update({"status":"done",'image_info':labeled})
                logging.info('Image: %s processed correctly',image['id'])
            if status == -2:
                image.update({"status":"error","error":"No exif"})
                logging.error('Error in image: %s with error: No exif',image['id'])
            if status == -3:
                image.update({"status":"error","error":"No labeled"})
                logging.error('Error in image: %s with error: No labeled',image['id'])
            if status == -4:
                image.update({"status":"error","error":"No geotags"})
                logging.error('Error in image: %s with error: No geotags',image['id'])
            if status < 0:
                image.update({"status":"error","error":"general error"})
                logging.error('Error in image: %s with error: general error',image['id'])
            db.image.update_one({'_id':image['_id']},{"$set":image})
        

    logging.info('Daemon finishes')


if __name__ == "__main__":
    main()