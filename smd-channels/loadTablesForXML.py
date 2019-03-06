#!/usr/bin/env python

# Module to load & display editable tables (using xml.etree and Qt's
# QTableWidget) for use by other design code.  By jiw, 26 Feb 2018
# Ref: https://doc.qt.io/archives/qt-4.8/qtablewidget.html

# Table specifications and data appear in a .xml file, with name
# supplied by external calling program.  Tables are displayed in a
# QtSplitter widget.  (In a first prototypical application, tables are
# called Tape Data, Channel Specs, Units to Make, and Instructions,
# which work together to provide specs and measurements for producing
# SMD-parts-dispensing guide channels.)

# Program make-xml-accessors.py makes a variables-accessor module
# `ChannelVars`, [or use whatever other module name is preferred].
# Each cell V in a row of the displayed tables has corresponding colV,
# getV and putV methods defined in ChannelVars.py.

# When loadTablesPerXML loads tables from an xml file into memory,
# three methods from user-defined module `ChannelCallbacks` [or your
# own preferred name] will be set up as .connect() routines.  When
# their events occur, callbacks will receive values like (mains, tab,
# row#, col#, buttonname, buttonnumber.  The three methods are:
# on_cellChange(mains, tab,row#,col#), on_Selects(mains, tab), and
# on_buttonClick(mains, buttonname,buttonnumber).  Your
# `ChannelCallbacks` module should define those methods, with those
# arguments, to meet application requirements.  During callback
# handling, your code can access the main Qt widgets display structure
# from `tab` via mains or tab.mains, or can access a link to the jth
# table via mains.tab[j].  Note, functions for table ids and names
# appear at the end of ChannelVars module.

# After data is loaded and tables built by the routines in this
# module, your own code can add or remove other application-specific
# .connect() routines as necessary.

import re, sys
from ChannelVars       import Table1, Table2, Table3
from ChannelCallbacks  import CallData
from PyQt5             import QtWidgets
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QColor
from PyQt5.QtWidgets import QSplitter, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QHeaderView
from PyQt5.QtWidgets import QRadioButton
from xml.etree import ElementTree
#---------------------------------------------
def ErrorExit(msg, fname):
    sys.stderr.write('\n*** {} {} ***\n'.format(msg, fname))
    sys.exit(0)
#---------------------------------------------
def rowProcess(mains, tab, top, colNums, colFmts, colVals):
    rowdat = [v for v in colVals] # Copy default values
    attr = top.attrib
    colName, colNick = Table1.colName(), Table1.colNick()    
    for key in attr.keys():
        try:
            co = colNums[key]
            rowdat[co] = attr[key]
        except:
            print ('\n\tKey `{}` mistake?  Head keys are {}\n\tand row data is {}\n'.format(key, sorted(colNums.keys()),attr))
    # If 'nick' isn't set (is blank or None), copy name to nick.
    if tab.tabN == '1':
        print  colName, colNick, rowdat
        if not rowdat[colNick]:  rowdat[colNick] = rowdat[colName]
    # Insert next row into display structure
    ro = tab.rowCount();  tab.insertRow(ro)
    # Copy items from rowdat into new row
    for co, txt in enumerate(rowdat):
        if colFmts[co]=='r':
            bu = QRadioButton(tab)
            bu.toggled.connect(CallData.makeToggleFunc(mains, tab, ro,co))
            tab.setCellWidget(ro, co, bu)
            if txt:
                bu.setChecked(True)
                tab.radioRo, tab.radioCo = ro, co
            else:
                bu.setChecked(False)
        else:
            tab.setItem(ro, co, QTableWidgetItem(txt))
#---------------------------------------------
def colProcess(tab, top):
    cols = []
    for col in top:
        atts = [col.attrib.get(x,None) for x in ['col', 'cue', 'name', 'fmt', 'val', 'tip']]
        atts[-1] = re.sub(' +', ' ', atts[-1]) # tip
        cols.append(atts)

    cols = sorted(cols)
    # Return: colCues, colNames, colFmts, colVals, colTips
    return ([e[i] for e in cols] for i in range(1,6))
#---------------------------------------------
def makeTable(mains, tabN, tbase):
    #print ('Making table {}'.format(tabN))
    styleBlob, rowSet, tWide, tHi, tName, tCue = '', [], 100, 100, '?', '?'
    attr = tbase.attrib
    for key in attr.keys():
        if   key=='hpix': tHi   = int(attr[key])
        elif key=='wpix': tWide = int(attr[key])
        elif key=='name': tName = attr[key]
        elif key=='cue' : tCue   = attr[key]

    tab = None
    for elt in tbase:
        if elt.tag=='columnData':
            colCues, colNames, colFmts, colVals, colTips = colProcess(tab, elt)
            tab = QTableWidget(0, len(colNames), mains)
            tab.tabN = tabN
            tab.setHorizontalHeaderLabels(colNames)
            colOrder = {}
            for k, t in enumerate(colCues):
                colOrder[t] = k
                tab.horizontalHeaderItem(k).setToolTip(colTips[k])

    if tab==None:
        print ('Table {} not specified'.format(tabN))
        return (None,None)
    tab.tabName, tab.tabCue = tName, tCue
    
    # At some point, maybe should add if's to qualify which connects
    # to make.  For example, could have `con` or `connect` items in
    # column defs, and turn connects on or off for specific columns
    tab.setMinimumSize(tWide, tHi)
    tab.cellChanged.connect(CallData.makeChangeFunc(mains, tab))
    tab.itemSelectionChanged.connect(CallData.makeSelectFunc(mains, tabN))
    # Set radioR & radioCo to -1,-1 to show not-valid
    tab.tabN, tab.radioRo, tab.radioCo, tab.mains = tabN, -1,-1, mains 
    if   tabN=='1':  mains.tab1 = tab
    elif tabN=='2':  mains.tab2 = tab
    elif tabN=='3':  mains.tab3 = tab
    elif tabN=='4':  mains.tab4 = tab
    elif tabN=='5':  mains.tab5 = tab

    for elt in tbase:
        if elt.tag=='row':
            rowSet.append(rowProcess(mains, tab, elt, colOrder, colFmts, colVals))
        elif elt.tag=='style':
            styleBlob += elt.attrib.get('part',None)
    if styleBlob:
        tab.setStyleSheet(styleBlob)
    tab.resizeColumnsToContents()
#---------------------------------------------
def makeTables(mains, etree): # Make tables per data from XML tree
    for kid in etree.getroot():
        if kid.tag == 'table':
            tabN = kid.attrib.get('tab', None)
            if tabN != None:
                makeTable(mains, tabN, kid)
#---------------------------------------------
def loadData(specsFile):
    # Get param: name of data XML file
    try:                        # Read script from file and parse it
        etree = ElementTree.parse(specsFile)
    except IOError:
        ErrorExit('IOError, check file or filename', specsFile)
    except ElementTree.ParseError:
        ErrorExit('ParseError, check XML validity in file', specsFile)
    except:                     # Some unknown error
        ErrorExit('Error while treating', specsFile)
    return etree
#---------------------------------------------
def loadAndShow():
    app = QApplication(sys.argv)    # Create a Qt application, first thing
    mainpanes = QSplitter(Qt.Vertical)
    mainpanes.setWindowTitle('SMD channel design tables')
    specsFile = sys.argv[1] if len(sys.argv)>1 else './smd-channels3.xml'
    etree = loadData(specsFile)     # Get etree of data from .xml file

    styleBlob = '''
QHeaderView { background-color: darkgray; color: white; text-align: center; font-size:18px; }
QTableCornerButton { background-color: "pink"; gridline-color: "green"; } 
QTableWidget { font: bold 16pt; text-align: center; background-color:  #202800; color: "lightcyan"; }
QPushButton { min-width: "23"; font: bold 23pt Helvetica; background-color: orange; color: navy; }'''
    mainpanes.setStyleSheet(styleBlob)
    # Make pushbuttons
    PBNames = CallData.buttonLabels()
    wib, hib, mb = 180, 75, 14
    tab0 = QWidget(mainpanes)
    tab0.setMinimumSize(len(PBNames)*(mb+wib), hib+2*mb)
    for k, txt in enumerate(PBNames):
        u = QPushButton(txt, tab0)
        u.move(mb+(mb+wib)*k, mb)
        u.resize(wib, hib)
        u.clicked.connect(CallData.makeClickFunc(etree, mainpanes, u, k))

    mainpanes.tab1 = mainpanes.tab2 = mainpanes.tab3 = mainpanes.tab4 = None
    makeTables(mainpanes, etree)    # Make tables per .xml data
    CallData.calcVols(mainpanes)    # Update volumes-of-parts cells
    mainpanes.show()                # Show the window
    app.exec_()                     # Run the app
