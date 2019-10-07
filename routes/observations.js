var express = require('express')
var router = express.Router()
var db = require('../db_connection')
var Observations = require('../models/observation.js').Observations;


// middleware that is specific to this router
router.use(function timeLog (req, res, next) {
  console.log('Time: ', Date.now())
  next()
})

router.get('/observations', function (req, res) {
  console.log('Get Observations')
  Observations.find({},function(err,doc){
    res.json(doc);
  });
})

router.post('/observations', function (req, res){
  console.log(req.body)
  let observation = new Observations(req.body)
  observation.save(function(error) {
     res.status(201).send("Observation inserted!");
     if (error) {
       res.status(500).res.json({
         message: error
       });
     }
  });
})

module.exports = router
