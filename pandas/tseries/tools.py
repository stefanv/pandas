from datetime import datetime, timedelta
import re
import sys

import numpy as np

import pandas._tseries as lib
import pandas.core.common as com

try:
    import dateutil
    from dateutil.parser import parser
    from dateutil.relativedelta import relativedelta

    # raise exception if dateutil 2.0 install on 2.x platform
    if (sys.version_info[0] == 2 and
        dateutil.__version__ == '2.0'):  # pragma: no cover
        raise Exception('dateutil 2.0 incompatible with Python 2.x, you must '
                        'install version 1.5!')
except ImportError: # pragma: no cover
    print 'Please install python-dateutil via easy_install or some method!'
    raise # otherwise a 2nd import won't show the message

def _delta_to_microseconds(delta):
    return (delta.days * 24 * 60 * 60 * 1000000
            + delta.seconds * 1000000
            + delta.microseconds)

def _infer_tzinfo(start, end):
    def _infer(a, b):
        tz = a.tzinfo
        if b and b.tzinfo:
            assert(tz == b.tzinfo)
        return tz
    tz = None
    if start is not None:
        tz = _infer(start, end)
    elif end is not None:
        tz = _infer(end, start)
    return tz


def _maybe_get_tz(tz):
    if isinstance(tz, (str, unicode)):
        import pytz
        tz = pytz.timezone(tz)
    return tz

def _figure_out_timezone(start, end, tzinfo):
    inferred_tz = _infer_tzinfo(start, end)
    tz = inferred_tz
    if inferred_tz is None and tzinfo is not None:
        tz = tzinfo
    elif tzinfo is not None:
        assert(inferred_tz == tzinfo)
        # make tz naive for now

    tz = _maybe_get_tz(tz)

    start = start if start is None else start.replace(tzinfo=None)
    end = end if end is None else end.replace(tzinfo=None)

    return start, end, tz


def to_datetime(arg, errors='ignore', dayfirst=False):
    """
    Convert argument to datetime

    Parameters
    ----------
    arg : string, datetime, array of strings (with possible NAs)
    errors : {'ignore', 'raise'}, default 'ignore'
        Errors are ignored by default (values left untouched)

    Returns
    -------
    ret : datetime if parsing succeeded
    """
    from pandas.core.series import Series
    if arg is None:
        return arg
    elif isinstance(arg, datetime):
        return arg
    elif isinstance(arg, Series):
        values = lib.string_to_datetime(com._ensure_object(arg.values),
                                        raise_=errors == 'raise',
                                        dayfirst=dayfirst)
        return Series(values, index=arg.index, name=arg.name)
    elif isinstance(arg, (np.ndarray, list)):
        if isinstance(arg, list):
            arg = np.array(arg, dtype='O')
        return lib.string_to_datetime(com._ensure_object(arg),
                                      raise_=errors == 'raise',
                                      dayfirst=dayfirst)

    try:
        if not arg:
            return arg
        return _dtparser.parse(arg, dayfirst=dayfirst)
    except Exception:
        if errors == 'raise':
            raise
        return arg


class DateParseError(ValueError):
    pass


_dtparser = parser()


# patterns for quarters like '4Q2005', '05Q1'
qpat1full = re.compile(r'(\d)Q(\d\d\d\d)')
qpat2full = re.compile(r'(\d\d\d\d)Q(\d)')
qpat1 = re.compile(r'(\d)Q(\d\d)')
qpat2 = re.compile(r'(\d\d)Q(\d)')


def parse_time_string(arg):
    """
    Try hard to parse datetime string, leveraging dateutil plus some extra
    goodies like quarter recognition.

    Parameters
    ----------
    arg : basestring

    Returns
    -------
    datetime, datetime/dateutil.parser._result, str
    """
    from pandas.core.format import print_config

    if not isinstance(arg, basestring):
        return arg

    arg = arg.upper()
    try:
        default = datetime(1,1,1).replace(hour=0, minute=0,
                                          second=0, microsecond=0)

        # special handling for possibilities eg, 2Q2005, 2Q05, 2005Q1, 05Q1
        if len(arg) in [4, 6]:
            add_century = False
            if len(arg) == 4:
                add_century = True
                qpats = [(qpat1, 1), (qpat2, 0)]
            else:
                qpats = [(qpat1full, 1), (qpat2full, 0)]

            for pat, yfirst in qpats:
                qparse = pat.match(arg)
                if qparse is not None:
                    if yfirst:
                        yi, qi = 1, 2
                    else:
                        yi, qi = 2, 1
                    q = int(qparse.group(yi))
                    y_str = qparse.group(qi)
                    y = int(y_str)
                    if add_century:
                        y += 2000
                    ret = default.replace(year=y, month=(q-1)*3+1)
                    return ret, ret, 'quarter'

        dayfirst = print_config.date_dayfirst
        yearfirst = print_config.date_yearfirst

        parsed = _dtparser._parse(arg, dayfirst=dayfirst, yearfirst=yearfirst)
        if parsed is None:
            raise DateParseError("Could not parse %s" % arg)

        repl = {}
        reso = 'year'
        stopped = False
        for attr in ["year", "month", "day", "hour",
                     "minute", "second", "microsecond"]:
            can_be_zero = ['hour', 'minute', 'second', 'microsecond']
            value = getattr(parsed, attr)
            if value is not None and (value != 0 or attr in can_be_zero):
                repl[attr] = value
                if not stopped:
                    reso = attr
                else:
                    raise DateParseError("Missing attribute before %s" % attr)
            else:
                stopped = True
        ret = default.replace(**repl)
        return ret, parsed, reso  # datetime, resolution
    except Exception, e:
        raise DateParseError(e)

def normalize_date(dt):
    if isinstance(dt, np.datetime64):
        dt = lib.Timestamp(dt)
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def format(dt):
    """Returns date in YYYYMMDD format."""
    return dt.strftime('%Y%m%d')

OLE_TIME_ZERO = datetime(1899, 12, 30, 0, 0, 0)

def ole2datetime(oledt):
    """function for converting excel date to normal date format"""
    val = float(oledt)

    # Excel has a bug where it thinks the date 2/29/1900 exists
    # we just reject any date before 3/1/1900.
    if val < 61:
        raise Exception("Value is outside of acceptable range: %s " % val)

    return OLE_TIME_ZERO + timedelta(days=val)

