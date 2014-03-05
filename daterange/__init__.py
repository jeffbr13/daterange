# -*- coding: utf-8 -*-

"""
Example Usage
=============

>>> import datetime
>>> start = datetime.date(2009, 6, 21)

>>> g1 = daterange(start)
>>> next(g1)
datetime.date(2009, 6, 21)
>>> next(g1)
datetime.date(2009, 6, 22)
>>> next(g1)
datetime.date(2009, 6, 23)
>>> next(g1)
datetime.date(2009, 6, 24)
>>> next(g1)
datetime.date(2009, 6, 25)
>>> next(g1)
datetime.date(2009, 6, 26)

>>> g2 = daterange(start, to=datetime.date(2009, 6, 25))
>>> next(g2)
datetime.date(2009, 6, 21)
>>> next(g2)
datetime.date(2009, 6, 22)
>>> next(g2)
datetime.date(2009, 6, 23)
>>> next(g2)
datetime.date(2009, 6, 24)
>>> next(g2)
datetime.date(2009, 6, 25)
>>> next(g2)
Traceback (most recent call last):
...
StopIteration

>>> g3 = daterange(start, step='2 days')
>>> next(g3)
datetime.date(2009, 6, 21)
>>> next(g3)
datetime.date(2009, 6, 23)
>>> next(g3)
datetime.date(2009, 6, 25)
>>> next(g3)
datetime.date(2009, 6, 27)

>>> g4 = daterange(start, to=datetime.date(2009, 6, 25), step='2 days')
>>> next(g4)
datetime.date(2009, 6, 21)
>>> next(g4)
datetime.date(2009, 6, 23)
>>> next(g4)
datetime.date(2009, 6, 25)
>>> next(g4)
Traceback (most recent call last):
...
StopIteration

"""

import datetime
import re
import sys

# Support Python 3's simpler built-in types
if sys.version > '3':
    long = int
    basestring = unicode = str


def daterange(date, to=None, step=datetime.timedelta(days=1)):
    return DateRange(date, to, step)


class DateRange:
    """
    Similar to the built-in ``xrange()``, only for datetime objects.

    If called with just a ``datetime`` object, it will keep yielding values
    forever, starting with that date/time and counting in steps of 1 day.

    If the ``to_date`` keyword is provided, it will count up to and including
    that date/time (again, in steps of 1 day by default).

    If the ``step`` keyword is provided, this will be used as the step size
    instead of the default of 1 day. It should be either an instance of
    ``datetime.timedelta``, an integer, a string representing an integer, or
    a string representing a ``delta()`` value (consult the documentation for
    ``delta()`` for more information). If it is an integer (or string thereof)
    then it will be interpreted as a number of days. If it is not a simple
    integer string, then it will be passed to ``delta()`` to get an instance
    of ``datetime.timedelta()``.

    Note that, due to the similar interfaces of both objects, this function
    will accept both ``datetime.datetime`` and ``datetime.date`` objects. If
    a date is given, then the values yielded will be dates themselves. A
    caveat is in order here: if you provide a date, the step should have at
    least a ‘days’ component; otherwise the same date will be yielded forever.
    """

    def __init__(self, date, to=None, step=datetime.timedelta(days=1)):
        self.date = date

        if to is None:
            self.condition = lambda d: True
        else:
            self.condition = lambda d: (d <= to)

        if isinstance(step, (int, long)):
            # By default, integers are interpreted in days. For more granular
            # steps, use a `datetime.timedelta()` instance.
            step = datetime.timedelta(days=step)
        elif isinstance(step, basestring):
            # If the string
            if re.match(r'^(\d+)$', str(step)):
                step = datetime.timedelta(days=int(step))
            else:
                try:
                    step = delta(step)
                except ValueError:
                    pass

        if not isinstance(step, datetime.timedelta):
            raise TypeError('Invalid step value: %r' % (step,))

        self.step = step


    def __iter__(self):
        return self


    def next(self):
        if self.condition(self.date):
            current_date = self.date
            self.date += self.step
            return current_date
        else:
            raise StopIteration()


    # Python 3 compatibility
    def __next__(self):
        return self.next()


class delta(object):

    """
    Build instances of ``datetime.timedelta`` using short, friendly strings.

    ``delta()`` allows you to build instances of ``datetime.timedelta`` in
    fewer characters and with more readability by using short strings instead
    of a long sequence of keyword arguments.

    A typical (but very precise) spec string looks like this:

        '1 day, 4 hours, 5 minutes, 3 seconds, 120 microseconds'

    ``datetime.timedelta`` doesn’t allow deltas containing months or years,
    because of the differences between different months, leap years, etc., so
    this function doesn’t support them either.

    The parser is very simple; it takes a series of comma-separated values,
    each of which represents a number of units of time (such as one day,
    four hours, five minutes, et cetera). These ‘specifiers’ consist of a
    number and a unit of time, optionally separated by whitespace. The units
    of time accepted are (case-insensitive):

        * Days ('d', 'day', 'days')
        * Hours ('h', 'hr', 'hrs', 'hour', 'hours')
        * Minutes ('m', 'min', 'mins', 'minute', 'minutes')
        * Seconds ('s', 'sec', 'secs', 'second', 'seconds')
        * Microseconds ('ms', 'microsec', 'microsecs' 'microsecond',
          'microseconds')

    If an illegal specifier is present, the parser will raise a ValueError.

    This utility is provided as a class, but acts as a function (using the
    ``__new__`` method). This is so that the names and aliases for units are
    stored on the class object itself: as ``UNIT_NAMES``, which is a mapping
    of names to aliases, and ``UNIT_ALIASES``, the converse.
    """

    UNIT_NAMES = {
    ##  unit_name: unit_aliases
        'days': 'd day'.split(),
        'hours': 'h hr hrs hour'.split(),
        'minutes': 'm min mins minute'.split(),
        'seconds': 's sec secs second'.split(),
        'microseconds': 'ms microsec microsecs microsecond'.split(),
    }

    # Turn `UNIT_NAMES` inside-out, so that unit aliases point to canonical
    # unit names.
    UNIT_ALIASES = {}

    for cname, aliases in UNIT_NAMES.items():
        for alias in aliases:
            UNIT_ALIASES[alias] = cname
        # Make the canonical unit name point to itself.
        UNIT_ALIASES[cname] = cname

    def __new__(cls, string):
        specifiers = (specifier.strip() for specifier in string.split(','))
        kwargs = {}

        for specifier in specifiers:
            match = re.match(r'^(\d+)\s*(\w+)$', specifier)
            if not match:
                raise ValueError('Invalid delta specifier: %r' % (specifier,))

            number, unit_alias = match.groups()
            number, unit_alias = int(number), unit_alias.lower()

            unit_cname = cls.UNIT_ALIASES.get(unit_alias)
            if not unit_cname:
                raise ValueError('Invalid unit: %r' % (unit_alias,))
            kwargs[unit_cname] = kwargs.get(unit_cname, 0) + number

        return datetime.timedelta(**kwargs)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
