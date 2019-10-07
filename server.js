'use strict';

const express = require('express');
const bodyParser = require('body-parser');

var observations = require('./routes/observations')

const PORT = 8888;

//App

var app = express();

//app.use(bodyParser.urlencoded({ extended:true }));
app.use(bodyParser.json());
app.use(function(req, res, next) {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
  next();
});

var router = express.Router();

router.get('/', function(req, res) {
  res.json({
    message: 'Hello world\n'
  });
});

app.use(router)
app.use(observations)

app.listen(PORT);

console.log("Running on server:" + PORT);
