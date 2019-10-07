var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var ObservationSchema = new Schema({
	datasource : { type: String },
	userid : { type: String },
  observation: { type: Object }
},{
  versionKey: false // You should be aware of the outcome after set to false
});
var Observations = mongoose.model('Observation',ObservationSchema,'observations');

module.exports.Observations = Observations;
module.exports.Schema = ObservationSchema;
