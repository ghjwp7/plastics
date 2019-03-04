#!/usr/bin/env python

# jiw 26 Feb 2019 - Using SolidPython to gen OpenSCAD code for
# SMD-tape channels, for pick-and-place operations -- with specs
# picked up from QtTableWidget application

from PyQt5.QtCore import Qt
from solid import color, cube, cylinder, rotate
from solid import hole, part, scad_render_to_file, scale, translate
from solid.screw_thread import thread, default_thread_section
from solid.utils import up, down, left, right, forward, back, Cyan, Green, Red
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
        self.Bridges     = rtab.getBridges()
        self.BridgeOffset= rtab.getBridgeOffset()
        self.BridgeWide  = rtab.getBridgeWide()
        self.eps         = eps
        self.railOk = True
#-------------------------------------------------- 
class TapeData:                 # Specs for one tape-type
    '''Get data for one tape type from tapes table, and put into a
    TapeData object.'''
    def __init__(self, mains, ttype):
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
                self.tab  = trow
                self.wide = trow.getWide()
                self.high = trow.getHigh()
                self.oh1  = trow.getOh1()
                self.oho  = trow.getOho()
                self.tapeOk = True
                return
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
    ul   = Table3(tab3, 0)        # Get first-row accessors
    for ro3 in range(1,nro):
        ur = Table3(tab3, ro3)    # Get next-row accessors
        ulT, urT = ul.getTtype(), ur.getTtype() # L-side and R-side tape types
        sl, sr = TapeData(mains, ulT), TapeData(mains, urT) # Locate types, get data
        if not (sl.tapeOk and sr.tapeOk): # Were both tape types found?
            print ('TType {} or {} * Not Found'.format(ulT, urT))
            ur.putVolRO('-0')   # Indicate bad vol calc
            continue
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
        # Push computed value into table
        ur.putVolRO(evol)
        ul = ur
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
def makeLegs(rail, tapeA, tapeB, maxHi): 
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
    
    def channelBar(leng, wide, hi, transl):
        cu = cube([leng, wide, hi])
        m = 2*max(wide, maxHi)
        box = translate([0, -m/3, m/2])(rotate(a=[0,45,0])(cube([m,m,m])))
        l = right(leng-m/2)(box)
        r = left(0.8*m)(box)        
        return translate(transl)(cu-r-l)
        #return translate(transl)(r+l)
    def cappedCube(leng, wide, hi, transl):
        cu = cube([leng, wide, hi])
        ci = forward(wide/2)(cylinder(d=wide, h=hi))
        return translate(transl)(cu + ci + right(leng)(ci))
   
    barx  = (CapLen-LegLen-LegSepO)/2
    barz  = CapThik-eps*1.1
    chanA = channelBar(LegLen+LegSepO, tapeA.oho, maxHi-tapeA.high+eps, [barx, 0, barz])
    chanB = channelBar(LegLen+LegSepO, tapeB.oh1, maxHi-tapeB.high+eps, [barx, CapWide-tapeB.oh1, barz])
    legOut  = cappedCube(LegLen, LegSepO, maxHi+eps,   [overEnd/2, tapeA.oho,         CapThik-eps/2])
    legIn   = cappedCube(LegLen, LegSepI, maxHi+2*eps, [overEnd/2, tapeA.oho+LegThik, CapThik-eps/2])
    return legOut-legIn+chanA+chanB
#--------------------------------------------------
def makeUnit(rail, tapeA, tapeB, maxHi):
    '''Make a unit based on rail length-and-width specs in rail, and tape
    specs in tapeA, tapeB.'''
    eps     = rail.eps
    EndLen  = rail.EndLen
    CapLen  = rail.CapLen
    CapWide = rail.CapWide
    CapThik = rail.CapThik
    PostStep   = (CapLen-2*rail.PostOffset)/max(1,rail.nPosts-1)
    cap = cube([CapLen, CapWide, CapThik])
    legs = makeLegs(rail, tapeA, tapeB, maxHi)
    asm = cap + color(Green)(legs)
    px = rail.PostOffset
    for pn in range(rail.nPosts):          # Add set of posts
        asm += makeTube(rail.PostID, rail.PostOD, maxHi, [px, rail.CapWide/2, 0], 0, rail.eps)
        px  += PostStep
    return asm
#--------------------------------------------------
def produceOutput(mains):
    eps = 0.02   # eps is mostly for clearing display sheen
    rail = RailData(mains, eps)
    # Find max leg height
    tab3 = mains.tab3
    typeCol = Table3.colTtype()
    # Make array of tape data
    tapes = []
    for ro in range(tab3.rowCount()):
        tapes.append(TapeData(mains, tab3.item(ro,typeCol).text()))

    # Find max leg height, and span across all units
    maxHi = 0
    span = -rail.CapWide - tapes[0].wide - tapes[-1].wide - tapes[0].oho - tapes[-1].oh1
    for tt in tapes:
        maxHi = max(maxHi, tt.high)
        span += rail.CapWide + tt.wide - tt.oh1 - tt.oho
    print ('Span across {} units is {:<0.2f}'.format(len(tapes)-1, span))

    # Make bridges
    bridgeAsm = makeBridges(rail, span)
    
    asm = None
    sideA = tapes[0]
    for sideB in tapes[1:]:
        c = makeUnit(rail, sideA, sideB, maxHi)
        # need to change 2 in next line to tape-width
        chanDel = sideA.wide-sideA.oh1-sideA.oho
        asm = (c + back(rail.CapWide+chanDel)(asm)) if asm else c
        sideA = sideB
    if bridgeAsm:
        asm += bridgeAsm
    cylSegments = 60
    cylSet_fn = '$fn = {};'.format(cylSegments)
    asmFile = 'channel-asm{}.scad'.format(version)
    scad_render_to_file(asm, asmFile, file_header=cylSet_fn, include_orig_code=False)
    print ('Wrote scad code to {}'.format(asmFile))
#--------------------------------------------------
if __name__ == '__main__':
    version = 4    
    print 'Program:  Make SMD Channels with Qt & SolidPython.  jiw - Feb 2019'
    # Link callbacks to volume-updater and scad-output routines
    CallData.setProducers([calcVols, produceOutput])
    # Load up .xml and run the app
    loadAndShow()
