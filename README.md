# understory
Tools to power your personal website

## An IndieWeb-compatible personal website packaged and deployed

Install [Poetry](https://python-poetry.org).

Clone your empty website repository and descend into it. *If you
use a **private** GitHub repository your changes will be deployed through
GitHub. If you use a **public** repository your changes will be deployed
through PyPI.*

Initialize your project and add understory as a dependency.

    poetry init
    poetry add understory

Create a file `site.py`:

    from understory import indieweb
    
    app = indieweb.site()

Add your site's app as an entry point in your `pyproject.toml`:

    poetry run web install site:app AliceAnderson

Serve your website locally in development mode:

    poetry run web serve AliceAnderson

Open <a href=http://localhost:9000>localhost:9000</a> in your browser.

*Develop.* For example, add a custom route:

    import random
    
    @app.route(r"hello")
    class SayHello:
        return random.choice(["How you doin'?", "What's happening?", "What's up?"])

To publish:

    poetry run pkg publish patch

To deploy:

    poetry run web deploy

    ██╗   ██╗███╗   ██╗██████╗ ███████╗██████╗ ███████╗████████╗ ██████╗ ██████╗ ██╗   ██╗
    ██║   ██║████╗  ██║██╔══██╗██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗╚██╗ ██╔╝
    ██║   ██║██╔██╗ ██║██║  ██║█████╗  ██████╔╝███████╗   ██║   ██║   ██║██████╔╝ ╚████╔╝
    ██║   ██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗╚════██║   ██║   ██║   ██║██╔══██╗  ╚██╔╝
    ╚██████╔╝██║ ╚████║██████╔╝███████╗██║  ██║███████║   ██║   ╚██████╔╝██║  ██║   ██║
     ╚═════╝ ╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝
