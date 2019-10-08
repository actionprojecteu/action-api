const mongoose = require('mongoose');

//Set up default mongoose connection
var mongoDB = 'mongodb://'+process.env.MONGO_IP+'/'+process.env.MONGO_DB
mongoose.connect(mongoDB, { useNewUrlParser: true, user: process.env.MONGO_USERNAME, pass: process.env.MONGO_PASSWORD });

//Get the default connection
var db = mongoose.connection;

//Bind connection to error event (to get notification of connection errors)
db.on('error', console.error.bind(console, 'MongoDB connection error:'));
db.once('open', function callback() {
  console.log('Connected to DB');
});

module.export = db;
