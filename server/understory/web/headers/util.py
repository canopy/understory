"""

"""


class Header:

    """"""

    def __init__(self, header):
        self.header = str(header).strip()
        self.parse()

    def parse(self):
        pass

    def __eq__(self, comparison):
        if isinstance(comparison, str):
            return self.header == comparison
        return False

    def __ne__(self, comparison):
        return not self == comparison

    def __contains__(self, what):
        return what in str(self.header)

    def __str__(self):
        return str(self.header)

    def __unicode__(self):
        return str(self.header)

    def __repr__(self):
        return str(self.header)
