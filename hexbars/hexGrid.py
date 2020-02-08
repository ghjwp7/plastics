#!/usr/bin/env python3

# jiw 26 Dec 2018
'''A program that uses SolidPython to generate OpenSCAD code for tubes
along selected edges in a hex grid.  This is for visualization of tube
placements for truss-like strengthening of geodesic dome structures.'''

# Optional params for __main__:
#    dCase, eGap, poHi, pDiam, qDiam, stSep

#    These default to 0, 5, 8, 6, 2, and 100 respectively,
#    representing design case 0; 5-unit end gaps; 8-unit post heights;
#    thick and thin diameters of 6 and 2 units; and 100-unit standard
#    separation between posts.

# This program processes a string of cylinder specifications.  Each
# specification is an entry containing <color>, <diam>, <end1>, and
# <end2> elements, terminated by a semicolon.  <color> is one of G, Y,
# R, B, C, or M for green, yellow, red, blue, cyan, magenta.  <diam>
# is p or q, where (by default) p is thick, q is thin.  Each of <end1>
# and <end2> has form <post>or <post><level> or <level><post>.  Each
# <post> is a decimal integer identifying a vertex.  Each <level> is a
# letter (a-e) for a level on a post.  Level a is low, e is high, and
# others are spread proportionally between.  The semicolon after
# <end2> is required punctuation.  Whenever a semicolon appears, a
# cylinder is produced, using the most recent two post numbers and two
# levels, whatever they are, and the most recent color and diameter.
# Thus, most elements are optional within each entry, and elements not
# given remain as previously specified.  For example, the
# specification 'Ccc0,1;2;3;4;' draws four cyan-colored cylinders, in
# a chain from post 0 to 1 to 2 to 3 to 4, with all ends at level c.
# Color, thickness, and level initial defaults are G,p,a.  White space
# and other characters are ignored, except that they delimit post
# numbers. For example, the entries quoted in the following set are
# equivalent: { "Gp0a1e;" "pG0ae1;" "ae0Gp1;" }.

# When modifying this code:
# (a) At outset (ie once only), at command prompt say:
#           V=0;  SCF=hexGrid$V.scad;  PYF=${SCF%.scad}.py
#           STF=${SCF%.scad}.stl; exec-on-change $PYF "python $PYF" &
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

class Post:
    def __init__(self, x, y, zb=0):
        self.x, self.y, self.z = x, y, zb

posts = []
def makePosts(inSides, nPosts):
    posts.append(Post(0,0))
    theta = 2*pi/inSides
    st, ct = sin(theta), cos(theta)
    x, y = stSep, 0
    for post in range(inSides):        
        posts.append(Post(x,y))
        x, y = x*ct - y*st, x*st + y*ct
    #print (list((p.x,p.y) for p in posts))

def rotate2(a,b,theta):
    st = sin(theta)
    ct = cos(theta)
    return  a*ct-b*st, a*st+b*ct

def doSpecs(specs, nPosts):
    colorr='G'; thix='p'; assembly = pc = None
    post1, post2, level1, level2 = '0', '1', 'c','c'
    colors, levels, digits = 'GYRBCM', 'abcde', '01234356789'
    colorSet = dict({'G':'Green', 'Y':'Yellow', 'R':'Red', 'B':'Blue', 'C':'Cyan', 'M':'Magenta'})
    
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
            m, n = int(post1)%nPosts, int(post2)%nPosts
            p, q = posts[m], posts[n]
            za1 = (ord(level1)-loLevel)*deltaHi
            za2 = (ord(level2)-loLevel)*deltaHi
            pz, qz = za1 + p.z, za2 + q.z
            dx, dy, dz  =  q.x-p.x,  q.y-p.y,  qz-pz
            L = max(0.1, sqrt(dx*dx + dy*dy + dz*dz))
            cName = colorSet[colorr]
            print (f'Make  {cName:6} {thix} {m}{level1} {n}{level2}   Length {L:2.2f}')
            yAxisAngle = (pi/2 - asin(dz/L)) * 180/pi
            zAxisAngle =  atan2(dy, dx)      * 180/pi
            tube = cylinder(d=pDiam if thix=='p' else qDiam, h=L)
            colo = color(cName)(tube)
            tilt = rotate([0,yAxisAngle,zAxisAngle])(colo)
            cyli = translate([p.x,p.y,pz])(tilt)
            assembly = assembly + cyli if assembly else cyli
        pc = c
    return assembly

if __name__ == '__main__': 
    arn = 0   # Get params:
    arn+=1; dCase = int(argv[arn])   if len(argv)>arn else 0
    arn+=1; eGap  = float(argv[arn]) if len(argv)>arn else 5
    arn+=1; poHi  = float(argv[arn]) if len(argv)>arn else 24
    arn+=1; pDiam = float(argv[arn]) if len(argv)>arn else 6
    arn+=1; qDiam = float(argv[arn]) if len(argv)>arn else 2
    arn+=1; stSep = float(argv[arn]) if len(argv)>arn else 100
    cylSegments = 30
    version = 0
    asmFile = f'hexGrid{version}.scad'
    specs0 = 'Gpae 0 1;2;3;4;5;1;'
    specs1 = 'Gp 0a1e; Rp 1a2a; Cq 3;c4c;p a5e;a6e;Ma1e;2ab;e3;ae4; 5 ; 6;'
    specs2 = 'pae B0 1;G2;R3;Y4;C5;M6;G7;Y1; qea G2;R3;Y4;C5;M6;G7;Y1;'
    cases = ((5, 6, specs0), (6,7,specs1), (7,8,specs2))
    dCase = min(dCase, len(cases)-1)
    nSides, nPosts, dSpec = cases[dCase]
    makePosts(nSides, nPosts)
    assembly = doSpecs(dSpec, nPosts)
    scad_render_to_file(assembly, asmFile,
                        file_header = f'$fn = {cylSegments};',
                        include_orig_code=False)
    print (f'Wrote scad code to {asmFile}')