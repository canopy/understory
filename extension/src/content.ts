const browser = require('webextension-polyfill')
const { mf2 } = require('microformats-parser')
const $ = document.querySelector.bind(document)

const configureToolbar = () => {
  // TODO recipe, repo, issue
  const buttons = []
  const data = mf2($('html').innerHTML, { baseUrl: window.location.href })
  if (data.items.length) {
    data.items.forEach((value, index) => {
      let itemURL
      try {
        itemURL = value.properties.url[0].replace(/^\/|\/$/g, '')
      } catch (e) {
        if (e instanceof TypeError) {
          itemURL = null
        }
      }
      const windowURL = window.location.href.replace(/^\/|\/$/g, '')
      const windowPath = window.location.pathname.replace(/^\/|\/$/g, '')
      switch (value.type[0]) {
        case 'h-entry':
          if (itemURL === windowURL || itemURL === windowPath) {
            buttons.push('Reply')
            buttons.push('Repost')
          }
          break
        // case 'h-feed':
        //   // TODO tantek's feed is nested inside his card
        //   // TODO aaron's feed is implied from flat entries
        //   buttons.push('Follow')
        //   break
        case 'h-event':
          buttons.push('RSVP')
          break
        case 'h-card':
          if (itemURL === windowURL || itemURL === windowPath) {
            buttons.push('Follow')
          }
          break
      }
    })
  }
  buttons.push('Bookmark')
  buttons.push('Like')
  buttons.push('Share')
  browser.runtime.onMessage.addListener((msg, sender, response) => {
    if ((msg.from === 'popup') && (msg.subject === 'Info')) {
      response({
        url: window.location.href,
        title: document.title,
        buttons: buttons
      })
    }
  })
}

setTimeout(configureToolbar, 500)

// var recognizer = new SpeechRecognition()
// // recognizer.continuous = true
// recognizer.onresult = function(event) {
//   transcription = ''
//   for (var i = event.resultIndex i < event.results.length i++) {
//     if (event.results[i].isFinal) {
//       transcription = event.results[i][0].transcript + ' (Confidence: ' + event.results[i][0].confidence + ')'
//     } else {
//       transcription += event.results[i][0].transcript
//     }
//   }
//   noteContentEditor.textContent = transcription
// }
// document.querySelector('button#dictate').addEventListener('click', (ev) => {
//   console.log(recognizer)
// })
