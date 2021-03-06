#!/usr/bin/env python

# jiw 26 Feb 2019 - Using SolidPython to gen OpenSCAD code for
# SMD-tape channels, for pick-and-place operations -- with specs
# picked up from QtTableWidget application

from math import sqrt
from PyQt5.QtCore import Qt
from solid import color, cube, cylinder, rotate
from solid import hole, part, scad_render_to_file, scale, translate
from solid.utils import up, down, left, right, forward, back
from solid.utils import Cyan, Green, Red, Magenta
from ChannelVars import Table1, Table2, Table3 # tape-types, rail-specs, units-to-do
from ChannelCallbacks import CallData
from loadTablesForXML import loadAndShow
#--------------------------------------------------
class RailData:                 # Specs for channel-rail
    def __init__(self, mains, eps):
        '''Get data from rails tables for selected row of table.

        Parameters: mains is overall data-and-display structure.
        eps is a small number, like 0.005 mm (0.0002"), added (a) to
        each end of post-hole to ensure open ends of holes, and (b) to
        height of leg structure to ensure leg and cap overlap, no gap.
        '''
        tab = mains.tab2
        ro  = tab.radioRo
        self.railOk = False
        if ro < 0:
            return
        rtab = Table2(tab,ro)
        self.CapLen      = rtab.getCapLen()
        self.nPosts      = rtab.getPosts()
        self.PostOffset  = rtab.getPostOffset()
        self.PostID      = rtab.getPostID()
        self.PostOD      = rtab.getPostOD()
        self.LegThik     = rtab.getLegThik()
        self.CapThik     = rtab.getCapThik()
        self.CapWide     = rtab.getCapWide()
        self.EndLen      = rtab.getEndLen()
        self.PadLen      = rtab.getPadLen()
        self.Slack       = rtab.getSlack()
        self.Bridges     = rtab.getBridges()
        self.BridgeOffset= rtab.getBridgeOffset()
        self.BridgeWide  = rtab.getBridgeWide()
        self.Output      = rtab.getOutput()
        self.eps         = eps
        self.railOk = True
        #self.      = rtab.get()
#-------------------------------------------------- 
class TapeData:                 # Specs for one tape-type
    '''Get data for one tape type from tapes table, and put into a
    TapeData object.'''
    def __init__(self, mains, ttype, rofrom):
        '''Get data from tapes table for tape type with name ttype.
        On ok result, set tapeOk True, else False

        Parameters: mains is overall data-and-display structure.
        ttype is a tape-type id string -- a name or a nickname.
        '''
        tab, self.ro, self.tapeOk = mains.tab1, -1, False
        coN, coK = Table1.colName(), Table1.colNick()
        for ro in range(tab.rowCount()):
            if tab.item(ro,coN).text()==ttype or tab.item(ro,coK).text()==ttype:
                trow = Table1(tab,ro)
                self.ro   = ro
                self.rof  = rofrom
                self.tab  = trow
                self.wide = trow.getWide()
                self.high = trow.getHigh()
                self.oh1  = trow.getOh1()
                self.oho  = trow.getOho()
                self.oh1a  = trow.getOh1a()
                self.ohoa  = trow.getOhoa()
                self.tapeOk = True
                return
        # Raise an exception if tape type wasn't found.
        raise ValueError('Tape type `{}` not found, or no * selected.'.format(ttype))
#--------------------------------------------------
def getTapeDataList(mains):
    '''Make list of TapeData objects, corresponding to tape types found in
    both Table3 and Table1.  Not-found types are silently elided.
    Parameter mains is top level of data/display structure.
    '''
    tab3 = mains.tab3
    typeCol = Table3.colTtype()
    # Make array of tape data
    tapes = []
    nro = tab3.rowCount()
    for ro in range(nro):
        try:
            td = TapeData(mains, tab3.item(ro,typeCol).text(), ro)
            if td.tapeOk:
                tapes.append(td)
        except ValueError:
            pass
    return tapes
#--------------------------------------------------
# Recompute and display volumes of parts    
def calcVols(mains):
    try:
        nr4  = mains.tab4.rowCount() # See if tab4 has been built yet
    except:  # Can't calc before tables are built
        return
    # Find selected specification (the marked row in table 2)
    tab1, tab2, tab3 = mains.tab1, mains.tab2, mains.tab3
    if tab2.radioRo < 0:
        print ('Problem:  No Marked Row Found in Table 2')
        return
    s2 = Table2(tab2, tab2.radioRo)
    nro  = tab3.rowCount()
    vols = ['']*nro
    tapes = getTapeDataList(mains)
    if not tapes: return
    sl = tapes[0]               # Get first-row accessors
    for sr in tapes[1:]:        # Get next-row accessors
        legHi = max(sl.high, sr.high)
        caplen = s2.getCapLen()
        # Approx cap volume: rounded corners not accounted for,
        # maybe ok, but not ok is setback not accounted for
        CapVol = max(0, s2.getCapWide() * caplen * s2.getCapThik())
        # Approx 2-legs volume: half-rounds at ends not accounted for.
        LegVol = max(0, 2 * (caplen - 2*s2.getPadLen()) * legHi * s2.getLegThik())
        # Approx volume of posts & bridges:  bridges not included.
        postArea = 3.14 * (s2.getPostOD()**2 - s2.getPostID()**2)/4.
        PilVol = max(0, s2.getPosts() * legHi * postArea)
        # Compute total approx volume, converting mm^3 to mL
        evol = '{:1.2f}'.format((CapVol+LegVol+PilVol)/1000) # 1000 mm^3 per mL
        # Put computed value in list
        vols[sr.rof] = evol
        sl = sr
    # Push computed values into table
    vols[0] = '(ml)'
    for ro in range(nro):
        Table3(tab3, ro).putVolRO(vols[ro])
#--------------------------------------------------
def makeBridges(rail, span):
    BridgeN      = rail.Bridges
    BridgeOffset = rail.BridgeOffset
    BridgeWide   = rail.BridgeWide
    BridgeStep   = (rail.CapLen-2*rail.BridgeOffset)/max(1,BridgeN-1)
    CapWide      = rail.CapWide
    asm = None
    proto = cube([BridgeWide, span, rail.CapThik])
    proto = back(span-CapWide)(proto)
    for k in range(BridgeN):
        b = right(BridgeOffset+k*BridgeStep-BridgeWide/2)(proto)
        asm = b + asm if asm else b
    return color(Cyan)(asm) if asm else None
#--------------------------------------------------
def makeTube(idi, odi, hi, transl, half, eps):
    '''Make a tube or half-tube.  idi, odi = inner and outer diameters;
    hi= height; transl = [x,y,z] translation vector; half = whole or
    half indicator: -1=right half, 0=whole, +1=left half.
    '''
    loss = cylinder(d=idi, h=hi+2*eps)
    tube = cylinder(d=odi, h=hi) - hole()(down(eps)(loss))
    if half:
        block = cube([odi/2, odi+2*eps, hi+2*eps])
        dx = -(odi+eps)/2 if half < 0 else 0
        tube -= translate([dx, -(eps+odi)/2,0])(block)
    return translate(transl)(tube)
#--------------------------------------------------
def rampBar(leng, wide, high, transl):
    '''Return a bar of specified length, width, height, except with ends
    ramping up at 45 degrees at one end, -45 at other, in a plane
    rotated about y axis.  Parameters: leng, wide, high give x,y,z
    sizes.  transl = 3-vector with x,y,z distances to translate the
    origin-corner of the bar.
    '''
    s2 = sqrt(2)
    cu = cube([leng, wide, high])
    box = rotate(a=[0,-45,0])(back(wide)((cube([s2*high, 3*wide, s2*high]))))
    return translate(transl)(cu-box-right(leng)(box))
#--------------------------------------------------
def rampSide(leng, wide, high, transl, rotat):
    '''Return a bar of specified length, width, height, except with ends
    ramping at 45 degrees at one end, -45 at other.  Is like a rampBar
    rotated +/- 90 degrees about the x axis.  Parameters: First four as
    for rampBar.  rotat: +/- 90 for amount of rotation about the x axis.   
    '''
    # x-axis rotate below exchanges hi, wide - next two lines compensate.
    tcorr = [0,0,-wide] if rotat>0 else [0,-high,0]
    s = rotate([rotat,0,0])(rampBar(leng, high, wide, tcorr))
    return translate(transl)(s)
#--------------------------------------------------
def cappedCube(leng, wide, hi, transl):
    '''Make a rectangular bar of specified size, then add half-rounds to
    each end.  Resulting length = leng+wide.  Parameters: leng, wide,
    high give x,y,z sizes.  transl = 3-vector with x,y,z distances to
    translate the origin-corner of the rectangular bar.
    '''
    cu = cube([leng, wide, hi])
    ci = forward(wide/2)(cylinder(d=wide, h=hi))
    return translate(transl)(cu + ci + right(leng)(ci))
#--------------------------------------------------
def makeLegs(rail, tapeA, tapeB, maxHi, oLegs, oRamps): 
    '''Make legs based on specs in params - overall x size from rail, y
    overhang sizes from tapeA & B, z heights from maxHi and from tapeA
    & B heights.  Add filler along rail when maxHi > A or B heights:
    maxHi is the highest clearance for any of the tapes used in the
    whole assembly.  When this exceeds (eg) tapeA.high, filler strips
    are needed to thicken the edge of the cap so clearance is reduced
    to tapeA.high instead of maxHi.

    '''   
    eps     = rail.eps
    CapLen  = rail.CapLen
    EndLen  = rail.EndLen
    PadLen  = rail.PadLen
    CapWide = rail.CapWide
    CapThik = rail.CapThik
    LegThik = rail.LegThik
    LegSepO = CapWide - tapeA.oho - tapeB.oh1
    LegSepI = LegSepO - 2*LegThik
    overEnd = 2*PadLen + LegSepO
    LegLen  = CapLen - overEnd
    
    barx  = (CapLen-LegLen-LegSepO)/2
    barz  = CapThik-eps*1.1
    chanA = rampBar(LegLen+LegSepO, tapeA.oho, maxHi-tapeA.high+eps, [barx, 0, barz])
    chanB = rampBar(LegLen+LegSepO, tapeB.oh1, maxHi-tapeB.high+eps, [barx, CapWide-tapeB.oh1, barz])
    legOut  = cappedCube(LegLen, LegSepO, maxHi+eps,   [overEnd/2, tapeA.oho,         CapThik-eps/2])
    legIn   = cappedCube(LegLen, LegSepI, maxHi+2*eps, [overEnd/2, tapeA.oho+LegThik, CapThik-eps/2])

    cutLen = CapLen - 2*EndLen
    cutR = rampSide(cutLen, tapeA.oho-tapeA.ohoa+eps, maxHi+CapThik+eps, [EndLen, tapeA.ohoa-eps/2, -eps/2], -90)
    cutL = rampSide(cutLen, tapeB.oh1-tapeB.oh1a+eps, maxHi+CapThik+eps, [EndLen, CapWide+tapeB.oh1a-tapeB.oh1-eps/2, -eps/2], 90)
    if oLegs:
        lera = legOut-legIn+chanA+chanB if oRamps else legOut-legIn
    else:
        lera = chanA+chanB if oRamps else None
    if lera: lera = color(Green)(lera)
    return lera, color(Red)(cutR)+color(Magenta)(cutL)
#--------------------------------------------------
def makeUnit(rail, tapeA, tapeB, maxHi):
    '''Make a unit based on rail length-and-width specs in rail, and tape
    specs in tapeA, tapeB.'''
    oEnds, oLegs, oPosts, oRamps = (c in rail.Output for c in 'ELPR')
    eps     = rail.eps
    EndLen  = rail.EndLen
    CapLen  = rail.CapLen
    CapWide = rail.CapWide
    CapThik = rail.CapThik
    PostStep   = (CapLen-2*rail.PostOffset)/max(1,rail.nPosts-1)
    if oEnds:
        cap = cappedCube(CapLen-CapWide, CapWide, CapThik,[CapWide/2,0,0])
    else:
        cap = cube([CapLen, CapWide, CapThik])
    legs, cutout = makeLegs(rail, tapeA, tapeB, maxHi, oLegs, oRamps)
    asm = cap + legs - cutout if legs else cap
    px = rail.PostOffset
    if oPosts:
        for pn in range(rail.nPosts):          # Add set of posts
            asm += makeTube(rail.PostID, rail.PostOD, CapThik+maxHi, [px, rail.CapWide/2, 0], 0, rail.eps)
            px  += PostStep
    return asm
#--------------------------------------------------
def produceOutput(mains):
    eps = 0.02   # eps is mostly for clearing display sheen
    rail = RailData(mains, eps)
    tapes = getTapeDataList(mains)
    # Find max leg height, and span across all units
    maxHi = 0
    unwide = tapes[0].wide + tapes[-1].wide + 2*rail.Slack
    span = -rail.CapWide - unwide - tapes[0].oho - tapes[-1].oh1
    for tt in tapes:
        maxHi = max(maxHi, tt.high)
        span += rail.CapWide + tt.wide + rail.Slack - tt.oh1 - tt.oho
    print ('Span across {} units is {:<0.2f}'.format(len(tapes)-1, span))

    # Make bridges
    bridgeAsm = makeBridges(rail, span)
    
    asm = None
    sideA = tapes[0]
    for sideB in tapes[1:]:
        c = makeUnit(rail, sideA, sideB, maxHi)
        openChan = sideA.wide + rail.Slack - sideA.oh1 - sideA.oho
        asm = (c + back(rail.CapWide+openChan)(asm)) if asm else c
        sideA = sideB
    if bridgeAsm:
        asm += bridgeAsm
    cylSegments = 44
    cylSet_fn = '$fn = {};'.format(cylSegments)
    asmFile = 'channel-asm{}.scad'.format(version)
    scad_render_to_file(asm, asmFile, file_header=cylSet_fn, include_orig_code=False)
    print ('Wrote scad code to {}'.format(asmFile))
#--------------------------------------------------
if __name__ == '__main__':
    version = 4    
    print ('Program:  Make SMD Channels with Qt & SolidPython.  jiw - Feb 2019')
    # Link callbacks to volume-updater and scad-output routines
    CallData.setProducers([calcVols, produceOutput])
    # Load up .xml and run the app
    loadAndShow()
