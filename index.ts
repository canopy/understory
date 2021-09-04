// function bindWebActions() {
//     $$("indie-action").each(function() {
//         this.onclick = function(e) {
//             var action_link = this.querySelector("a");
//             // TODO action_link.attr("class", "fa fa-spinner fa-spin");
//
//             var action_do = this.getAttribute("do");
//             var action_with = this.getAttribute("with");
//
//             // protocolCheck("web+action://" + action_do + "?url=" + action_with,
//             // setTimeout(function() {
//             //     var url = "//canopy.garden/?origin=" + window.location.href +
//             //               "do=" + action_do + "&with=" + action_with;
//             //     var html = `<!--p>Your device does not support web
//             //                 actions<br><em><strong>or</strong></em><br>
//             //                 You have not yet paired your website with
//             //                 your browser</p>
//             //                 <hr-->
//             //                 <p>If you have a website that supports web
//             //                 actions enter it here:</p>
//             //                 <form id=action-handler action=/actions-finder>
//             //                 <label>Your Website
//             //                 <div class=bounding><input type=text
//             //                 name=url></div></label>
//             //                 <input type=hidden name=do value="${action_do}">
//             //                 <input type=hidden name=with value="${action_with}">
//             //                 <p><small>Target:
//             //                 <code>${action_with}</code></small></p>
//             //                 <button>${action_do}</button>
//             //                 </form>
//             //                 <p>If you do not you can create one <a
//             //                 href="${url}">here</a>.</p>`;
//             //     switch (action_do) {
//             //         case "sign-in":
//             //             html = html + `<p>If you are the owner of this site,
//             //                            <a href=/security/identification>sign
//             //                            in here</a>.</p>`;
//             //     }
//             //     html = html + `<p><small><a href=/help#web-actions>Learn
//             //                    more about web actions</a></small></p>`;
//             //     $("#webaction_help").innerHTML = html;
//             //     $("#webaction_help").style.display = "block";
//             //     $("#blackout").style.display = "block";
//             //     $("#blackout").onclick = function() {
//             //         $("#webaction_help").style.display = "none";
//             //         $("#blackout").style.display = "none";
//             //     };
//             // }, 200);
//
//             window.location = action_link.getAttribute("href");
//
//             e.preventDefault ? e.preventDefault() : e.returnValue = false;
//         }
//     });
// }

// $.load(function () {
//   bindWebActions()
//
//   /*
//     $$(".pubkey").each(function() {
//         var armored_pubkey = $(this).text();
//         if (armored_pubkey) {
//             var pubkey = get_pubkey(armored_pubkey);
//             var fingerprint = pubkey.fingerprint.substring(0, 2);
//             for (i = 2; i < 40; i = i + 2)
//                 fingerprint = fingerprint + ":" +
//                               pubkey.fingerprint.substring(i, i + 2);
//             $(this).after("<code class=fingerprint><span>" +
//                           fingerprint.substr(0, 30) + "</span><span>" +
//                           fingerprint.substr(30, 60) + "</span></code>");
//         }
//     });
//     */
//
//   // var mySVG = document.getElementById("action_like");
//   // var svgDoc;
//   // mySVG.addEventListener("load",function() {
//   //     svgDoc = mySVG.contentDocument;
//   //     path = svgDoc.querySelector("path");
//   //     setTimeout(function() {
//   //         path.setAttribute("fill", "red");
//   //         mySVG.setAttribute("class", "icon animated pulse");
//   //     }, 2000);
//   // }, false);
//
//   // $$(".icon").each(function() {
//   //     var svgDoc;
//   //     var mySVG = this;
//   //     mySVG.addEventListener("load", function() {
//   //         svgDoc = mySVG.contentDocument;
//   //         // function z() {
//   //             svgDoc.querySelector("path").setAttribute("fill", "#2aa198");
//   //             // mySVG.setAttribute("class", "icon animated pulse");
//   //         // }
//   //         // setTimeout(z, 2000);
//   //     }, false);
//   // });
//
//   // $("a.quote").click(function() {
//   //     window.location = "web+action://quote=?url=" + window.location +
//   //                       "&quote=" + window.getSelection().toString();
//   //     return false
//   // });
//
//   // $$("#search").submit(function() {
//   //     $.ajax({method: "GET",
//   //              url: "/search?query=" +
//   //                   $(this).find("input[name=query]").val()})
//   //         .done(function(msg) { $("#resource_preview").html(msg); });
//   //     return false
//   // });
// })

// function get_pubkey (armored_pubkey) {
//   /*
//     handle displaying of fingerprints
//
//     */
//   let foundKeys = openpgp.key.readArmored(armored_pubkey).keys
//   if (!foundKeys || foundKeys.length !== 1) {
//     throw new Error('No key found or more than one key')
//   }
//   const pubKey = foundKeys[0]
//   foundKeys = null
//   return pubKey.primaryKey
// }

// activate fast AES-GCM mode (not yet OpenPGP standard)
// openpgp.config.aead_protect = true;  // TODO move to after openpgp load

// function sign (payload, handler) {
//   // XXX var pubkey = localStorage["pubkey"];
//   // XXX var privkey = localStorage["privkey"];
//   // XXX var passphrase = "";  // window.prompt("please enter the pass phrase");
//
//   // XXX // console.log(openpgp.key.readArmored(privkey));
//   // XXX // var privKeyObj = openpgp.key.readArmored(privkey).keys[0];
//   // XXX // privKeyObj.decrypt(passphrase);
//
//   // XXX // options = {
//   // XXX //     message: openpgp.cleartext.fromText('Hello, World!'),
//   // XXX //     privateKeys: [privKeyObj]
//   // XXX // };
//
//   // XXX // openpgp.sign(options).then(function(signed) {
//   // XXX //     cleartext = signed.data;
//   // XXX //     console.log(cleartext);
//   // XXX // });
//
//   // XXX openpgp.key.readArmored(privkey).then(function(privKeyObj) {
//   // XXX     // XXX var privKeyObj = z.keys[0];
//   // XXX     // XXX privKeyObj.decrypt(passphrase);
//   // XXX     // XXX var options = {data: payload, privateKeys: privKeyObj};
//   // XXX     var options = {message: openpgp.cleartext.fromText("helloworld"),
//   // XXX                    privateKeys: [privKeyObj]}
//   // XXX     openpgp.sign(options).then(handler);
//   // XXX });
// }

// function sign_form (form, data, submission_handler) {
//   const button = form.find('button')
//   button.prop('disabled', true)
//   const timestamp = Date.now()
//   form.append("<input type=hidden name=published value='" +
//                 timestamp + "'>")
//   data.published = timestamp
//   const payload = JSON.stringify(data, Object.keys(data).sort(), '  ')
//   sign(payload, function (signed) {
//     form.append('<input id=signature type=hidden name=signature>')
//     $('#signature').val(signed.data)
//     // XXX form.submit();
//     submission_handler()
//     button.prop('disabled', false)
//   })
// }

// function getTimeSlug (when) {
//   const centiseconds = (((when.hours() * 3600) +
//                          (when.minutes() * 60) +
//                          when.seconds()) * 100) +
//                        Math.round(when.milliseconds() / 10)
//   return when.format('Y/MM/DD/') + num_to_sxgf(centiseconds, 4)
// }

// function getTextSlug (words) {
//   let padding = ''
//   if (words.slice(-1) == ' ') { padding = '_' }
//   return words.toLowerCase().split(punct_re).join('_')
//     .replace(/_$$/gm, '') + padding
// }

// function previewImage(file, preview_container) {
//     return false
//     var reader = new FileReader();
//     reader.onload = function (e) {
//         preview_container.attr("src", e.target.result);
//     }
//     reader.readAsDataURL(file);
//
//     // var data = new FormData();
//     // data.append("file-0", file);
//     // $.ajax({method: "POST",
//     //         url: "/editor/media",
//     //         contentType: "multipart/form-data",
//     //         data: data
//     //        }).done(function(msg) {
//     //                    console.log("repsonse");
//     //                    console.log(msg);
//     //                    var body = msg["content"];
//     //                    preview_container.html(body);
//     //                });
// }

// function previewResource (url, handler) {
//   if (url == '') {
//     // preview_container.innerHTML = "";
//     return
//   }
//
//   const xhr = new XMLHttpRequest()
//   xhr.open('GET', '/editor/preview/microformats?url=' +
//                     encodeURIComponent(url))
//   xhr.onload = function () {
//     if (xhr.status === 200) {
//       const response = JSON.parse(xhr.responseText)
//       // var entry = response["entry"];
//       // XXX console.log(response);
//       handler(response)
//       // var body = "";
//       // if ("profile" in response) {
//       //     // asd
//       // } else if (entry) {
//       //     if ("name" in entry)
//       //         body = "unknown type";
//       //     else if ("photo" in entry)
//       //         body = "Photo:<br><img src=" + entry["photo"] + ">";
//       //     else
//       //         body = "Note:<br>" + entry["content"];
//       // }
//       // preview_container.innerHTML = body;
//     } else { console.log('request failed: ' + xhr.status) }
//   }
//   xhr.send()
// }

// $(function() {
//     var current_body = "";
//     function setTimer() {
//         setTimeout(function() {
//             var new_body = $("#body").val();
//             if (new_body != current_body) {
//                 $.ajax({method: "POST",
//                          url: "/content/editor/preview",
//                          data: {content: new_body}
//                         }).done(function(msg) {
//                                     $("#body_readability").html(msg["readability"]);
//                                     $("#body_preview").html(msg["content"]);
//                                 });
//                 current_body = new_body;
//             }
//             setTimer();
//         }, 5000);
//     };
//     setTimer();
// });

// const socket_origin = (window.location.protocol == 'http:' ? 'ws' : 'wss') +
//                       '://' + window.location.host + '/'

interface Configuration {
  q?: string
  'media-endpoint'?: string
  'syndicate-to'?: string
  'visibility'?: string
}

class MicropubClient {
  endpoint: string
  token: string
  headers: any
  config: Configuration

  constructor (endpoint, token) {
    this.endpoint = endpoint
    this.token = token
    this.headers = {
      accept: 'application/json'
    }
    if (typeof token !== 'undefined') {
      this.headers.authorization = `Bearer ${token}`
    }

    this.getConfig = this.getConfig.bind(this)

    this.create = this.create.bind(this)
    this.read = this.read.bind(this)
    this.update = this.update.bind(this)
    this.delete = this.delete.bind(this)

    this.query = this.query.bind(this)
    this.upload = this.upload.bind(this)
  }

  getConfig () {
    return fetch(this.endpoint + '?q=config', {
      headers: this.headers
    }).then(response => {
      if (response.status === 200 || response.status === 201) {
        return response.json().then(data => {
          return data
        })
      }
    })
  }

  getCategories () {
    return fetch(this.endpoint + '?q=category', {
      headers: this.headers
    }).then(response => {
      if (response.status === 200 || response.status === 201) {
        return response.json().then(data => {
          return data
        })
      }
    })
  }

  create (type: string, payload: object, visibility?: string) {
    const headers = this.headers
    headers['content-type'] = 'application/json'
    if (typeof visibility === 'undefined') {
      visibility = 'private'
    }
    return fetch(this.endpoint, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({
        type: [`h-${type}`],
        properties: payload,
        visibility: visibility
      })
    }).then(response => {
      if (response.status === 200 || response.status === 201) {
        return response.headers.get('location') // permalink
      }
    })
  }

  read (url) {
    const headers = this.headers
    headers['content-type'] = 'application/json'
    return fetch(this.endpoint, {
      method: 'GET',
      headers: headers
    }).then(response => {
      if (response.status === 200 || response.status === 201) {
        return response.json().then(data => {
          return data
        })
      }
    })
  }

  update (url, operation, property, values) {
    const payload = { action: 'update', url: url }
    payload[operation] = {}
    payload[operation][property] = values
    return fetch(this.endpoint, {
      method: 'POST',
      headers: {
        accept: 'application/json',
        authorization: `Bearer ${this.token}`,
        'content-type': 'application/json'
      },
      body: JSON.stringify(payload)
    }).then(response => {
      if (response.status === 200 || response.status === 201) {
        console.log('UPDATED!')
      }
    })
  }

  delete (url) {
  }

  query (q, args) {
    return fetch(this.endpoint + `?q=${q}&search=${args}`, {
      headers: this.headers
    }).then(response => {
      if (response.status === 200 || response.status === 201) {
        return response.json().then(data => {
          return data
        })
      }
    })
  }

  upload () {
  }
}

class MicrosubClient {
  endpoint: string
  token: string

  constructor (endpoint, token) {
    this.endpoint = endpoint
    this.token = token
    // this.followers = this.followers.bind(this)
    // this.follow = this.follow.bind(this)
  }

//   followers (...channel) {
//     let requestUrl = this.endpoint + 'action=follow'
//     if (channel.length) {
//       requestUrl += `&channel=${channel[0]}`
//     }
//     return fetch(requestUrl).then(response => {
//       if (response.status === 200 || response.status === 201) {
//         return response.json().then(data => {
//           return data
//         })
//       }
//     })
//   }
//
//   follow (url, ...channel) {
//     let body = `action=follow&url=${url}`
//     if (channel.length) {
//       body += `&channel=${channel[0]}`
//     }
//     fetch(this.endpoint, {
//       method: 'POST',
//       headers: { 'content-type': 'application/x-www-form-urlencoded' },
//       body: body
//     }).then(response => {
//       if (response.status === 200 || response.status === 201) {
//         return response.json().then(data => {
//           return data
//         })
//       }
//     })
//   }
//
//   search (query, ...channel) {
//     let body = `action=search&query=${query}`
//     if (channel.length) {
//       body += `&channel=${channel[0]}`
//     }
//     return fetch(this.endpoint, {
//       method: 'POST',
//       headers: { 'content-type': 'application/x-www-form-urlencoded' },
//       body: body
//     }).then(response => {
//       if (response.status === 200 || response.status === 201) {
//         return response.json().then(data => {
//           return data
//         })
//       }
//     })
//   }
}

/**
 * JavaScript Client Detection
 * (C) viazenetti GmbH (Christian Ludwig)
 */
const getBrowser = () => {
  const unknown = '-'

  // screen
  let screenSize = ''
  if (screen.width) {
    const width = (screen.width) ? screen.width : ''
    const height = (screen.height) ? screen.height : ''
    screenSize += '' + width + ' x ' + height
  }

  // browser
  const nVer = navigator.appVersion
  const nAgt = navigator.userAgent
  let browser = navigator.appName
  let version = '' + parseFloat(navigator.appVersion)
  let majorVersion = parseInt(navigator.appVersion, 10)
  let nameOffset, verOffset, ix

  // Opera
  if ((verOffset = nAgt.indexOf('Opera')) != -1) {
    browser = 'Opera'
    version = nAgt.substring(verOffset + 6)
    if ((verOffset = nAgt.indexOf('Version')) != -1) {
      version = nAgt.substring(verOffset + 8)
    }
  }
  // Opera Next
  if ((verOffset = nAgt.indexOf('OPR')) != -1) {
    browser = 'Opera'
    version = nAgt.substring(verOffset + 4)
  }
  // Legacy Edge
  else if ((verOffset = nAgt.indexOf('Edge')) != -1) {
    browser = 'Microsoft Legacy Edge'
    version = nAgt.substring(verOffset + 5)
  }
  // Edge (Chromium)
  else if ((verOffset = nAgt.indexOf('Edg')) != -1) {
    browser = 'Microsoft Edge'
    version = nAgt.substring(verOffset + 4)
  }
  // MSIE
  else if ((verOffset = nAgt.indexOf('MSIE')) != -1) {
    browser = 'Microsoft Internet Explorer'
    version = nAgt.substring(verOffset + 5)
  }
  // Chrome
  else if ((verOffset = nAgt.indexOf('Chrome')) != -1) {
    browser = 'Chrome'
    version = nAgt.substring(verOffset + 7)
  }
  // Safari
  else if ((verOffset = nAgt.indexOf('Safari')) != -1) {
    browser = 'Safari'
    version = nAgt.substring(verOffset + 7)
    if ((verOffset = nAgt.indexOf('Version')) != -1) {
      version = nAgt.substring(verOffset + 8)
    }
  }
  // Firefox
  else if ((verOffset = nAgt.indexOf('Firefox')) != -1) {
    browser = 'Firefox'
    version = nAgt.substring(verOffset + 8)
  }
  // MSIE 11+
  else if (nAgt.indexOf('Trident/') != -1) {
    browser = 'Microsoft Internet Explorer'
    version = nAgt.substring(nAgt.indexOf('rv:') + 3)
  }
  // Other browsers
  else if ((nameOffset = nAgt.lastIndexOf(' ') + 1) < (verOffset = nAgt.lastIndexOf('/'))) {
    browser = nAgt.substring(nameOffset, verOffset)
    version = nAgt.substring(verOffset + 1)
    if (browser.toLowerCase() == browser.toUpperCase()) {
      browser = navigator.appName
    }
  }
  // trim the version string
  if ((ix = version.indexOf(';')) != -1) version = version.substring(0, ix)
  if ((ix = version.indexOf(' ')) != -1) version = version.substring(0, ix)
  if ((ix = version.indexOf(')')) != -1) version = version.substring(0, ix)

  majorVersion = parseInt('' + version, 10)
  if (isNaN(majorVersion)) {
    version = '' + parseFloat(navigator.appVersion)
    majorVersion = parseInt(navigator.appVersion, 10)
  }

  // mobile version
  const mobile = /Mobile|mini|Fennec|Android|iP(ad|od|hone)/.test(nVer)

  // cookie
  let cookieEnabled = !!(navigator.cookieEnabled)

  if (typeof navigator.cookieEnabled === 'undefined' && !cookieEnabled) {
    document.cookie = 'testcookie'
    cookieEnabled = (document.cookie.indexOf('testcookie') != -1)
  }

  // system
  let os = unknown
  const clientStrings = [
    { s: 'Windows 10', r: /(Windows 10.0|Windows NT 10.0)/ },
    { s: 'Windows 8.1', r: /(Windows 8.1|Windows NT 6.3)/ },
    { s: 'Windows 8', r: /(Windows 8|Windows NT 6.2)/ },
    { s: 'Windows 7', r: /(Windows 7|Windows NT 6.1)/ },
    { s: 'Windows Vista', r: /Windows NT 6.0/ },
    { s: 'Windows Server 2003', r: /Windows NT 5.2/ },
    { s: 'Windows XP', r: /(Windows NT 5.1|Windows XP)/ },
    { s: 'Windows 2000', r: /(Windows NT 5.0|Windows 2000)/ },
    { s: 'Windows ME', r: /(Win 9x 4.90|Windows ME)/ },
    { s: 'Windows 98', r: /(Windows 98|Win98)/ },
    { s: 'Windows 95', r: /(Windows 95|Win95|Windows_95)/ },
    { s: 'Windows NT 4.0', r: /(Windows NT 4.0|WinNT4.0|WinNT|Windows NT)/ },
    { s: 'Windows CE', r: /Windows CE/ },
    { s: 'Windows 3.11', r: /Win16/ },
    { s: 'Android', r: /Android/ },
    { s: 'Open BSD', r: /OpenBSD/ },
    { s: 'Sun OS', r: /SunOS/ },
    { s: 'Chrome OS', r: /CrOS/ },
    { s: 'Linux', r: /(Linux|X11(?!.*CrOS))/ },
    { s: 'iOS', r: /(iPhone|iPad|iPod)/ },
    { s: 'Mac OS X', r: /Mac OS X/ },
    { s: 'Mac OS', r: /(Mac OS|MacPPC|MacIntel|Mac_PowerPC|Macintosh)/ },
    { s: 'QNX', r: /QNX/ },
    { s: 'UNIX', r: /UNIX/ },
    { s: 'BeOS', r: /BeOS/ },
    { s: 'OS/2', r: /OS\/2/ },
    { s: 'Search Bot', r: /(nuhk|Googlebot|Yammybot|Openbot|Slurp|MSNBot|Ask Jeeves\/Teoma|ia_archiver)/ }
  ]
  for (const id in clientStrings) {
    const cs = clientStrings[id]
    if (cs.r.test(nAgt)) {
      os = cs.s
      break
    }
  }

  let osVersion = unknown

  if (/Windows/.test(os)) {
    osVersion = /Windows (.*)/.exec(os)[1]
    os = 'Windows'
  }

  switch (os) {
    case 'Mac OS':
    case 'Mac OS X':
    case 'Android':
      osVersion = /(?:Android|Mac OS|Mac OS X|MacPPC|MacIntel|Mac_PowerPC|Macintosh) ([\.\_\d]+)/.exec(nAgt)[1]
      break

      // TODO case 'iOS':
      // TODO   osVersion = /OS (\d+)_(\d+)_?(\d+)?/.exec(nVer)
      // TODO   osVersion = osVersion[1] + '.' + osVersion[2] + '.' + (osVersion[3] | 0)
      // TODO   break
  }

  // flash (you'll need to include swfobject)
  /* script src="//ajax.googleapis.com/ajax/libs/swfobject/2.2/swfobject.js" */
  // TODO var flashVersion = 'no check'
  // TODO if (typeof swfobject !== 'undefined') {
  // TODO   const fv = swfobject.getFlashPlayerVersion()
  // TODO   if (fv.major > 0) {
  // TODO     flashVersion = fv.major + '.' + fv.minor + ' r' + fv.release
  // TODO   } else {
  // TODO     flashVersion = unknown
  // TODO   }
  // TODO }

  return {
    screen: screenSize,
    browser: browser,
    browserVersion: version,
    browserMajorVersion: majorVersion,
    mobile: mobile,
    os: os,
    osVersion: osVersion,
    cookies: cookieEnabled
    // TODO flashVersion: flashVersion
  }
}

// TODO alert(
// TODO   'OS: ' + jscd.os + ' ' + jscd.osVersion + '\n' +
// TODO     'Browser: ' + jscd.browser + ' ' + jscd.browserMajorVersion +
// TODO       ' (' + jscd.browserVersion + ')\n' +
// TODO     'Mobile: ' + jscd.mobile + '\n' +
// TODO     'Flash: ' + jscd.flashVersion + '\n' +
// TODO     'Cookies: ' + jscd.cookies + '\n' +
// TODO     'Screen Size: ' + jscd.screen + '\n\n' +
// TODO     'Full User Agent: ' + navigator.userAgent
// TODO )

module.exports = {
  MicropubClient: MicropubClient,
  MicrosubClient: MicrosubClient,
  getBrowser: getBrowser
}
