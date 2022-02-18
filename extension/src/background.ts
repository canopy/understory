const browser = require('webextension-polyfill')
require('webextension-indieauth')
const micropub = require('micropub-client2')
const _ = browser.i18n.getMessage

window.postSignIn = async function postSignIn (user) {
  const pub = new micropub.MicropubClient(user.endpoints.micropub, user.accessToken)
  browser.storage.local.set({ micropubConfig: await pub.getConfig() })
  browser.browserAction.setTitle({ title: _('profileSignedInAs', user.me) })
}

window.postSignOut = async function postSignOut () {
  browser.browserAction.setTitle({ title: _('signinIconTooltip') })
}

// function handleMessage(request, sender, sendResponse) {
//     if (request.from === "devtools") {
//         browser.tabs.executeScript(request.tabId, {
//             code: request.script
//         });
//     }
// }
// browser.runtime.onMessage.addListener(handleMessage)
