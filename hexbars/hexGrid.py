#!/usr/bin/env python3

# jiw 26 Dec 2018
'''A program that uses SolidPython to generate OpenSCAD code for tubes
along selected edges in a hex grid.  This is for visualization of tube
placements for truss-like strengthening of geodesic dome structures.'''

# Optional params for __main__:
#    eGap, pDiam, qDiam
#    These default to .05, .06, .02 respectively.

# This program processes a string of cylinder specifications.  Each
# specification is an entry containing <color>, <diam>, <end1>, and
# <end2> elements, terminated by a semicolon.  <color> is one of G, Y,
# R, B, C for green, yellow, red, blue, cyan.  <diam> is p or q, where
# (by default) p is thick, q is thin.  Each of <end1> and <end2> has
# form <post>or <post><level> or <level><post>.  Each <post> is a
# digit (0-9) identifying a vertex.  Each <level> is a letter (a-e)
# for a level on a post.  Level a is high, c is central, and e is low.
# The semicolon after <end2> is required punctuation; whenever a
# semicolon appears, a cylinder gets produced, using the most recent
# two post numbers and levels, whatever they are, and the most recent
# color and diameter.  For example, the entries in the following set
# are equivalent: { Gp0a1e;, pG01ae;, ae01Gp }.  White space is
# ignored.  <color>, <diam>, and <level> elements are optional, and
# when not given remain as previously specified. (Initial default:
# Gpa)

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

from solid import cylinder, hole, part, rotate, scad_render_to_file, scale
from solid.screw_thread import thread, default_thread_section
from solid.utils import down, up, left
from sys import argv

posts = []
def makePosts():
    for post in range(10):
        posts.append(post)  # make a post object to put in here

def doSpecs(specs):
    color='G'; thix='p'
    post1, post2, level1, level2 = 0, 1, 'c','c'
    for c in specs:
        if c in 'GYRBC': color = c
        elif c in 'pq' : thix = c
        elif c in 'abcde':
            level1, level2 = level2, c
        elif c in '01234356789':
            post1, post2 = post2, c
        elif c==';':
            print (f'Make  {color}{thix} {post1}{level1} {post2}{level2}')


if __name__ == '__main__': 
    arn = 0   # Get params:
    arn+=1; eGap  = float(argv[arn]) if len(argv)>arn else .05
    arn+=1; pDiam = float(argv[arn]) if len(argv)>arn else .06
    arn+=1; qDiam = float(argv[arn]) if len(argv)>arn else .02
    cylSegments = 30
    version = 0
    asmFile = f'hexGrid{version}.scad'
    assembly = cylinder(d=pDiam, h=1)
    scad_render_to_file(assembly, asmFile,
                        file_header = f'$fn = {cylSegments};',
                        include_orig_code=False)
    print ('Wrote scad code to {}'.format(asmFile))

    specs = 'Gp 0a1e; Rp 1a2a; Cq0c2c; 34;45;56;'
    doSpecs(specs)