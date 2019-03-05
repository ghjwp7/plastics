#!/usr/bin/env python

# Utility code by jiw, 24 Feb 2018, to produce 
 
# Produce a module that defines classes of objects Table1, Table2,
# ... corresponding to table specified in a subject .xml file.  For
# each table x, extract column-heading keys from the .xml, and use
# those keys as names of Tablex class-instance variables.  Define some
# methods for each class, like getV(), putV(), colV(), for each V in
# the set of variables (columns) in table.

from xml.etree import ElementTree
from time import ctime
import sys
#---------------------------------------------
def ErrorExit(msg, fname):
    sys.stderr.write('\n*** {} {} ***\n'.format(msg, fname))
    sys.exit(0)

def colProcess(tabCue, tabNum, tabName, top, modo):
    colData = []
    for colEntry in top:
        col = colEntry.attrib.get('col',None)
        cue = colEntry.attrib.get('cue', None)
        fmt = colEntry.attrib.get('fmt',None)
        nam = colEntry.attrib.get('name',None)
        cid = cue[0].upper() + cue[1:] # Upper-case the first character of id
        colData.append((col,cid,cue,fmt,nam))
    colData = sorted(colData)
    colCids  = [e[1] for e in colData]
    colCues  = [e[2] for e in colData]
    colFmts  = [e[3] for e in colData]
    colNames = [e[4] for e in colData]

    modo.write('\nclass Table{}:  # Class: Accessors for a row of tab{} / {} / {}\n'.format(tabNum, tabNum, tabCue, tabName))
    modo.write('    def __init__(self,tab,ro):  self.tab, self.ro = tab, ro\n')
    modo.write("    ''' __init__ sets values of .tab and .ro variables'''\n")
    modo.write('    def row(self):              return self.ro\n')
    modo.write('    def setRow(self,ro):        self.ro = ro\n')
    modo.write('    def tab(self):              return self.tab\n')
    modo.write('    def setTab(self,ro):        self.tab = tab\n')
    modo.write('    @staticmethod\n')
    modo.write('    def tabN():                 return "{}"\n'.format(tabNum))
    modo.write('    @staticmethod\n')
    modo.write('    def tabCue():               return "{}"\n'.format(tabCue))
    modo.write('    @staticmethod\n')
    modo.write('    def tabName():              return "{}"\n'.format(tabName))
    modo.write('    @staticmethod\n')
    modo.write('    def colCids():              return {}\n'.format(colCids))
    modo.write('    @staticmethod\n')
    modo.write('    def colCues():              return {}\n'.format(colCues))
    modo.write('    @staticmethod\n')
    modo.write('    def colFmts():              return {}\n'.format(colFmts))
    modo.write('    @staticmethod\n')
    modo.write('    def colNames():             return {}\n'.format(colNames))
    modo.write('\n')
    
    for k, i in enumerate(colCids):
        fmt = colFmts[k]
        pre  = '' if fmt=='s' else 'xml_int(' if fmt=='i' else 'xml_float('
        post = '' if fmt=='s' else ')'
        modo.write('    def get{}(self):{:{wide}}return {}self.tab.item(self.ro,{}).text(){}\n'.format(i, '', pre, k, post, wide=max(1,14-len(i))))
        modo.write('    def put{}(self, v):{:{wide}}self.tab.item(self.ro,{}).setText(str(v))\n'.format(i, '',k, wide=max(1,11-len(i))))
        
    for k, i in enumerate(colCids):
        fmt = colFmts[k]
        if k>0:
            modo.write('    @staticmethod\n')
        else:
            modo.write('\n    @staticmethod          #    Column #   Format     Id           Column-name \n')
        modo.write('    def col{}():{:{wide}}return {:2}   #      {}     {:<14} {}\n'.format(i, '', k, fmt, i, colNames[k], wide=max(1,13-len(i))))

# Make module per columnData from XML tree
def makeModule(xmlFi, modFi, modo, etree):
    modo.write('# Module:  {}\n'.format(modFi))
    modo.write('# Get/Put variables for .xml file {}\n'.format(xmlFi))
    modo.write('# Generated {} by {}\n'.format(ctime(), __file__))
    modo.write('def xml_float(s):\n')
    modo.write('    try:\n')
    modo.write('        return float(s)\n')
    modo.write('    except ValueError:\n')
    modo.write('        return -1.\n')
    modo.write('def xml_int(s):\n')
    modo.write('    try:\n')
    modo.write('        return int(s)\n')
    modo.write('    except ValueError:\n')
    modo.write('        return -1\n')

    tabCues, tabNums, tabNames = [], [], []
    for kid in etree.getroot():
        if kid.tag == 'table':
            tabCue  = kid.attrib.get('cue', None)
            tabNum  = kid.attrib.get('tab', None)
            tabName = kid.attrib.get('name', None)
            if tabNum != None:
                for elt in kid:
                    if elt.tag=='columnData':
                        colProcess(tabCue, tabNum, tabName, elt, modo)
                tabCues.append(tabCue)
                tabNums.append(tabNum)
                tabNames.append(tabName)
    modo.write('\ndef tableCount():       return {}\n'.format(len(tabNums)))
    modo.write(  'def tableCues():        return {}\n'.format(tabCues))
    modo.write(  'def tableNums():        return {}\n'.format(tabNums))
    modo.write(  'def tableNames():       return {}\n'.format(tabNames))

def loadXMLData(specsFile):
    try:                            # Read script from file and parse it
        etree = ElementTree.parse(specsFile)
    except IOError:
        ErrorExit('IOError, check file or filename', specsFile)
    except ElementTree.ParseError:
        ErrorExit('ParseError, check XML validity in file', specsFile)
    except:                         # Some unknown error
        ErrorExit('Error while treating', specsFile)
    return etree

#--------------------------------------------------
if __name__ == '__main__':
    # Get params: name of data XML file, name of module
    xmlFi = sys.argv[1] if len(sys.argv)>1 else './smd-channels3.xml'
    modFi = sys.argv[2] if len(sys.argv)>2 else 'ChannelVars.py'
    modo  = open(modFi, 'w')
    etree = loadXMLData(xmlFi)      # Read .xml data into a tree structure
    makeModule(xmlFi, modFi, modo, etree)  # Make a module per .xml data
