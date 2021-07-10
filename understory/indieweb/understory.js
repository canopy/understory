var understory;
/******/ (() => { // webpackBootstrap
/******/ 	var __webpack_modules__ = ([
/* 0 */
/***/ ((module) => {

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
class MicropubClient {
    constructor(endpoint, token) {
        this.endpoint = endpoint;
        this.token = token;
        this.headers = {
            accept: 'application/json'
        };
        if (typeof token !== 'undefined') {
            this.headers.authorization = `Bearer ${token}`;
        }
        this.getConfig = this.getConfig.bind(this);
        this.create = this.create.bind(this);
        this.read = this.read.bind(this);
        this.update = this.update.bind(this);
        this.delete = this.delete.bind(this);
        this.query = this.query.bind(this);
        this.upload = this.upload.bind(this);
    }
    getConfig() {
        return fetch(this.endpoint + '?q=config', {
            headers: this.headers
        }).then(response => {
            if (response.status === 200 || response.status === 201) {
                return response.json().then(data => {
                    return data;
                });
            }
        });
    }
    create(type, payload, visibility) {
        const headers = this.headers;
        headers['content-type'] = 'application/json';
        if (typeof visibility === 'undefined') {
            visibility = 'private';
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
                const permalink = response.headers.get('location');
                // if (permalink.startsWith('/')) {
                //   permalink = `https://${me}${permalink}`
                // }
                return permalink;
            }
        });
    }
    read(url) {
        const headers = this.headers;
        headers['content-type'] = 'application/json';
        return fetch(this.endpoint, {
            method: 'GET',
            headers: headers
        }).then(response => {
            if (response.status === 200 || response.status === 201) {
                return response.json().then(data => {
                    return data;
                });
            }
        });
    }
    update(url, payload) {
        payload.action = 'update';
        payload.url = url;
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
                console.log('UPDATED!');
            }
        });
    }
    delete(url) {
    }
    query(q, args) {
        return fetch(this.endpoint + `?q=${q}&search=${args}`, {
            headers: this.headers
        }).then(response => {
            if (response.status === 200 || response.status === 201) {
                return response.json().then(data => {
                    return data;
                });
            }
        });
    }
    upload() {
    }
}
class MicrosubClient {
    constructor(endpoint, token) {
        this.endpoint = endpoint;
        this.token = token;
        // this.followers = this.followers.bind(this)
        // this.follow = this.follow.bind(this)
    }
}
module.exports = {
    MicropubClient: MicropubClient,
    MicrosubClient: MicrosubClient
};


/***/ })
/******/ 	]);
/************************************************************************/
/******/ 	// The module cache
/******/ 	var __webpack_module_cache__ = {};
/******/ 	
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/ 		// Check if module is in cache
/******/ 		var cachedModule = __webpack_module_cache__[moduleId];
/******/ 		if (cachedModule !== undefined) {
/******/ 			return cachedModule.exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = __webpack_module_cache__[moduleId] = {
/******/ 			// no module.id needed
/******/ 			// no module.loaded needed
/******/ 			exports: {}
/******/ 		};
/******/ 	
/******/ 		// Execute the module function
/******/ 		__webpack_modules__[moduleId](module, module.exports, __webpack_require__);
/******/ 	
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/ 	
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module is referenced by other modules so it can't be inlined
/******/ 	var __webpack_exports__ = __webpack_require__(0);
/******/ 	understory = __webpack_exports__;
/******/ 	
/******/ })()
;