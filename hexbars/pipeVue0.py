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
#    deNum/name, eGap, poHi, pDiam, qDiam, SF

#  The command-line parameters default to deNum=0, eGap=3, poHi=16,
#  pDiam=6, qDiam=2, and SF=100 respectively, representing design
#  number 0; 3-unit end gaps; 16-unit post heights; thick and thin
#  diameters of 6 and 2 units; and 100-unit scale factor.

#  Note, if the first parameter is a valid integer k (or blank, ie
#  k=0) pipeVue uses the k'th built-in script set for layout and
#  cylinders.  Else, the first parameter should be the name of a file
#  containing a layout script and a cylinders script.

#  Note, an end gap is a small gap between a post and a cylinder end.
#  With eGap=3, a gap of about 6 units is drawn between the ends of
#  cylinders meeting at the same point.  With eGap=0, there'd be no
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
                posts.append(Point(x,y,bz))
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
        tube = cylinder(d=qDiam, h=poHi)
        cyli = translate([p.x, p.y, p.z])(tube)
        assembly = assembly + cyli if assembly else cyli
    return assembly, Layout(LO.BP, posts)

def doCylinders(dz, LO, assembly):
    specs, posts = dz.cSpec, LO.posts
    colorr='G'; thix='p'; pc = None
    post1, post2, level1, level2 = '0', '1', 'c','c'
    colors, levels, digits = 'GYRBCMW', 'abcde', '01234356789'
    colorSet = dict({'G':'Green', 'Y':'Yellow', 'R':'Red', 'B':'Blue', 'C':'Cyan', 'M':'Magenta', 'W':'White'})
    nPosts = len(posts)
    deltaHi = poHi/(len(levels)-1)
    loLevel = ord(levels[0])
    noPL = True
    for cc in specs:
        if cc in colors: colorr = cc
        elif cc in 'pqr' : thix  = cc
        elif cc in levels:
            level1, level2 = level2, cc
            noPL = False
        elif cc in digits:
            if pc in digits:  post2 = post2 + cc
            else:             post1, post2 = post2, cc
            noPL = False
        elif cc=='/':
            level1, level2 = level2, level1
        elif cc==';':
            if noPL:
                post1, post2 = str(1+int(post1)), str(1+int(post2))
            m, n = int(post1)%nPosts, int(post2)%nPosts
            p, q = posts[m], posts[n]
            za1 = (ord(level1)-loLevel)*deltaHi
            za2 = (ord(level2)-loLevel)*deltaHi
            pz, qz = za1 + p.z, za2 + q.z
            dx, dy, dz  =  q.x-p.x,  q.y-p.y,  qz-pz
            L = max(0.1, sqrt(dx*dx + dy*dy + dz*dz))
            cName = colorSet[colorr]
            alpha = eGap/L
            bx, by, bz = p.x+alpha*dx, p.y+alpha*dy, pz+alpha*dz
            print (f'Make  {cName:8} {thix} {m:2}{level1} {n:2}{level2}   Length {L:2.2f}')
            yAxisAngle = (pi/2 - asin(dz/L)) * 180/pi
            zAxisAngle =  atan2(dy, dx)      * 180/pi
            diam = rDiam if thix=='r' else qDiam if thix=='q' else pDiam
            tube = cylinder(d=diam, h=L-2*eGap)
            colo = color(cName)(tube)
            tilt = rotate([0,yAxisAngle,zAxisAngle])(colo)
            cyli = translate([bx,by,bz])(tilt)
            assembly = assembly + cyli if assembly else cyli
            noPL = True
        pc = cc
    return assembly

def loadScriptFile(fiName):
    '''Read a layout script and a cylinders script from a file'''
    mode = 0;                   # Start out in comments mode
    los = cs = ''               # Start with empty scripts
    with open(fiName) as fi:
        for line in fi:
            ll = len(line)
            if mode==0:         # In comments mode?
                if ll>1 and line[0]=='=':
                    if line[1]=='L': # Got a Layout Script ?
                        mode = 1
                    if line[1]=='C': # Got a Cylinder Script ?
                        mode = 2
            elif mode==1:
                if ll>1 and line[0]=='=' and line[1]=='C':
                    mode = 2
                else:
                    los = los + line
            elif mode==2:
                if ll>1 and line[0]=='=' and line[1]=='L':
                    mode = 2
                else:
                    cs = cs + line
    # Having read in and then closed a file, return a Design
    return Design(los, cs)
    
specs0 = 'Gpae 1,2; 2,3; 3,4; 4,5; 5,1;"'
specs1 = 'Gpae 1,2;3;4;5;1;'
specs2 = 'Gpae 1,2;;;;1;'
specs3 = 'Gpae 1,2;;;;1; R6,2;;;;10,1; Y1,6;;;;; B11,6;;;;; C6,12;;;;10,11; M1,11;;;;; 0,1;0,2;0,3;0,4;0,5;'
layout0=layout1=layout2='C 0,0,0; P5,1,0;'
layout3= 'C 0,0,0; P5,1,0; P5,1.6,36; P5,2,0;'
design0 = Design(layout0, specs0)
design1 = Design(layout1, specs1)
design2 = Design(layout2, specs2)
design3 = Design(layout3, specs3)
designs = (design0, design1, design2, design3)

# Return 2 values, ival and fval (integer and float), using defVal as
# the result to return if not len(argv)>arn, and badCode as the result
# to return if conversion fails.
def getArg(arn, defVal, badCode):
    if len(argv)>arn:
        try:    ival = int(argv[arn])
        except: ival = badCode
        try:    fval = float(argv[arn])
        except: fval = badCode
        return ival, fval
    else: return defVal, defVal

if __name__ == '__main__': 
    arn = 0   # Get params:
    arn+=1; deNum, dc  = getArg(arn, 0,    None)
    arn+=1; dc,  eGap  = getArg(arn, 0.03, 0.03)
    arn+=1; dc,  poHi  = getArg(arn, 0.16, 0.16)
    arn+=1; dc,  pDiam = getArg(arn, 0.06, 0.06)
    arn+=1; dc,  qDiam = getArg(arn, 0.02, 0.02)
    arn+=1; dc,  SF    = getArg(arn, 100,  100)
    eGap, poHi = eGap*SF, poHi*SF
    rDiam = 2*pDiam
    pDiam, qDiam, rDiam = pDiam*SF, qDiam*SF, rDiam*SF
    cylSegments = 30
    version = 0
    asmFile = f'pipeVue{version}.scad'
    dz = designs[min(deNum, len(designs)-1)] if deNum != None else loadScriptFile(argv[1])
    #assembly = makePosts(dz)
    assembly, LO = doLayout(dz)
    assembly = doCylinders(dz, LO, assembly)
    scad_render_to_file(assembly, asmFile,
                        file_header = f'$fn = {cylSegments};',
                        include_orig_code=False)
    print (f'Wrote scad code to {asmFile}')
