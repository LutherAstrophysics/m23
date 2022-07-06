import re
def nameAfterAlignment(nameToAlign):
    return (re.sub('.fit$', '-aligned.fit', nameToAlign))