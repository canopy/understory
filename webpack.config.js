const path = require('path')

const config = {
  entry: './index.ts',
  resolve: {
    extensions: ['', '.webpack.js', '.web.js', '.ts', '.tsx', '.js']
  },
  mode: 'none',
  node: false,
  module: {
    rules: [
      { test: /\.tsx?$/, loader: 'ts-loader' }
    ]
  }
}

const browserConfig = Object.assign({}, config, {
  output: {
    path: path.resolve(__dirname),
    filename: 'understory/web/framework/static/understory.js',
    library: 'understory'
  }
})
const extensionConfig = Object.assign({}, config, {
  output: {
    path: path.resolve(__dirname),
    filename: 'understory.js',
    library: {
      name: 'understory',
      type: 'commonjs-module'
    }
  }
})

module.exports = [
  browserConfig, extensionConfig
]
