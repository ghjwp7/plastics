#!/usr/bin/env python

# jiw 26 Dec 2018
'''Use SolidPython to generate OpenSCAD code for parts to connect a
drain hose to a tile saw tray.  More generally, make a threaded
bulkhead-mounting hose connector.

thredSlop (in __main__) controls looseness-of-fit between mating
threads.  Larger values make a looser, sloppier fit.  Smaller values
make tighter fits.  If the fit is too tight, the outer ring won't fit
over the inner.  On my Omni (a Prusa-style 3D printer) using CraftWare
slicing with 0.03 mm layers, thredSlop of 0.03" (and other values
defaulted) is too small for the ring to fit on, while 0.05" slop works
ok with 0.02 mm layers.
'''
# Optional params for __main__:
#    makeConn, makeRing, holeDiam, scaleFactor
#    These default to 1, 1, 1.33, 25.4 respectively.

# When modifying this code:
# (a) At outset (ie once only), at command prompt say:
#           V=3;  SCF=flanged-tube$V.scad;  PYF=gen-${SCF%.scad}.py
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

def cylinderAsm(dii, doo, hss):
    '''Produce an assembly of specified cylinders, given three lists that
       specify sequences of inner diameters, outer diameters, and
       heights.  Consecutive triples (of diameters and height) specify
       the ends of a cylindrical or conical portion of an assembly, in
       ascending order of heights; except if the next height in
       sequence isn't more than the current height, there is no output
       for that pair of triples.
    '''
    # Get inner and outer start and end diameters, and s & e heights
    asm = None
    for jointNum, dis, die, dos, doe, hs, he in zip(range(len(dii)), dii, dii[1:], doo, doo[1:], hss, hss[1:]):
        if hs >= he: # Skip rings that don't have positive thickness
            continue
        print '{:2}.  dis {:<5.2f}, die {:<5.2f}, dos {:<5.2f}, doe {:<5.2f}, ys {:<5.2f}, ye {:<5.2f}'.format(jointNum, dis, die, dos, doe, hs, he)
        co = cylinder(d1=dos, d2=doe, h=he-hs)
        ci = cylinder(d1=dis, d2=die, h=he-hs+0.002)
        cyl = part()(co - hole()(down(0.001)(ci)))
        asm = asm + up(hs)(cyl) if asm else cyl
    return asm

def threadAsm(uplift, thredID, thredThik, pitch, starts, turns, extern):
    '''Return an assembly for an internal or external thread of given
       inner diameter, thickness, and pitch, with specified number of
       starts (independent thread parts), wrapping a given number of
       turns.  uplift = Z-axis translation amount.  Inner diameter
       thredID is the diameter of the cylinder the threads wrap
       against.  It is that cylinder's outer diameter for external
       threads, or the cylinder's inner diameter for internal threads.
       threadAsm adds or subtracts an epsilon (0.0001) to prevent
       small gaps between thread and cylinder, which if they happen
       will lead to rendering/slicing error messages.
    '''
    inRadi, eps, thredSpan = thredID/2, 1e-4, pitch*turns
    # Set tooth_height and tooth_depth in thread-shape
    thredShape = default_thread_section((pitch/starts)-eps, thredThik)
    # Generate one thread start, with eps to ensure not non-manifold
    inRadiEps = inRadi - (eps if extern else -eps)
    thred1 = thread(thredShape, inRadiEps, pitch, thredSpan, external=extern,
                  segments_per_rot=40, neck_in_degrees=30, neck_out_degrees=30)
    thred = thred1
    # Rotate thred1 for other thread starts
    for t in range(1,starts):
        thred += rotate(a=(0, 0, (t*360)/starts))(thred1)
    # Return thread moved up to proper position
    return up(uplift)(thred)
    
if __name__ == '__main__':
    from jgenArg import genArg
    args = genArg([1, 0, 1.33, 25.4])
    makeConn = args.next()      # Generate connector if non-zero
    makeRing = args.next()      # Generate outer ring if non-zero
    hd = args.next()            # Hole diameter to fit
    sf = args.next()            # Scale factor

    # Set thread pitch
    pitch = .375                # Inches of rise per full revolution
    
    # Set thread outer diameter, thread tooth depth, and flange base thickess
    thredOD, thredThik, baseThik = 1.33, 0.05, 0.07
    # thread high z, low z, and its inner diameter
    thredHi, thredLo, thredID =0.66, 0.2, thredOD-2*thredThik
    turns = (thredHi-thredLo)/pitch
    topThred = threadAsm(thredLo, thredID, thredThik, pitch, 3, turns, True)
    
    # Top piece: Specify inner and outer diameters, plus heights
    diam1 = thredID
    diam2 = diam1 - 0.11     # diam2 is diam1 minus 2 wall thicknesses
    cdiam1, cdiam2, cHi = .6, .5, baseThik+.25
    ddiam1, ddiam2 = cdiam1+0.07, cdiam2+0.07
    #      ...flange.....    ....center....     ...outer tube...
    dii = [cdiam1, cdiam1,   cdiam1, cdiam2,    diam2,    diam2]
    doo = [1.70,   1.70,     ddiam1, ddiam2,    diam1,    diam1]
    hss = [0.00, baseThik,   baseThik,  cHi,   baseThik,  thredHi]
    topAsm = cylinderAsm(dii, doo, hss) # Make assembly-of-cylinders

    # Bottom piece: Specify inner and outer diameters, plus heights
    thredSlop = 0.05            # Oversize to avoid thread binding
    # The bottom's ID is top's OD plus some slop for clearance
    diam1, diam2 = thredOD+thredSlop+0.20, thredOD+thredSlop
    moveTop = (doo[0]+diam1+.1)/2 # Left-shift for top & bottom parts
    ringHi = 0.35
    turns = ringHi/pitch
    dii = [diam2, diam2]
    doo = [diam1, diam1-0.10]
    hss = [0, ringHi]
    botAsm = cylinderAsm(dii, doo, hss) # Make assembly-of-cylinders
    botThred = threadAsm(0, diam2, thredThik, pitch, 3, turns, False)
        
    # Assemble items and apply scale factor
    asm, bot, top = None,  botAsm + botThred,  topThred+topAsm
    if makeConn: asm = left(moveTop)(top)
    if makeRing: asm = asm + bot if asm else bot
    asm = scale((sf, sf, sf))(asm)
    cylSegments, version = 60, 3
    cylSet_fn = '$fn = {};'.format(cylSegments)
    asmFile = 'flanged-tube{}.scad'.format(version)
    scad_render_to_file(asm, asmFile, file_header=cylSet_fn, include_orig_code=False)
    print ('Wrote scad code to {}'.format(asmFile))
