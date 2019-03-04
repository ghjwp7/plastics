#!/usr/bin/env python

# Define class CallData with application-specific callback routines
# and data, for use in loadTablesForXML module.  By jiw 28 Feb 2019

import sys
from PyQt5.QtWidgets   import QFileDialog
from ChannelVars       import Table1, Table2, Table3, Table4
class CallData:
    '''1. Provide methods to make callback closures, to be called by
    loadTablesForXML when it is building tables.  2. Manage a list of
    `producer` functions, which call app routines depending on
    conditions seen in callback code.  3. Provide incidental data such
    as button titles

    A producer receives form data and outputs produced results.  For
    example, calcVols receives mains data, and outputs computed
    volumes to display.

    This class is more of a namespace than an object design -- all of
    its methods so far are marked @classmethod or @staticmethod.
    '''
    def __init__(self):
        pass
    autoProduce = False
    @classmethod
    def setProducers(c, producer_list):
        c.producer_funcs = producer_list
    @classmethod
    def producer(c, k):      return c.producer_funcs[k]
    @classmethod
    def calcVols(c, mains):  return c.producer_funcs[0](mains)
    @classmethod
    def produceOutput(c, mains): return c.producer_funcs[1](mains)
    
    @staticmethod
    def buttonLabels():      return ['Quit', 'Save', 'Produce', 'AutoProd'] #, 'Load'
    @staticmethod
    def tableNames():        return ['tapetypes', 'railspecs', 'unitlist', 'instructions']
    
    # The next four functions make closures (encapsulations of values
    # existing at time of function creation) so that on_X callback
    # routines get data corresponding to whichever item is having an X
    # event.

    @classmethod
    def makeChangeFunc(c, mains, tab):
        return lambda ro,co: c.on_cellChange(mains, tab, ro,co)
    
    @classmethod
    def makeSelectFunc(c, mains, tabN):
        return lambda: c.on_Selects(mains, tabN)
    
    @classmethod
    def makeClickFunc(c, etree, mains, bu,bun):
        return lambda x: c.on_buttonClick(etree, mains, bu, bun)
    
    @classmethod
    def makeToggleFunc(c, mains, tab, ro,co):
        return lambda state: c.on_toggle(mains, tab, ro,co,state)

    #---------------------------------------------
    @classmethod
    def on_cellChange(c, mains, tab, ro, co):
        '''Handle cell-contents-changed events for loadTablesForXML.  User
        code in this routine should use supplied table, row, and column
        values to select appropriate code for execution.

        Params: mains = Top level of display structure
        tab = table in which selection changed
        ro = Row number of cell whose contents changed
        co = Col number of cell whose contents changed    
        '''
        #print ('Cell {},{} in tab{} changed to {}'.format(ro,co,tabN,tab.item(ro,co).text()))
        # Don't re-calc when calcVols changes Vol entries
        if tab.tabCue != 'makes' or co != Table3.colVolRO():
            c.calcVols(mains)
            if c.autoProduce:
                c.produceOutput(mains)
    #---------------------------------------------
    @classmethod
    def on_Selects(c, mains, tabN):
        '''Handle selections-changed events for loadTablesForXML.  User code
        in this routine should use supplied values to select appropriate
        code for execution.

        Params: mains = Top level of display structure
        tabN = id-character of table in which selection changed
        '''
        pass            
    #---------------------------------------------
    @staticmethod
    def saveXML(etree, mains):
        stuff = QFileDialog.getSaveFileName(mains, 'Save File')
        name = str(stuff[0])

        # Copy data out of mains back into etree
        eTabs = etree.findall('table')
        mTabs  = [mains.tab1, mains.tab2, mains.tab3, mains.tab4 ]
        mClass = [Table1, Table2, Table3, Table4]
        for et, mt, mc in zip(eTabs, mTabs, mClass):
            #print '{}  {}'.format(et, et.items())
            for ro, ero in enumerate(et.findall('row')):
                #print '  {}  {}'.format(ero, ero.items())
                for co, mk in enumerate(mc.colCues()):
                    if mc.colFmts()[co]=='r':
                        mv = '*' if mt.cellWidget(ro,co).isChecked() else ''
                    else:
                        mv = mt.item(ro,co).text() # Get value from table
                    #print 'Copy t{} {},{}  {}'.format(mc.tabN(),ro,co,mv)
                    ero.set(mk, mv) # Copy table's value into etree 

        print ('\nWriting tables to file:\n    {}'.format(name))
        print ('It can be reloaded by:\n')
        print ('    ./smd-channelsProduce.py {}\n'.format(name))
        with open(name,'w') as fo:
            etree.write(fo, encoding="UTF-8")
    #---------------------------------------------
    @classmethod
    def on_buttonClick(c, etree, mains, bu, bun):
        '''Handle buttons like 'Quit','Save','Load','Produce'

        Params: mains = Top level of display structure
        bu  = button object of button that was clicked
        bun = button number of button that was clicked
        '''
        bt = c.buttonLabels()[bun]
        if bt=='Quit':       sys.exit()
        elif bt=='Produce':  c.produceOutput(mains)
        elif bt=='Save':     c.saveXML(etree, mains)
        elif bt=='AutoProd': c.autoProduce = not c.autoProduce
        else:
            print ('B{} {} {} click'.format(bun, bt, bu.text()))
    #---------------------------------------------
    @classmethod
    def on_toggle(c, mains, tab, ro, co, state):
        if state:
            tab.radioRo, tab.radioCo = ro, co
            c.on_cellChange(mains, tab, ro, co)
    #---------------------------------------------
