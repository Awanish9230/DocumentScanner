const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const documentSchema = new Schema({
  user: { type: Schema.Types.ObjectId, ref: 'User', required: true },
  title: { type: String },
  ocrText: { type: String },
  pages: { type: Number, default: 1 },
  pdfPath: { type: String },
  imagePath: { type: String },
  createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Document', documentSchema);
