const browser = require('webextension-polyfill')
const indieauth = require('webextension-indieauth')
const micropub = require('micropub-client2')
const microsub = require('microsub-client')
const _ = browser.i18n.getMessage
const $ = document.querySelector.bind(document)

let clientID
if (navigator.userAgent.indexOf('Firefox') > 0) {
  clientID = 'https://addons.mozilla.org/addon/liana'
} else if (navigator.userAgent.indexOf('Chrome') > 0) {
  clientID = 'https://chrome.google.com/webstore/detail' +
    '/liana/mhhlbkkefhiobmekahglonoabimiajme'
}

window.addEventListener('DOMContentLoaded', async () => {
  const user = await indieauth.getUser()
  let handler
  if (user.me) {
    browser.tabs.query({ active: true, currentWindow: true }, tabs => {
      browser.tabs.sendMessage(tabs[0].id, { from: 'popup', subject: 'Info' },
        createToolbar)
    })
    browser.browserAction.setTitle({ title: _('profileSignedInAs', user.me) })
    let visibility = ''
    const micropubConfig = await browser.storage.local.get(['micropubConfig'])
    if ('visibility' in micropubConfig.micropubConfig) {
      visibility = `<p id=visibility><label>Private <input type=checkbox
        name=private checked></label></p>`
    }
    $('body').innerHTML = `
      ${visibility}
      <div id=toolbar></div>
      <form id=signout>
        <div class=submit><button>${_('profileSignoutButton')}</button></div>
      </form>
    `
    handler = () => {
      indieauth.signOut()
      window.close()
    }
  } else {
    $('body').innerHTML = `
      <form id=signin>
        <input name=me type=text placeholder="${_('signinPlaceholder')}">
        <div class=submit><button>${_('signinButton')}</button></div>
      </form>
    `
    handler = async () => {
      let me = $('input').value
      if (!(me.startsWith('http://') || me.startsWith('https://'))) {
        me = 'https://' + me
      }
      indieauth.signIn(me, clientID)
    }
  }
  $('form').addEventListener('submit', (ev) => {
    ev.preventDefault()
    handler()
  })
})

const createToolbar = (info) => {
  if (info === undefined) {
    return
  }
  const toolbar = document.createElement('div')
  for (const button of info.buttons) {
    toolbar.appendChild(createButton(button, info))
  }
  $('#toolbar').appendChild(toolbar)
}

const createButton = (kind, info) => {
  const xmlns = 'http://www.w3.org/2000/svg'
  const icon = icons[kind]
  const svg = document.createElementNS(xmlns, 'svg')
  svg.setAttributeNS(null, 'viewBox', `0 0 ${icon[0]} ${icon[1]}`)
  svg.setAttributeNS(null, 'width', icon[0] / 36)
  svg.setAttributeNS(null, 'height', icon[1] / 36)
  const path = document.createElementNS(xmlns, 'path')
  path.setAttributeNS(null, 'd', icon[2])
  path.setAttributeNS(null, 'fill', '#2aa198')
  svg.appendChild(path)
  const button = document.createElement('span')
  button.title = _(`postkind${kind}`)
  button.appendChild(svg)
  button.addEventListener('click', async (ev) => {
    if (kind === 'Reply') {
      window.foo = 'BAR'
      browser.sidebarAction.open()
    } else {
      const user = await indieauth.getUser()
      const pub = new micropub.MicropubClient(user.endpoints.micropub, user.accessToken)
      const sub = new microsub.MicrosubClient(user.endpoints.microsub, user.accessToken)
      const visibility = $('input[name=private]').checked ? 'private' : 'public'
      const permalink = await icon[3](info, pub, sub, visibility)
      console.log(`Created post at: ${permalink}`)
    }
    // window.close()
  })
  return button
}

const shareTab = async (info, pub, sub, visibility) => {
  return pub.update('/now', {
    add: {
      browsing: [info.url]
    }
  })
}

const createBookmark = async (info, pub, sub, visibility) => {
  browser.bookmarks.create({ title: info.title, url: info.url })
  return pub.create('entry', {
    'bookmark-of': [info.url]
  },
  visibility)
}

const createLike = async (info, pub, sub, visibility) => {
  return pub.create('entry', {
    'like-of': [info.url]
  },
  visibility)
}

// const createIdentification = async (info, pub, sub, visibility) => {
//   return pub.create({
//     type: ['h-entry'],
//     visibility: visibility,
//     properties: {
//       name: `Identified ${info.title}`,
//       'identification-of': [
//         {
//           type: ['h-cite'],
//           properties: {
//             name: info.title,
//             url: info.url
//           }
//         }
//       ]
//     }
//   })
// }

const createFollow = async (info, pub, sub, visibility) => {
  const rawChannels = await sub.getChannels()
  const channels = {}
  rawChannels.forEach(value => {
    channels[value.name] = value.uid
  })
  // console.log(Object.keys(channels))
  const channel = 'IndieWeb' // prompt('Channel name?')
  sub.follow(info.url, channel)

  // return pub.create({
  //   type: ['h-entry'],
  //   visibility: visibility,
  //   properties: {
  //     name: `Followed ${info.title}`,
  //     'follow-of': [
  //       {
  //         type: ['h-cite'],
  //         properties: {
  //           name: info.title,
  //           url: info.url
  //         }
  //       }
  //     ]
  //   }
  // })
}

const createRepost = async (info, pub, sub, visibility) => {
  return pub.create({
    type: ['h-entry'],
    visibility: visibility,
    properties: {
      name: `Reposted ${info.title}`,
      'repost-of': [
        {
          type: ['h-cite'],
          properties: {
            name: info.title,
            url: info.url
          }
        }
      ]
    }
  })
}

const createRSVP = async (info, pub, sub, visibility) => {
  return pub.create({
    type: ['h-entry'],
    visibility: visibility,
    properties: {
      'in-reply-to': [info.url],
      rsvp: ['yes']
    }
  })
}

const icons = {
  Share: [576, 512, `M 256,140
                     L 256,56
                     C 256,32 228,24 216,36
                     L 40,192
                     C 32,200 32,216 40,224
                     L 216,380
                     C 228,392 256,384 256,360
                     L 256,276
                     C 416,276 468,332 432,460
                     C 424,484 452,488 472,476
                     C 528,444 544,368 544,320
                     C 544,192 416,140 256,140
                     Z`, shareTab],
  Reply: [576, 512, `M 256,140
                     L 256,56
                     C 256,32 228,24 216,36
                     L 40,192
                     C 32,200 32,216 40,224
                     L 216,380
                     C 228,392 256,384 256,360
                     L 256,276
                     C 416,276 468,332 432,460
                     C 424,484 452,488 472,476
                     C 528,444 544,368 544,320
                     C 544,192 416,140 256,140
                     Z`],
  Bookmark: [576, 512, `M 144,32
                        C 136,32 128,40 128,48
                        L 128,480
                        L 288,384
                        L 448,480
                        L 448,48
                        C 448,40 440,32 432,32
                        Z`, createBookmark],
  Like: [576, 512, `M 288,92
                    C 264,64 224,32 160,32
                    C 64,32 32,80 32,168
                    C 32,232 92,292 96,296
                    L 268,472
                    C 280,484 296,484 308,472
                    L 480,296
                    C 484,292 544,232 544,168
                    C 544,80 512,32 416,32
                    C 352,32 312,64 288,92
                    Z`, createLike],
  Follow: [576, 512, `M 128,352
                      C 92,352 64,380 64,416
                      C 64,452 92,480 128,480
                      C 164,480 192,452 192,416
                      C 192,380 164,352 128,352
                      Z

                      M 64,208
                      L 64,272
                      C 64,280 72,288 80,288
                      C 200,288 256,344 256,464
                      C 256,472 264,480 272,480
                      L 336,480
                      C 344,480 352,472 352,464
                      C 352,288 256,192 80,192
                      C 72,192 64,200 64,208
                      Z

                      M 64,48
                      L 64,112
                      C 64,120 72,128 80,128
                      C 296,128 416,248 416,464
                      C 416,472 424,480 432,480
                      L 496,480
                      C 504,480 512,472 512,464
                      C 512,188 356,32 80,32
                      C 72,32 64,40 64,48
                      Z`, createFollow],
  Repost: [576, 512, `M 320,140
                      L 320,56
                      C 320,32 348,24 360,36
                      L 536,192
                      C 544,200 544,216 536,224
                      L 360,380
                      C 348,392 320,384 320,360
                      L 320,276
                      C 160,276 108,332 144,460
                      C 152,484 124,488 104,476
                      C 48,444 32,368 32,320
                      C 32,192 160,140 320,140
                      Z`, createRepost],
  RSVP: [576, 512, `M 112,72
                    C 96,72 88,80 88,96
                    L 88,148
                    C 88,156 92,160 100,160
                    L 468,160
                    C 476,160 480,156 480,148
                    L 480,96
                    C 480,80 472,72 456,72
                    L 376,72
                    L 376,52
                    C 376,44 372,40 364,40
                    L 340,40
                    C 332,40 328,44 328,52
                    L 328,72
                    L 240,72
                    L 240,52
                    C 240,44 236,40 228,40
                    L 204,40
                    C 196,40 192,44 192,52
                    L 192,72
                    Z

                    M 100,184
                    C 92,184 88,188 88,196
                    L 88,448
                    C 88,464 96,472 112,472
                    L 456,472
                    C 472,472 480,464 480,448
                    L 480,196
                    C 480,188 476,184 468,184
                    Z

                    M 268,324
                    L 340,240
                    L 388,284
                    L 272,408
                    L 176,328
                    L 216,276
                    Z`, createRSVP]
}

// Add: [576, 512, `M 368,96
//                  C 304,96 256,144 256,208
//                  C 256,272 304,320 368,320
//                  C 432,320 480,272 480,208
//                  C 480,144 432,96 368,96
//                  Z
//
//                  M 288,320
//                  L 224,344
//                  C 192,364 192,384 192,396
//                  L 192,456
//                  C 192,468 204,480 216,480
//                  L 520,480
//                  C 532,480 544,468 544,456
//                  L 544,396
//                  C 544,384 544,364 512,344
//                  L 448,320
//                  C 416,352 320,352 288,320
//                  Z
//
//                  M 108,32
//                  C 100,32 96,36 96,44
//                  L 96,96
//                  L 44,96
//                  C 36,96 32,100 32,108
//                  L 32,148
//                  C 32,156 36,160 44,160
//                  L 96,160
//                  L 96,212
//                  C 96,220 100,224 108,224
//                  L 148,224
//                  C 156,224 160,220 160,212
//                  L 160,160
//                  L 212,160
//                  C 220,160 224,156 224,148
//                  L 224,108
//                  C 224,100 220,96 212,96
//                  L 160,96
//                  L 160,44
//                  C 160,36 156,32 148,32
//                  Z`, createIdentification],
