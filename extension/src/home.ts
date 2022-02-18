const indieauth = require('webextension-indieauth')
// const roots = require('Roots')
const $ = document.querySelector.bind(document)

window.addEventListener('DOMContentLoaded', async () => {
  const user = await indieauth.getUser()
  if (!user.me) {
    $('body').innerHTML = '<p>Use the toolbar button to sign in!</p>'
    return
  }

  $('body').innerHTML = `
    <p><strong>Shared browsing:</strong></p>
    <ul id=my_shared_browsing>
    </ul>
  `

  // roots('http://angelo:8000/now', { browsing: [] }, {
  //   my_shared_browsing: '/browsing'
  // }, (data) => {
  //   console.log(data)
  // })
})
