const browser = require('webextension-polyfill')
const indieauth = require('webextension-indieauth')
const micropub = require('micropub-client2')
// const roots = require('Roots')
const $ = document.querySelector.bind(document)

window.addEventListener('DOMContentLoaded', async () => {
  const user = await indieauth.getUser()
  if (!user.me) {
    $('body').innerHTML = '<p>Use the toolbar button to sign in!</p>'
    return
  }

  $('body').innerHTML = `
    <div id=reply></div>
    <p><strong>Your posts related to this page:</strong></p>
    <ul id=your_posts></ul>
    <p><strong>Others' posts related to this page:</strong></p>
    <ul id=others_posts></ul>

    <p><strong>Mood indicator:</strong></p>
    <input type=range min=0 max=255 id=moodStartR>
    <input type=range min=0 max=255 id=moodStartG>
    <input type=range min=0 max=255 id=moodStartB>
    <input type=range min=0 max=255 id=moodEndR>
    <input type=range min=0 max=255 id=moodEndG>
    <input type=range min=0 max=255 id=moodEndB>

    <div id=braid></div>
    <!--div id=content></div-->
  `

  // roots(`${user.me}/now`, {
  //   moodStartR: '/mood/start/0',
  //   moodStartG: '/mood/start/1',
  //   moodStartB: '/mood/start/2',
  //   moodEndR: '/mood/end/0',
  //   moodEndG: '/mood/end/1',
  //   moodEndB: '/mood/end/2'
  // }, (data) => {
  //   console.log(data)
  // })

  let myWindowId
  // const contentBox = document.querySelector('#content')
  // window.addEventListener('mouseover', () => {
  //   contentBox.setAttribute('contenteditable', true)
  // })
  // window.addEventListener('mouseout', () => {
  //   contentBox.setAttribute('contenteditable', false)
  //   browser.tabs.query({ windowId: myWindowId, active: true }).then((tabs) => {
  //     const contentToStore = {}
  //     contentToStore[tabs[0].url] = contentBox.textContent
  //     browser.storage.local.set(contentToStore)
  //   })
  // })
  async function updateContent () {
    const pub = new micropub.MicropubClient(user.endpoints.micropub, user.accessToken)
    browser.tabs.query({ windowId: myWindowId, active: true })
      .then(async (tabs) => {
        const results = await pub.query('', tabs[0].url)
        if (results) {
          const yourPosts = document.querySelector('#your_posts')
          yourPosts.innerText = JSON.stringify(results.items)
          // for (const result of results.items) {
          //   const listItem = document.createElement('li')
          //   listItem.textContent = JSON.stringify(result)
          //   yourPosts.appendChild(listItem)
          // }
        }
        return browser.storage.local.get(tabs[0].url)
      })
      // .then((storedInfo) => {
      //   contentBox.textContent = storedInfo[Object.keys(storedInfo)[0]]
      // })
  }
  browser.tabs.onActivated.addListener(updateContent)
  browser.tabs.onUpdated.addListener(updateContent)
  browser.windows.getCurrent({ populate: true }).then((windowInfo) => {
    myWindowId = windowInfo.id
    updateContent()
  })
})
