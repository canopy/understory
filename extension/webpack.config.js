const path = require('path')

module.exports = {
  entry: {
    background: './src/background.ts',
    content: './src/content.ts',
    popup: './src/popup.ts',
    devtools: './src/devtools.ts',
    sidebar: './src/sidebar.ts',
    home: './src/home.ts',
    newtab: './src/newtab.ts',
    theme: './src/theme.ts'
  },
  resolve: {
    extensions: ['', '.webpack.js', '.web.js', '.ts', '.tsx', '.js']
  },
  mode: 'none',
  node: false,
  module: {
    rules: [
      { test: /\.tsx?$/, loader: 'ts-loader' }
    ]
  },
  output: {
    path: path.resolve(__dirname, 'addon'),
    filename: '[name]/index.js'
  }
}
