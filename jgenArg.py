#!/usr/bin/env python
# - jiw - 19 Nov 2018
'''Module to yield params, with default values and a few type conversions'''

def genArg(defVals):
    '''Make a generator to yield params, with default values and type conversions

Parameter `defVals` is a list of default values, which imply desired type of
result: integer, float, or string.  Note, if int(arg) or float(arg) get a 
ValueError while converting an arg, the arg is returned as a string.'''
    
    from sys import argv
    parnum = 1
    while 1:
        dv = defVals[parnum-1] if parnum<=len(defVals) else None
        v = argv[parnum] if len(argv)>parnum else dv
        try:
            v = int(v) if isinstance(dv, int) else (float(v) if isinstance(dv, float) else v)
        except ValueError:
            pass
        yield v
        parnum += 1

if __name__ == '__main__':
    '''Demo use of genArg to get and convert 3 args.'''
    from sys import argv
    def say(v, tv, nv):
        typ = 'i' if isinstance(v, int) else ('f' if isinstance(v, float) else ('s' if isinstance(v, basestring) else '?'))
        print '{} is `{}` vs default `{}`  Type: {}'.format(tv, v, defVals[nv], typ)
    
    defVals = [13, 17.7, 'nemo']
    print 'sys.argv = {}'.format(argv)
    print 'defVals  = {}'.format(defVals)
    vargs = genArg(defVals)
    ii = vargs.next();  say(ii, 'ii', 0)
    ff = vargs.next();  say(ff, 'ff', 1)
    ss = vargs.next();  say(ss, 'ss', 2)
