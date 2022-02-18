const browser = require('webextension-polyfill')
const indieauth = require('webextension-indieauth')
const micropub = require('micropub-client2')
const _ = browser.i18n.getMessage
const $ = document.querySelector.bind(document)

window.addEventListener('DOMContentLoaded', async () => {
  const user = await indieauth.getUser()
  if (!user.me) {
    $('body').innerHTML = '<p>Use the toolbar button to sign in!</p>'
    return
  }

  $('body').innerHTML = `
    <form id=newnote>
      <textarea name=content placeholder="${_('newNotePlaceholder')}"></textarea>
      <div class=submit><button id=create>${_('createButton')}</button></div>
    </form>
  `
  $('form').addEventListener('submit', async (ev) => {
    ev.preventDefault()
    const note = $('textarea').value
    const pub = new micropub.MicropubClient(user.endpoints.micropub, user.accessToken)
    createNote(note, pub)
  })
})

const createNote = async (content, pub, sub) => {
  pub.create({
    type: ['h-entry'],
    properties: {
      content: [content]
    }
  })
}
