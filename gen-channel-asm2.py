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
    def __init__(self, ChanWide, ChanHi, ChanHang):
        self.ChanWide, self.ChanHi, self.ChanHang = ChanWide, ChanHi, ChanHang

class RailModel:
    def __init__(self, PillarOD, PillarID, PillarSep, LegThik, CapThik, CapWide, eps):
        self.PillarOD  = PillarOD
        self.PillarID  = PillarID
        self.PillarSep = PillarSep
        self.LegThik   = LegThik
        self.CapThik   = CapThik
        self.CapWide   = CapWide
        self.eps       = eps
        
# Specs-holder for channel-rail
class ChannelRail(RailModel, ChannelSpec):
    def __init__(self, Rail, Chan):
        self.PillarOD  = Rail.PillarOD
        self.PillarID  = Rail.PillarID
        self.PillarSep = Rail.PillarSep
        self.LegThik   = Rail.LegThik
        self.CapThik   = Rail.CapThik
        self.CapWide   = Rail.CapWide
        self.eps       = Rail.eps
        self.ChanWide  = Chan.ChanWide
        self.ChanHi    = Chan.ChanHi
        self.ChanHang  = Chan.ChanHang
    
    def makePillar(self, xloc):
        tHi = self.ChanHi + self.CapThik
        loss = cylinder(d=self.PillarID, h=tHi+2*self.eps)
        tube = cylinder(d=self.PillarOD, h=tHi) - hole()(down(self.eps)(loss))
        return translate([xloc, self.CapWide/2, 0])(tube)

    def makeRail(self, length, post1):
        cap = cube([length, self.CapWide, self.CapThik])
        leg = up(self.CapThik)(cube([length, self.LegThik, self.ChanHi + self.eps]))
        asm = cap + forward(self.ChanHang)(leg) + forward(self.CapWide-self.ChanHang)(leg)
        px = post1
        while px < length:
            asm += self.makePillar(px)
            px  += self.PillarSep
        return asm

def makeChannelSpecs():
    return {
        'Resistor': ChannelSpec(0.312, 0.04, 0.09),
        'SS14':     ChannelSpec(0.500, 0.11, 0.13),
        'TSOP8':    ChannelSpec(0.500, 0.09, 0.13),
        'TSOP16':   ChannelSpec(0.650, 0.09, 0.15),
        'inductor': ChannelSpec(0.650, 0.24, 0.15) }

def makeModelRail():
    PillarOD, PillarID, PillarSep = 0.21, 0.11, 1.25
    LegThik, CapThik, CapWide, eps = 0.05, 0.05, 0.75, 1e-4
    return RailModel(PillarOD, PillarID, PillarSep, LegThik, CapThik, CapWide, eps)

def makeChannels(railModel, chanNames, length, post1):
    asm = None
    for cname in chanNames:
        crail = ChannelRail(railModel, channelSpecs[cname])
        c = crail.makeRail(length, post1)
        asm = (c + forward(railModel.CapWide+.1)(asm)) if asm else c
    return asm

def makeCrossbar(railModel, chanNames, barThik, barWidth, nBars):
    eps   = railModel.eps
    capW  = railModel.CapWide
    holeD = railModel.PillarID
    specs = [channelSpecs[cname] for cname in chanNames]
    skips = [spec.ChanWide - 2*spec.ChanHang for spec in specs]
    barLen = sum([capW + skip for skip in skips])
    bar = cube([barLen, barWidth, barThik])
    holeAt = capW/2
    for skip in skips:
        bar += hole()(translate([holeAt,barWidth/2,-eps])(cylinder(d=holeD, h=barThik+2*eps)))
        holeAt += capW + skip
    asm = None
    for line in range(nBars):
        asm = back(barWidth+.1)(bar + asm if asm else bar)
    return asm


if __name__ == '__main__':
    channelSpecs = makeChannelSpecs()
    modelRail = makeModelRail()
    sf = 25.4
    nPosts, post1x = 2, 0.5
    barThik, barWidth, nBars = 0.06, 0.4, nPosts
    chanNames = ['Resistor', 'SS14', 'inductor']
    asm  = scale((sf, sf, sf))(makeChannels(modelRail, chanNames, nPosts, post1x))
    asm += scale((sf, sf, sf))(makeCrossbar(modelRail, chanNames, barThik, barWidth, nBars))
    cylSegments, version = 60, 2
    cylSet_fn = '$fn = {};'.format(cylSegments)
    asmFile = 'channel-asm{}.scad'.format(version)
    scad_render_to_file(asm, asmFile, file_header=cylSet_fn, include_orig_code=False)
    print ('Wrote scad code to {}'.format(asmFile))

