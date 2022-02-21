const path = require('path')

const config = {
  entry: 'web.ts/index.ts',
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
    filename: 'web/framework/static/understory.js',
    library: 'web'
  }
})
const extensionConfig = Object.assign({}, config, {
  output: {
    path: path.resolve(__dirname),
    filename: 'dist/web.js',
    library: {
      name: 'web',
      type: 'commonjs-module'
    }
  }
})

module.exports = [
  browserConfig, extensionConfig
]
