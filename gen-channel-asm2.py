#!/usr/bin/env python

# jiw 6 Jan 2019 - Using SolidPython to gen OpenSCAD code for
# SMD-tape channels, for pick-and-place operations

# When modifying this code:
# (a) At outset (ie once only), at command prompt say:
#           PP=channel-asm2;  SCF=$PP.scad;  PYF=gen-$PP.py
#           STF=$PP.stl; exec-on-change $PYF "python $PYF" &
#           echo $PYF, $SCF, $STF;  openscad $SCF &
# (b) After changes that you want to see the effect of, save $PYF.
# (c) In openscad, press F6 to render details, then Export, as STL.
# (d) Say `craftware $STF &` then slice it and save gcode

from solid import cube, cylinder, hole, part, scad_render_to_file, scale, translate
from solid.screw_thread import thread, default_thread_section
from solid.utils import up, down, left, right, forward, back

# Specs-holder for channel height, width, and overhang
class ChannelSpec:
    def __init__(self, ChanWide, ChanHi, ChanHang1, ChanHang2):
        # Channel specs are in millimeters!
        def mi(mm): return mm/25.4
        self.ChanWide  = mi(ChanWide)
        self.ChanHi    = mi(ChanHi)
        self.ChanHang1 = mi(ChanHang1)
        self.ChanHang2 = mi(ChanHang2)

class RailModel:
    def __init__(self, railLen, nPosts, Pillar1, PillarSep, PillarOD, PillarID, LegThik, CapThik, CapWide, eps):
        self.RailLen   = railLen
        self.nPosts    = nPosts
        self.Pillar1   = Pillar1  
        self.PillarSep = PillarSep 
        self.PillarOD  = PillarOD
        self.PillarID  = PillarID
        self.LegThik   = LegThik
        self.CapThik   = CapThik
        self.CapWide   = CapWide
        self.eps       = eps
        
# Specs-holder for channel-rail
class ChannelRail(RailModel, ChannelSpec):
    def __init__(self, Rail, Chan):
        self.RailLen   = Rail.RailLen
        self.nPosts    = Rail.nPosts
        self.Pillar1   = Rail.Pillar1  
        self.PillarOD  = Rail.PillarOD
        self.PillarID  = Rail.PillarID
        self.PillarSep = Rail.PillarSep
        self.LegThik   = Rail.LegThik
        self.CapThik   = Rail.CapThik
        self.CapWide   = Rail.CapWide
        self.eps       = Rail.eps
        self.ChanWide  = Chan.ChanWide
        self.ChanHi    = Chan.ChanHi
        self.ChanHang1  = Chan.ChanHang1
        self.ChanHang2  = Chan.ChanHang2
    
    def makePillar(self, xloc):
        tHi = self.ChanHi + self.CapThik
        loss = cylinder(d=self.PillarID, h=tHi+2*self.eps)
        tube = cylinder(d=self.PillarOD, h=tHi) - hole()(down(self.eps)(loss))
        return translate([xloc, self.CapWide/2, 0])(tube)

    def makeRail(self):
        length = self.RailLen
        cap = cube([length, self.CapWide, self.CapThik])
        leg = up(self.CapThik)(cube([length, self.LegThik, self.ChanHi + self.eps]))
        asm = cap + forward(self.ChanHang1)(leg) + forward(self.CapWide-self.ChanHang2-self.LegThik)(leg)
        px = self.Pillar1
        while px < length:
            asm += self.makePillar(px)
            px  += self.PillarSep
        return asm

def makeChannelSpecs():
    return {        # Channel specs are in millimeters!
         #          channel  width, height, overhangs left and right
        'Resistor': ChannelSpec(8,    1,     3.5,   0.8),  
        'SS14':     ChannelSpec(12,   3,     3.8,   0.8),  
        'TSOP8':    ChannelSpec(12,   2.5,   3.8,   0.8),  
        'TSOP16':   ChannelSpec(16,   2.5,   3.8,   0.8),  
        'TQFP32A':  ChannelSpec(16,   2,     4,     1.5),  
        'tantCap':  ChannelSpec(12,   3.5,   3.3,   0.8),  
        'inductor': ChannelSpec(16,   6,     3.8,   0.8) }

def makeModelRail(railLen, nPosts, pillar1, pillarSep):
    PillarOD, PillarID = 0.21, 0.11
    LegThik, CapThik, CapWide, eps = 0.05, 0.05, 0.75, 2e-4
    return RailModel(railLen, nPosts, pillar1, pillarSep, PillarOD, PillarID, LegThik, CapThik, CapWide, eps)

def makeChannels(railModel, chanNames):
    asm = None
    for cname in chanNames:
        crail = ChannelRail(railModel, channelSpecs[cname])
        c = crail.makeRail()
        asm = (c + forward(railModel.CapWide+.1)(asm)) if asm else c
    return asm

def makeCrossbar(railModel, chanNames, barThik, barWidth, nBars):
    eps   = railModel.eps
    capW  = railModel.CapWide
    holeD = railModel.PillarID
    specs = [channelSpecs[cname] for cname in chanNames]
    skips = [spec.ChanWide - spec.ChanHang1 - spec.ChanHang2 for spec in specs]
    barLen = sum([capW + skip for skip in skips])
    bar = cube([barWidth, barLen, barThik])
    holeAt = capW/2
    for skip in skips:
        bar += hole()(translate([barWidth/2,holeAt,-eps])(cylinder(d=holeD, h=barThik+2*eps)))
        holeAt += capW + skip
    asm = None
    for line in range(nBars):
        asm = left(barWidth+.1)(bar + asm if asm else bar)
    return asm


if __name__ == '__main__':
    channelSpecs = makeChannelSpecs()
    railLen = 1.0
    nPosts = 2
    postSep = railLen/nPosts
    post1x = postSep/2
    modelRail = makeModelRail(railLen, nPosts, post1x, postSep)
    sf = 25.4
    barThik, barWidth, nBars = 0.06, 0.4, nPosts
    chanNames = ['Resistor','Resistor', 'SS14','SS14', 'TSOP16','TSOP16', 'inductor']
    chanNames = ['Resistor', 'Resistor', 'SS14', 'TSOP16']
    asm  = scale((sf, sf, sf))(makeChannels(modelRail, chanNames))
    asm += scale((sf, sf, sf))(makeCrossbar(modelRail, chanNames, barThik, barWidth, nBars))
    cylSegments, version = 60, 2
    cylSet_fn = '$fn = {};'.format(cylSegments)
    asmFile = 'channel-asm{}.scad'.format(version)
    scad_render_to_file(asm, asmFile, file_header=cylSet_fn, include_orig_code=False)
    print ('Wrote scad code to {}'.format(asmFile))

