#!/usr/bin/env python

# jiw 26 Dec 2018 - Using SolidPython to gen OpenSCAD code for parts
# to connect a drain hose to tile saw tray.

# Optional params for __main__:
#    makeConn, makeRing, holeDiam, scaleFactor
#    These default to 1, 1, 1.33, 25.4 respectively.

# When modifying this code:
# (a) At outset (ie once only), at command prompt say:
#           V=3;  SCF=flanged-tube$V.scad;  PYF=gen-${SCF%.scad}.py
#           STF=${SCF%.scad}.stl; exec-on-change $PYF "python $PYF" &
#           openscad $SCF &
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
    # Get inner and outer start and end diameters, and s & e heights 
    for jointNum, dis, die, dos, doe, hs, he in zip(range(len(dii)), dii, dii[1:], doo, doo[1:], hss, hss[1:]):
        if hs >= he: # Skip rings that don't have positive thickness
            continue
        print '{:2}.  dis {:<5.2f}, die {:<5.2f}, dos {:<5.2f}, doe {:<5.2f}, ys {:<5.2f}, ye {:<5.2f}'.format(jointNum, dis, die, dos, doe, hs, he)
        co = cylinder(d1=dos, d2=doe, h=he-hs)
        ci = cylinder(d1=dis, d2=die, h=he-hs+0.002)
        cyl = part()(co - hole()(down(0.001)(ci)))
        if jointNum:
            asm += up(hs)(cyl)
        else:
            asm = cyl
    return asm

def threadAsm(uplift, thredID, thredThik, pitch, starts, turns, extern):
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
    args = genArg([1, 1, 1.33, 25.4])
    makeConn = args.next()      # Generate connector if non-zero
    makeRing = args.next()      # Generate outer ring if non-zero
    hd = args.next()            # Hole diameter to fit
    sf = args.next()            # Scale factor
    
    # Set thread outer diameter, thread tooth depth, and number of turns
    thredOD, thredThik, turns = 1.33, 0.05, 0.8
    # base thickness, thread high/low, and thread inner diameter
    bThk, thredHi, thredLo, thredID = 0.07, 0.5, 0.2, thredOD-2*thredThik
    pitch = (thredHi-thredLo)/turns
    topThred = threadAsm(thredLo, thredID, thredThik, pitch, 3, turns, True)
    
    # Top piece: Specify inner and outer diameters, plus heights
    diam1 = thredID
    diam2 = diam1 - 0.11     # diam2 is diam1 minus 2 wall thicknesses
    dii = [0.38, 0.38, 0.38, 0.38, diam2, diam2]
    doo = [1.70, 1.70, 0.50, 0.50, diam1, diam1]
    hss = [0.00, bThk, bThk, 0.60, bThk,  thredHi]
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
