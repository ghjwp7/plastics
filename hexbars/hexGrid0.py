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
#  k=0) hexGrid uses the k'th built-in script set for layout and
#  cylinders.  Else, the first parameter should be the name of a file
#  containing a layout script and a cylinders script.

#  Note, an end gap is a small gap between a post and a cylinder end.
#  With eGap=3, a gap of about 6 units is drawn between the ends of
#  cylinders meeting at the same point.  With eGap=0, there'd be no
#  gap.

# When modifying this code:
# (a) At outset (ie once only), at command prompt say:
#           V=0;  SCF=hexGrid$V.scad;  PYF=${SCF%.scad}.py
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

posts = []

def rotate2(a,b,theta):
    st = sin(theta)
    ct = cos(theta)
    return  a*ct-b*st, a*st+b*ct

def produceOut(code, numbers, LO):
    BP, posts = LO.BP, LO.posts
    bx, by, bz = BP.x, BP.y, BP.z
    nn = len(numbers)
    def getNums(j, k):
        nums = []
        try:
            if j > nn or nn > k :
                raise ValueError;
            for ns in numbers:
                nums.append(float(ns))
        except ValueError:
            print (f'Anomaly: code {code}, numbers {numbers}')
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
                posts.append(Point(x,y,0))
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
    #print(f'\nline 162: scale & make,   posts={posts}, len()={len(posts)}')
    for k in range(len(posts)):
        p = posts[k]
        posts[k] = Point(SF*p.x, SF*p.y, SF*p.z)
    #print(f'\nline 166:  len(posts) {len(posts)}')
    assembly = None
    for p in posts:        
        tube = cylinder(d=qDiam, h=poHi)
        cyli = translate([p.x, p.y, p.z])(tube)
        assembly = assembly + cyli if assembly else cyli
    
    #print(f'\nline 173:  dz {dz},  LO.BP {LO.BP},   len(posts) {len(posts)}')
    return assembly, Layout(LO.BP, posts)

def doCylinders(dz, LO, assembly):
    specs, posts = dz.cSpec, LO.posts
    #print(f'\nline 178: posts {posts}, dz {dz}')
    colorr='G'; thix='p'; pc = None
    post1, post2, level1, level2 = '0', '1', 'c','c'
    colors, levels, digits = 'GYRBCM', 'abcde', '01234356789'
    colorSet = dict({'G':'Green', 'Y':'Yellow', 'R':'Red', 'B':'Blue', 'C':'Cyan', 'M':'Magenta'})
    nPosts = len(posts)
    deltaHi = poHi/(len(levels)-1)
    loLevel = ord(levels[0])
    for c in specs:
        if c in colors: colorr = c
        elif c in 'pq' : thix  = c
        elif c in levels:
            level1, level2 = level2, c
        elif c in digits:
            if pc in digits:  post2 = post2 + c
            else:             post1, post2 = post2, c
        elif c==';':
            #print(f'\nline 195: post1,post2 {post1},{post2}, nPosts {nPosts}, dz {dz}')
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
            tube = cylinder(d=pDiam if thix=='p' else qDiam, h=L-2*eGap)
            colo = color(cName)(tube)
            tilt = rotate([0,yAxisAngle,zAxisAngle])(colo)
            cyli = translate([bx,by,bz])(tilt)
            assembly = assembly + cyli if assembly else cyli
        pc = c
    return assembly

specs0 = 'Gpae 0 1;C2;3;4;5;1; Rqaa2;3;4;5;1; Mqee2;3;4;5;1; Ypae 6 7;8;9;G10;11;R6;Yea 12 13;G14;15;16;17;18;C12;'
specs1 = 'Gp 0a1e; Rp 1a2a; Cq 3;c4c;p a5e;a6e;Ma1e;2ab;e3;ae4; 5 ; 6;'
specs2 = 'pae B0 1;G2;R3;Y4;C5;M6;G7;Y1; qea G2;R3;Y4;C5;M6;G7;Y1;'
specs3 = 'qCab0,1;c;d;e;'
cases = ((5, 6, specs0), (6,7,specs1), (7,8,specs2), (5,6,specs3))
layout0=layout1=layout2=layout3='''C 0,0,0;
P5,1,0;
P6,1.3,30;
P7,1.5,23;
B1.5,.5,-.2;   R5,5,.1,.1;
B-2,.5,.3;     T7,6,.1,.0866;
B-.5,-.5,-.5;  L10 .1, .1, .1;
'''
design0 = Design(layout0, specs0)
design1 = Design(layout1, specs1)
design2 = Design(layout2, specs2)
design3 = Design(layout3, specs3)
designs = (design0, design1, design2, design3)

if __name__ == '__main__': 
    arn = 0   # Get params:
    arn+=1; deNum = int(argv[arn])   if len(argv)>arn else 0
    arn+=1; eGap  = float(argv[arn]) if len(argv)>arn else 3
    arn+=1; poHi  = float(argv[arn]) if len(argv)>arn else 16
    arn+=1; pDiam = float(argv[arn]) if len(argv)>arn else 6
    arn+=1; qDiam = float(argv[arn]) if len(argv)>arn else 2
    arn+=1; SF    = float(argv[arn]) if len(argv)>arn else 100
    cylSegments = 30
    version = 0
    asmFile = f'hexGrid{version}.scad'
    dz = designs[min(deNum, len(cases)-1)]
    #assembly = makePosts(dz)
    assembly, LO = doLayout(dz)
    assembly = doCylinders(dz, LO, assembly)
    scad_render_to_file(assembly, asmFile,
                        file_header = f'$fn = {cylSegments};',
                        include_orig_code=False)
    print (f'Wrote scad code to {asmFile}')
