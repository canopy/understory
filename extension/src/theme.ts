const browser = require('webextension-polyfill')

async function updateTheme () {
  if (typeof (browser.theme) === 'undefined') { return }
  await browser.theme.getCurrent().then(theme => {
    console.log(theme)
    if (theme && theme.colors) {
      // const colors = [`--color-background: ${theme.colors.popup}`,
      //                 `--color-primary: ${theme.colors.popup_text}`]
      // document.body.setAttribute('style', colors.join(''))
      const style = `background-color: ${theme.colors.popup}
                     color: ${theme.colors.popup_text}`
      document.body.setAttribute('style', style)
    }
  })
}

updateTheme()
