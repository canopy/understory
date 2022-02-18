const browser = require('webextension-polyfill')

function handleShown () {
  console.log('panel is being shown')
  // const scriptToAttach = 'document.body.innerHTML = 'Hi from devtools''
  // browser.runtime.sendMessage({
  //     from: 'devtools',
  //     tabId: browser.devtools.inspectedWindow.tabId,
  //     script: scriptToAttach
  // })
}

function handleHidden () {
  console.log('panel is being hidden')
}

browser.devtools.panels.create('Microformats', 'icons/star.png', 'panel.html')
  .then((newPanel) => {
    newPanel.onShown.addListener(handleShown)
    newPanel.onHidden.addListener(handleHidden)
  })
