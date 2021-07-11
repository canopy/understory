from understory import mm, term

main = term.application("mm", mm.__doc__)


@main.register()
class Main:
    def setup(self, add_arg):
        add_arg("args", nargs="*", help="argument(s) passed to template")
        add_arg(
            "-w",
            "--wrap",
            nargs="+",
            dest="wrappers",
            type=open,
            help="wrap in given template(s)",
        )

    def run(self, args, stdin):
        document = mm.Template(stdin)(*args.args)
        for wrapper in args.wrappers:
            document = mm.Template(wrapper)(document)
        print(document)
