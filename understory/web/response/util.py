"""

"""

import regex as re


class Status(Exception):

    """ """

    def __init__(self, body):
        super(Status, self).__init__(body)
        self.body = body

    @property
    def code(self):
        return int(self.__doc__.split()[0].strip("."))

    @property
    def reason(self):
        if self.code == 200:
            return "OK"
        return re.sub("([A-Z])", r" \1", self.__class__.__name__).lstrip()

    def __str__(self):
        return "{} {}".format(self.code, self.reason)
