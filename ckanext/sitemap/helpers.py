
from datetime import *

## Debug
#import pydevd_pycharm
#pydevd_pycharm.settrace('localhost', port=6666, stdoutToServer=True, stderrToServer=True, suspend=False)

def getExtrasValue(package, key):
    """ Return the value associated with the given key in the package extras list.
        If the given key is not in the list, return None.
    """
    as_dict = package.as_dict()
    extras = as_dict['extras']
    returnValue = extras.get(key, None)
    return returnValue

def isDOI(urlString):
    """  Returns True if urlString appears to be a DOI.  Otherwise, it returns False.
    """
    isDOI = False
    if urlString:
       if urlString.startswith('http://doi.org/') or urlString.startswith('https://doi.org/'):
          isDOI = True
    return isDOI

def getDOISuffix(urlString):
    suffix = urlString.split('doi.org/', 1)[1]
    return suffix

def getDateParts(iso_date):
    date = iso_date.split('T')[0]
    components = date.split('-')
    return components

def getExtentParts(extent):
    """ Parse Solr date range with format similar to "[1992-11-01 TO 1993-02-28]"
        Sometimes the second value is '*', which means "Now" in Solr
    """
    dates = extent[1:-1].split(' TO ')
    startDate = dates[0].split('-')
    if dates[1] == '*':
        iso_date = datetime.now().isoformat()
        date = iso_date.split('T')[0]
        endDate = date.split('-')
    else:
        endDate = dates[1].split('-')
    return (startDate, endDate)


def getPersonParts(author):
    """ Try to split compound names into firstName and lastName.
        If the name is too complex, place everything in firstName.
    """
    parts = None
    # Most specific case is finding a single comma.
    split1 = parts.split(',')
