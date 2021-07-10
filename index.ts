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
        const permalink = response.headers.get('location')
        // if (permalink.startsWith('/')) {
        //   permalink = `https://${me}${permalink}`
        // }
        return permalink
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

  update (url, payload) {
    payload.action = 'update'
    payload.url = url
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

module.exports = {
  MicropubClient: MicropubClient,
  MicrosubClient: MicrosubClient
}
