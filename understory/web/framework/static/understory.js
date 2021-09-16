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
    getCategories() {
        return fetch(this.endpoint + '?q=category', {
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
                return response.headers.get('location'); // permalink
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
    update(url, operation, property, values) {
        const payload = { action: 'update', url: url };
        payload[operation] = {};
        payload[operation][property] = values;
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
/**
 * JavaScript Client Detection
 * (C) viazenetti GmbH (Christian Ludwig)
 */
const getBrowser = () => {
    const unknown = '-';
    // screen
    let screenSize = '';
    if (screen.width) {
        const width = (screen.width) ? screen.width : '';
        const height = (screen.height) ? screen.height : '';
        screenSize += '' + width + ' x ' + height;
    }
    // browser
    const nVer = navigator.appVersion;
    const nAgt = navigator.userAgent;
    let browser = navigator.appName;
    let version = '' + parseFloat(navigator.appVersion);
    let majorVersion = parseInt(navigator.appVersion, 10);
    let nameOffset, verOffset, ix;
    // Opera
    if ((verOffset = nAgt.indexOf('Opera')) != -1) {
        browser = 'Opera';
        version = nAgt.substring(verOffset + 6);
        if ((verOffset = nAgt.indexOf('Version')) != -1) {
            version = nAgt.substring(verOffset + 8);
        }
    }
    // Opera Next
    if ((verOffset = nAgt.indexOf('OPR')) != -1) {
        browser = 'Opera';
        version = nAgt.substring(verOffset + 4);
    }
    // Legacy Edge
    else if ((verOffset = nAgt.indexOf('Edge')) != -1) {
        browser = 'Microsoft Legacy Edge';
        version = nAgt.substring(verOffset + 5);
    }
    // Edge (Chromium)
    else if ((verOffset = nAgt.indexOf('Edg')) != -1) {
        browser = 'Microsoft Edge';
        version = nAgt.substring(verOffset + 4);
    }
    // MSIE
    else if ((verOffset = nAgt.indexOf('MSIE')) != -1) {
        browser = 'Microsoft Internet Explorer';
        version = nAgt.substring(verOffset + 5);
    }
    // Chrome
    else if ((verOffset = nAgt.indexOf('Chrome')) != -1) {
        browser = 'Chrome';
        version = nAgt.substring(verOffset + 7);
    }
    // Safari
    else if ((verOffset = nAgt.indexOf('Safari')) != -1) {
        browser = 'Safari';
        version = nAgt.substring(verOffset + 7);
        if ((verOffset = nAgt.indexOf('Version')) != -1) {
            version = nAgt.substring(verOffset + 8);
        }
    }
    // Firefox
    else if ((verOffset = nAgt.indexOf('Firefox')) != -1) {
        browser = 'Firefox';
        version = nAgt.substring(verOffset + 8);
    }
    // MSIE 11+
    else if (nAgt.indexOf('Trident/') != -1) {
        browser = 'Microsoft Internet Explorer';
        version = nAgt.substring(nAgt.indexOf('rv:') + 3);
    }
    // Other browsers
    else if ((nameOffset = nAgt.lastIndexOf(' ') + 1) < (verOffset = nAgt.lastIndexOf('/'))) {
        browser = nAgt.substring(nameOffset, verOffset);
        version = nAgt.substring(verOffset + 1);
        if (browser.toLowerCase() == browser.toUpperCase()) {
            browser = navigator.appName;
        }
    }
    // trim the version string
    if ((ix = version.indexOf(';')) != -1)
        version = version.substring(0, ix);
    if ((ix = version.indexOf(' ')) != -1)
        version = version.substring(0, ix);
    if ((ix = version.indexOf(')')) != -1)
        version = version.substring(0, ix);
    majorVersion = parseInt('' + version, 10);
    if (isNaN(majorVersion)) {
        version = '' + parseFloat(navigator.appVersion);
        majorVersion = parseInt(navigator.appVersion, 10);
    }
    // mobile version
    const mobile = /Mobile|mini|Fennec|Android|iP(ad|od|hone)/.test(nVer);
    // cookie
    let cookieEnabled = !!(navigator.cookieEnabled);
    if (typeof navigator.cookieEnabled === 'undefined' && !cookieEnabled) {
        document.cookie = 'testcookie';
        cookieEnabled = (document.cookie.indexOf('testcookie') != -1);
    }
    // system
    let os = unknown;
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
    ];
    for (const id in clientStrings) {
        const cs = clientStrings[id];
        if (cs.r.test(nAgt)) {
            os = cs.s;
            break;
        }
    }
    let osVersion = unknown;
    if (/Windows/.test(os)) {
        osVersion = /Windows (.*)/.exec(os)[1];
        os = 'Windows';
    }
    switch (os) {
        case 'Mac OS':
        case 'Mac OS X':
        case 'Android':
            osVersion = /(?:Android|Mac OS|Mac OS X|MacPPC|MacIntel|Mac_PowerPC|Macintosh) ([\.\_\d]+)/.exec(nAgt)[1];
            break;
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
    };
};
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