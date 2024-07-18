

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

def getDateComponents(iso_date):
    date = iso_date.split('T')[0]
    components = date.split('-')
    return components