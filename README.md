    ██╗   ██╗███╗   ██╗██████╗ ███████╗██████╗ ███████╗████████╗ ██████╗ ██████╗ ██╗   ██╗
    ██║   ██║████╗  ██║██╔══██╗██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗╚██╗ ██╔╝
    ██║   ██║██╔██╗ ██║██║  ██║█████╗  ██████╔╝███████╗   ██║   ██║   ██║██████╔╝ ╚████╔╝ 
    ██║   ██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗╚════██║   ██║   ██║   ██║██╔══██╗  ╚██╔╝  
    ╚██████╔╝██║ ╚████║██████╔╝███████╗██║  ██║███████║   ██║   ╚██████╔╝██║  ██║   ██║   
     ╚═════╝ ╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝   

The tools that power the canopy..

## An IndieWeb-compatible personal website packaged and deployed

Install [Python Poetry][0].

Clone your empty website repository and descend into it.

NOTE: If you use a private GitHub repository your changes will be
deployed through GitHub. If you use a public repository your changes
will be deployed through PyPI.

    poetry init
    poetry add understory

Create a file `site.py`:

    from understory import indieweb

    app = indieweb.site("Alice")

Initialize your project, add understory as a dependency, install your site's
entry point in your `project.toml` and serve your website locally in
development mode:

    poetry run web install site:app Alice
    poetry run web serve Alice

Open <a href=http://localhost:9000>localhost:9000</a> in your browser.

*Develop.*

To deploy:

    poetry run pkg publish patch
    poetry run web deploy

[0]: https://python-poetry.org
