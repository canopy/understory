"""
tools for NewBase60, NewBase64 and NewDateTime numbering systems

NewBase60
---------

NewBase60 is a base 60 (sexagesimal) numbering system that uses only
ASCII numbers and letters that are print, prose and code safe. Lowercase
l and uppercase I are aliased to the number 1. Capital O is aliased to
the number 0.

    0123456789ABCDEFGHJKLMNPQRSTUVWXYZ_abcdefghijkmnopqrstuvwxyz

NewBase60 encoded numbers sort properly in the typical case.

NewBase64
---------

NewBase64 is a base 64 numbering system that extends NewBase60 for use
in shortly encoding square grids. The four characters added are -, +, *
and $.

        0 1 2 3 4 5 6 7
       ----------------
     0| 0 1 2 3 4 5 6 7
     8| 8 9 A B C D E F
    16| G H J K L M N P
    24| Q R S T U V W X
    32| Y Z _ a b c d e
    40| f g h i j k m n
    48| o p q r s t u v
    56| w x y z - + * $

latitude: -90 to 90 (pole to pole)
longitude: -180 to 180 (meridian back to meridian)

Earth is split into 32 quadrants:

    0 1 2 3  4 5 6 7
    8 9 A B  C D E F
    G H J K  L M N P
    Q R S T  U V W X

Each quadrant can be further scoped by 1/64ths. e.g. the 0th quadrant:

    0 1 2 3 4 5 6 7
    8 9 A B C D E F
    G H J K L M N P
    Q R S T U V W X
    Y Z _ a b c d e
    f g h i j k m n
    o p q r s t u v
    w x y z - + * $

The initial quadrant is divided into 64 subquadrants with dimensions
5.625 degrees square. Second and third subquadrants are 0.703125 and
0.087890625 degrees square respectively.

1 degree latitude = between 110.567 (at equator) and 111.699 km (at poles)
1 degree longitude = between 111.321 (at equator) and 0 (at poles)

    precision  scope
            1  4.950 Mm

            2  618.75 km
            3  77.34375 km
            4  9.66796875 km
            5  1.20849609375 km

            6  151.06201171 m
            7  18.8827514648 m
            8  2.36034393311 m

            9  295.04299163 mm
           10  36.88037395 mm
           11  4.61004674 mm

           12  576.25584 μm
           13  72.0319803804 μm
           14  9.00399754755 μm
           15  1.12549969344 μm

NewDateTime
-----------

Four sundays (0th day of the week) mark solar equinoxes and solstices.
Monday through Saturday are days 1-6. Friday and Saturday are weekends
resulting in a "4 day work week".

5 days * 52 weeks = 260 work days in existing calendar
5 days * 50 weeks = 250 work days accounting for two weeks vacation
4 days * 60 weeks = 240 work days in NewDateTime

Four 90 day, 15 week quarters. Each quarter is split into three months.

52 days * 4 quarters = 184 work days accounting for mid-quarter vacation

        Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec  Jan  Feb  Mar

       0123456789ABCDEFGHJKLMNPQRSTUVWXYZ_abcdefghijkmnopqrstuvwxyz
    Su @--------------@--------------@--------------@-------------- 0
    Mo X              X              X              X               1
    Tu X              X              X              X               2
    We X    X    X    X    X    X    X    X    X    X    X    X     3
    Th X    X    X    X    X    X    X    X    X    X    X    X     4
    Fr XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 5
    Sa XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 6

    @ - sunday
    X - non-work

      0  year 1

    000  new epoch

    000  Sunday

    000  northern tilt - new first sunday (old Mar 20, equinox)
    0F0  northern sun - new second sunday (old Jun 21, northern solstice)
    0W0  southern tilt - new third sunday (old Sep 23, equinox)
    0k0  southern sun - new fourth sunday (old Dec 21, southern solstice)

    001  Monday
    002  Tuesday
    003  Wednesday
    004  Thursday
    005  Friday
    006  Saturday

    0z6  last day of first year

    100  second new new year

      1  year 2
     1R  26th week of the 2nd year
    1R0  Monday of the 26th week of the 2nd year

Based upon @[Tantek Çelik][1]'s [NewBase60][2], [NewBase64][3] and
[NewCalendar][4] specifications.

[1]: https://tantek.com
[2]: https://tantek.pbworks.com/NewBase60
[3]: https://tantek.pbworks.com/NewBase64
[4]: https://tantek.pbworks.com/NewCalendar

"""

import Crypto.Random
import pendulum

nb60 = "0123456789ABCDEFGHJKLMNPQRSTUVWXYZ_abcdefghijkmnopqrstuvwxyz"
nb60_re = "[0-9A-HJ-NP-Z_a-km-z]"
_nb60map = dict(zip(nb60, range(len(nb60))))
_nb60map["l"] = 1  # typo l to 1
_nb60map["I"] = 1  # typo I to 1
_nb60map["O"] = 0  # typo O to 0


def nbencode(number, min_length=1):
    """
    return the NewBase60 string equivalent of decimal integer `i`

    `min_length`: final size of string, zero padding on the left if needed

        >>> nbencode(2011)
        'ZX'
        >>> nbencode(2011, min_length=5)
        '000ZX'
        >>> nbencode(-2011)
        '-ZX'

    """
    string = ""
    try:
        number = int(number)
    except ValueError:
        raise ValueError("NewBase60 encoding requires a decimal integer")
    sign = ""
    if number < 0:
        sign = "-"
        number = abs(number)
    while number > 0:
        number, i = divmod(number, 60)
        string = nb60[i] + string
    length = len(string)
    min_length = int(min_length)
    if length < min_length:
        string = "0" * (min_length - length) + string
    return sign + string


def nbdecode(string):
    """
    return the decimal integer equivalent of NewBase60 string `s`

        >>> nbdecode('ZX')
        2011
        >>> nbdecode('000ZX')
        2011
        >>> nbdecode('-ZX')
        -2011

    """
    string = str(string)
    sign = 1
    if string.startswith("-"):
        sign = -1
        string = string[1:]
    number = 0
    for character in string:
        number = number * 60 + _nb60map.get(character, 0)
    return number * sign


def nbrandom(length):
    """
    return a random NewBase60 string `length` digits long

        >>> nbrandom(3)  # doctest: +SKIP
        'Do_'
        >>> nbrandom(6)  # doctest: +SKIP
        'j9cQ4m'

    """
    start = nbdecode("1" + "0" * (length - 1))
    end = nbdecode("z" * length)
    return nbencode(Crypto.Random.random.randint(start, end))


def nbrange(start, stop=None, step=1):
    """
    return a generator that yields NewBase60 strings like the builtin `range`

    Arguments will be coerced to their NewBase60 string representations if
    not provided as such.

        >>> list(nbrange(5))
        ['0', '1', '2', '3', '4']
        >>> list(nbrange('ex', 'f3'))
        ['ex', 'ey', 'ez', 'f0', 'f1', 'f2']

    """
    if stop is None:
        stop = start
        start = "0"
    for i in range(nbdecode(start), nbdecode(stop), step):
        yield nbencode(i)


def ncencode(dt):
    """ """
    ddd = int(dt.format("DDD"))
    bimnumber = int((ddd - 1) / 61) + 1
    bim = hex(bimnumber + 9)[2].upper()
    dayinbim = int((ddd - 1) % 61) + 1
    seconds = round((dt.hour * 3600) + (dt.minute * 60) + dt.second) / 24
    return nbencode(dt.year), bim, nbencode(dayinbim), nbencode(seconds)


def ncdecode(year, bim, dayinbim, seconds):
    """ """
    bimnumber = int("0x" + bim, 16) - 9
    ddd = 61 * (bimnumber - 1) + dayinbim
    return pendulum.parse("{}-{:03}".format(year, ddd))
