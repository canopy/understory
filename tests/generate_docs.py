import json
import pathlib

from understory import src, web

docs_dir = pathlib.Path("docs")
tests_dir = pathlib.Path("tests")


def main(characters, scenes):
    toc = ""
    story = ""
    for index, (who, caption, description, slug) in enumerate(scenes):
        if caption:
            toc += f"<li><a href=#{slug}>{caption}</a></li>"
        story += f"<section id={slug}>"
        if caption:
            story += f"<h3>{caption}</h3>"
        if description:
            story += f"<p>{description}</p>"
        story += f"<div class=storyboard>"
        for character in sorted(characters):
            if character in who:
                url = (
                    f"https://media.githubusercontent.com/media/canopy/understory/"
                    f"main/docs/{index:03}_{character}_{slug}.png"
                )
                story += f"<div class=character-name>{character}</div>"
                story += f"<a href={url}><img src={url}></a>"
            else:
                story += "<div class=filler></div>"
        story += f"</div></section>"
    now = web.utcnow()
    api = [
        (name, src.get_doc(mod))
        for name, mod in src.get_api("understory")["members"][0]
    ]
    with pathlib.Path("README.md").open() as fp:
        readme = "\n".join(fp.read().splitlines()[12:])
    with (docs_dir / "index.html").open("w") as output_fp:
        with (tests_dir / "docs_template.html").open() as template_fp:
            output_fp.write(
                str(web.template(template_fp)(now, characters, toc, story, api, readme))
            )


if __name__ == "__main__":
    with (tests_dir / "results.json").open() as fp:
        results = json.load(fp)
    main(results["characters"], results["scenes"])
