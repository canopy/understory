const path = require('path')

module.exports = {
  entry: {
    browser: './understory.ts'
  },
  output: {
    path: path.resolve(__dirname),
    filename: 'understory/indieweb/understory.js',
    library: 'understory'
  },
  devtool: 'eval-source-map',
  resolve: {
    extensions: ['', '.webpack.js', '.web.js', '.ts', '.tsx', '.js']
  },
  module: {
    rules: [
      { test: /\.tsx?$/, loader: 'ts-loader' },
      { test: /\.js$/, loader: 'source-map-loader' }
    ]
  }
}
