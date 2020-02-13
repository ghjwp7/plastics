#!/usr/bin/env python3

# jiw 26 Dec 2018
'''A program that uses SolidPython to generate OpenSCAD code for tubes
along selected edges between `posts` in a plane.  This supports
visualization of arrangements of edges in geodesic dome structures.'''

#  This program processes a layout script and a cylinders script.  See
#  `spec-layout-script.odt` for examples and details of both kinds of
#  scripts.

#  A layout script tells where to locate posts.  It has entries with
#  type of pattern (polygon, rectangular grid, triangular grid),
#  numbers of corners, rows, or columns, and radius or spacing.

#  A cylinders script tells what post-to-post cylinders to make.  It
#  has entries with optional <color>, <diam>, <post>, and <level>
#  elements.  Each semicolon terminator invokes cylinder production.

# Optional params for __main__:
#    designNum/name, endGap, postHi, pDiam, qDiam, SF

# [parameter handling revision, 12 Feb: allow params in any order; but
# require keyword=value forms -- eg `pDiam=0.07` -- where keyword
# should exactly match the name of a variable in the program.]

#  The command-line parameters default to designNum=0, endGap=.03,
#  postHi=.24, pDiam=.06, qDiam=.02, and SF=100 respectively, which
#  when scaled represent design number 0; 3-unit end gaps; 24-unit
#  post heights; thick and thin diameters of 6 and 2 units; and
#  100-unit scale factor.

#  Note, if the first parameter is a valid integer k (or blank, ie
#  k=0) pipeVue uses the k'th built-in script set for layout and
#  cylinders.  Else, the first parameter should be the name of a file
#  containing a layout script and a cylinders script.

#  Note, an end gap is a small gap between a post and a cylinder end.
#  With endGap=3, a gap of about 6 units is drawn between the ends of
#  cylinders meeting at the same point.  With endGap=0, there'd be no
#  gap.

# When modifying this code:
# (a) At outset (ie once only), at command prompt say:
#           V=0;  SCF=pipeVue$V.scad;  PYF=${SCF%.scad}.py
#           STF=${SCF%.scad}.stl; exec-on-change $PYF "python3 $PYF" &
#           echo $PYF, $SCF, $STF;  openscad $SCF &
#     [To avoid a 'Text file busy' shell error message, instead of
#      just saying  ./$PYF  the commands above use python to run $PYF]
# (b) After changes that you want to see the effect of, save the
#     file.  The exec-on-change script will be informed of the file
#     change and will run $PYF.  Then [if openscad `Design -> Automatic
#     Reload and Preview` option is on] openscad will see that $SCF
#     changed*, and re-render its image.
# (c) In openscad, press F6 to render details, then Export, as STL.
# (d) Say `craftware $STF &` then slice it and save gcode

from solid import cylinder, translate, rotate, scad_render_to_file, color
from solid.utils import down, up, left
from sys import argv
from math import sqrt, pi, cos, sin, asin, atan2
from collections import namedtuple

Point  = namedtuple('Point',  'x,y,z')
#  Design elements cSides, nPosts, pLayout, cSpec are two integers and
#  two strings. cSides is the number of central sides (allowing
#  central area to be pentagonal, hexagonal, etc.).  nPosts is the
#  total number of posts.  pLayout is a script for arrangement of
#  posts.  cSpec is a script for cylinders between points on posts.
#  Re script contents, see `spec-layout-script.odt`.
Design = namedtuple('Design', 'pLayout, cSpec')
Layout = namedtuple('Layout', 'BP, posts')

def rotate2(a,b,theta):
    st = sin(theta)
    ct = cos(theta)
    return  a*ct-b*st, a*st+b*ct

def produceOut(code, numText, LO):
    BP, posts = LO.BP, LO.posts
    bx, by, bz = BP.x, BP.y, BP.z
    nn = len(numText)
    def getNums(j, k):
        nums = []
        try:
            if j > nn or nn > k :
                raise ValueError;
            for ns in numText:
                nums.append(float(ns))
        except ValueError:
            print (f'Anomaly: code {code}, {numText} has wrong count or format')
            return None
        return nums
    
    if code=='B':               # Set base point, BP
        nums = getNums(3,3)     # Need exactly 3 numbers
        if nums: return Layout(Point(*nums), posts)

    if code=='C':               # Create a collection of posts
        nums = getNums(3,33333) # Need at least 3 numbers
        if nums:
            while len(nums) >= 3:
                x, y, z = nums[0]+bx,  nums[1]+by, nums[2]+bz
                posts.append(Point(x,y,z))
                nums = nums[3:]
            if len(nums)>0:
                print (f'Anomaly: code {code}, {numText} has {nums} left over')
            return Layout(BP, posts)

    if code=='L':               # Create a line of posts
        nums = getNums(4,4)     # Need exactly 4 numbers
        if nums:
            n, dx, dy, dz = int(nums[0]), nums[1], nums[2], nums[3]
            x, y, z = bx, by, bz
            for k in range(n):
                x, y, z = x+dx, y+dy, z+dz
                posts.append(Point(x,y,z))
            return Layout(BP, posts)

    if code=='P':               # Create a polygon of posts        
        nums = getNums(3,3)     # Need exactly 3 numbers
        if nums:
            n, r, a0 = int(nums[0]), nums[1], nums[2]
            theta = 2*pi/n
            x, y = rotate2(r, 0, a0*pi/180) # a0 in degrees
            for post in range(n):
                posts.append(Point(bx+x, by+y, bz))
                x, y = rotate2(x, y,theta)
    
    if code in 'RT':            # Create an array of posts
        nums = getNums(4,4)     # Need exactly 4 numbers
        if nums:
            r, c, dx, dy = int(nums[0]), int(nums[1]), nums[2], nums[3]
            y, z = by, bz
            for rr in range(r):
                x, roLen = bx, c
                # For odd rows of triangular arrays, offset the row
                if code=='T' and (rr&1)==1:
                    x, roLen = bx - dx/2, c+1
                for cc in range(roLen):
                    posts.append(Point(x,y,z))
                    x += dx
                y += dy
            return Layout(BP, posts)
    return LO                   # No change if we fail or fall thru
    
def doLayout(dz):
    LO = Layout(Point(0,0,0), [])
    pc, code, numbers = '?', '?', []
    codes, digits = 'BCLPRT', '01234356789+-.'
    
    for cc in dz.pLayout:       # Process current character
        # Add character to number, or store a number?
        if cc in digits:
            num = num + cc if pc in digits else cc
        elif pc in digits:
            numbers.append(num) # Add number to list of numbers

        # Process a completed entry, or start a new entry?
        if cc==';':
            LO = produceOut(code, numbers, LO)
        elif cc in codes:
            pc, code, numbers = '?', cc, []
        pc = cc                 # Prep to get next character
        
    # Now LO has an unscaled points list.  Create and return CSG
    posts = LO.posts
    for k in range(len(posts)):
        p = posts[k]
        posts[k] = Point(SF*p.x, SF*p.y, SF*p.z)
    assembly = None
    for p in posts:        
        tube = cylinder(d=SF*postDiam, h=SF*postHi)
        cyli = translate([p.x, p.y, p.z])(tube)
        assembly = assembly + cyli if assembly else cyli
    return assembly, Layout(LO.BP, posts)

def doCylinders(dz, LO, assembly):
    specs, posts = dz.cSpec, LO.posts
    colorr='G'; thix='p'; pc = None
    post1, post2, level1, level2 = '0', '1', 'c','c'
    colors, levels, digits = 'GYRBCMW', 'abcde', '01234356789'
    thixx = 'pqrstuvw'
    colorSet = dict({'G':'Green', 'Y':'Yellow', 'R':'Red', 'B':'Blue', 'C':'Cyan', 'M':'Magenta', 'W':'White'})
    nPosts = len(posts)
    deltaHi = SF*postHi/(len(levels)-1)
    loLevel = ord(levels[0])
    nonPost = True
    for cc in specs:
        if cc in colors: colorr = cc
        elif cc in thixx: thix  = cc
        elif cc in levels:
            level1, level2 = level2, cc
        elif cc in digits:
            if pc in digits:  post2 = post2 + cc
            else:             post1, post2 = post2, cc
            nonPost = False
        elif cc=='/':
            level1, level2 = level2, level1
        elif cc==';':
            if nonPost:
                post1, post2 = str(1+int(post1)), str(1+int(post2))
            m, n = int(post1)%nPosts, int(post2)%nPosts
            p, q = posts[m], posts[n]
            za1 = (ord(level1)-loLevel)*deltaHi
            za2 = (ord(level2)-loLevel)*deltaHi
            pz, qz = za1 + p.z, za2 + q.z
            dx, dy, dz  =  q.x-p.x,  q.y-p.y,  qz-pz
            L = max(0.1, sqrt(dx*dx + dy*dy + dz*dz))
            cName = colorSet[colorr]
            alpha = SF*endGap/L
            bx, by, bz = p.x+alpha*dx, p.y+alpha*dy, pz+alpha*dz
            print (f'Make  {cName:8} {thix} {m:2}{level1} {n:2}{level2}   Length {L:2.2f}')
            yAxisAngle = (pi/2 - asin(dz/L)) * 180/pi
            zAxisAngle =  atan2(dy, dx)      * 180/pi
            if thix=='p':
                diam = SF*pDiam
            else: # diameters q, r, s, t... scale geometrically
                diam = SF*qDiam*pow(dRatio,ord(thix)-ord('q'))
            tube = cylinder(d=diam, h=L-SF*2*endGap)
            colo = color(cName)(tube)
            tilt = rotate([0,yAxisAngle,zAxisAngle])(colo)
            cyli = translate([bx,by,bz])(tilt)
            assembly = assembly + cyli if assembly else cyli
            nonPost = True
        pc = cc
    return assembly

def installParams(parTxt):
    '''Given a string like "var1=val1 var2=val2 var3=val3 ...", extract
    the variable names and the values, convert the values to numeric
    forms, and store the values in the globals() dict.  Note, do not
    use any white space within any of the var=val strings.    '''
    plist = parTxt.split()      # Split the list on white space
    flubs, glob = '', globals()
    for vev in plist:
        p = pq = vev.split('=')          # Split each equation on = sign
        q, ok = '', False
        if len(pq)==2:
            p, q = pq
            if p in glob.keys():
                t, v = type(glob[p]), q
                try:
                    if   t==int:   v = int(q);    ok=True
                    elif t==float: v = float(q);  ok=True
                    elif t==str:   v = q;         ok=True
                except:  pass
        if ok:
            glob[p] = v
        else:  flubs += f' [ {p} {q} ] '
    if flubs: print (f'Parameter-setting fail: {flubs}')

def loadScriptFile(fiName):
    '''Read parameters, layout script, and cylinders script from file'''
    mode = 0;                   # Start out in comments mode
    pt = los = cs = ''          # Start with empty scripts
    with open(fiName) as fi:
        for line in fi:
            ll, l1, l2 = len(line), line[:1], line[:2]
            if l1 == '=':   # Detect section change vs comment ...
                if   l2=='=P': mode = 1 # Parameters
                elif l2=='=L': mode = 2 # Layout
                elif l2=='=C': mode = 3 # Cylinders
            else:
                if   mode==1: pt  = pt  + line
                elif mode==2: los = los + line
                elif mode==3: cs  = cs  + line
    installParams(pt)           # Install params, if any
    return Design(los, cs)      # Return Design

# Return 2 values, ival and fval (integer and float), using defVal as
# the result to return if not len(argv)>arn, and badCode as the result
# to return if conversion fails.
def getArg(arn, defVal, badCode):
    if len(argv)>arn:
        try:    ival = int(argv[arn])
        except: ival = badCode
        return ival
    else: return defVal
        
if __name__ == '__main__':
    # Set initial values of main parameters
    pDiam,   qDiam,    dRatio   = 0.06, 0.02, sqrt(2)
    endGap,  postHi,   postDiam = 0.03, 0.16, qDiam
    f,       SF,    cylSegments = '', 100, 30

    version, paramTxt = 0, ''
    for k in range(1,len(argv)):
        paramTxt = paramTxt + ' ' + argv[k]
    installParams(paramTxt)     # Set params from command line
    
    if f == '':
        dz = Design('C 0,0,0; P5,1,0;', 'Gpae 1,2;;;;1;')
    else:
        dz = loadScriptFile(f)  # May install params from file.
    installParams(paramTxt)     # Again, set params from command line.

    assembly, LO = doLayout(dz)
    assembly = doCylinders(dz, LO, assembly)
    asmFile = f'pipeVue{version}.scad'
    scad_render_to_file(assembly, asmFile,
                        file_header = f'$fn = {cylSegments};',
                        include_orig_code=False)
    print (f'Wrote scad code to {asmFile}')
