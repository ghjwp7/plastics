# Module:  ChannelVars.py
# Get/Put variables for .xml file ./smd-channels3.xml
# Generated Wed Mar  6 15:38:58 2019 by ./make-xml-accessors.py
def xml_float(s):
    try:
        return float(s)
    except ValueError:
        return -1.
def xml_int(s):
    try:
        return int(s)
    except ValueError:
        return -1

class Table1:  # Class: Accessors for a row of tab1 / tapes / Tape Data
    def __init__(self,tab,ro):  self.tab, self.ro = tab, ro
    ''' __init__ sets values of .tab and .ro variables'''
    def row(self):              return self.ro
    def setRow(self,ro):        self.ro = ro
    def tab(self):              return self.tab
    def setTab(self,ro):        self.tab = tab
    @staticmethod
    def tabN():                 return "1"
    @staticmethod
    def tabCue():               return "tapes"
    @staticmethod
    def tabName():              return "Tape Data"
    @staticmethod
    def colCids():              return ['Name', 'Nick', 'Wide', 'High', 'Oh1', 'Oho', 'Oh1a', 'Ohoa']
    @staticmethod
    def colCues():              return ['name', 'nick', 'wide', 'high', 'oh1', 'oho', 'oh1a', 'ohoa']
    @staticmethod
    def colFmts():              return ['s', 's', 'f', 'f', 'f', 'f', 'f', 'f']
    @staticmethod
    def colNames():             return ['Tape Type', 'nickname', 'Tape Width', 'Tape High', 'Overhang1', 'Overhang2', 'Over.1 alt', 'Over.2 alt']

    def getName(self):          return self.tab.item(self.ro,0).text()
    def putName(self, v):       self.tab.item(self.ro,0).setText(str(v))
    def getNick(self):          return self.tab.item(self.ro,1).text()
    def putNick(self, v):       self.tab.item(self.ro,1).setText(str(v))
    def getWide(self):          return xml_float(self.tab.item(self.ro,2).text())
    def putWide(self, v):       self.tab.item(self.ro,2).setText(str(v))
    def getHigh(self):          return xml_float(self.tab.item(self.ro,3).text())
    def putHigh(self, v):       self.tab.item(self.ro,3).setText(str(v))
    def getOh1(self):           return xml_float(self.tab.item(self.ro,4).text())
    def putOh1(self, v):        self.tab.item(self.ro,4).setText(str(v))
    def getOho(self):           return xml_float(self.tab.item(self.ro,5).text())
    def putOho(self, v):        self.tab.item(self.ro,5).setText(str(v))
    def getOh1a(self):          return xml_float(self.tab.item(self.ro,6).text())
    def putOh1a(self, v):       self.tab.item(self.ro,6).setText(str(v))
    def getOhoa(self):          return xml_float(self.tab.item(self.ro,7).text())
    def putOhoa(self, v):       self.tab.item(self.ro,7).setText(str(v))

    @staticmethod          #    Column #   Format     Id           Column-name 
    def colName():         return  0   #      s     Name           Tape Type
    @staticmethod
    def colNick():         return  1   #      s     Nick           nickname
    @staticmethod
    def colWide():         return  2   #      f     Wide           Tape Width
    @staticmethod
    def colHigh():         return  3   #      f     High           Tape High
    @staticmethod
    def colOh1():          return  4   #      f     Oh1            Overhang1
    @staticmethod
    def colOho():          return  5   #      f     Oho            Overhang2
    @staticmethod
    def colOh1a():         return  6   #      f     Oh1a           Over.1 alt
    @staticmethod
    def colOhoa():         return  7   #      f     Ohoa           Over.2 alt

class Table2:  # Class: Accessors for a row of tab2 / rails / Unit Specs
    def __init__(self,tab,ro):  self.tab, self.ro = tab, ro
    ''' __init__ sets values of .tab and .ro variables'''
    def row(self):              return self.ro
    def setRow(self,ro):        self.ro = ro
    def tab(self):              return self.tab
    def setTab(self,ro):        self.tab = tab
    @staticmethod
    def tabN():                 return "2"
    @staticmethod
    def tabCue():               return "rails"
    @staticmethod
    def tabName():              return "Unit Specs"
    @staticmethod
    def colCids():              return ['Label', 'Use', 'CapWide', 'CapLen', 'EndLen', 'PadLen', 'Slack', 'Posts', 'PostOffset', 'PostID', 'PostOD', 'LegThik', 'CapThik', 'Bridges', 'BridgeOffset', 'BridgeWide']
    @staticmethod
    def colCues():              return ['label', 'Use', 'CapWide', 'CapLen', 'EndLen', 'PadLen', 'Slack', 'Posts', 'PostOffset', 'PostID', 'PostOD', 'LegThik', 'CapThik', 'Bridges', 'BridgeOffset', 'BridgeWide']
    @staticmethod
    def colFmts():              return ['s', 'r', 'f', 'f', 'f', 'f', 'f', 'i', 'f', 'f', 'f', 'f', 'f', 'i', 'f', 'f']
    @staticmethod
    def colNames():             return ['Spec-Label', 'Use', 'Cap Width', 'Cap Len', 'Cap End-Len', 'End-padding', 'Slack', 'Posts', 'Post Offset', 'Post ID', 'Post OD', 'Leg-Thick', 'Cap-Thick', 'Bridges', 'Brg Offset', 'Brg Width']

    def getLabel(self):         return self.tab.item(self.ro,0).text()
    def putLabel(self, v):      self.tab.item(self.ro,0).setText(str(v))
    def getUse(self):           return xml_float(self.tab.item(self.ro,1).text())
    def putUse(self, v):        self.tab.item(self.ro,1).setText(str(v))
    def getCapWide(self):       return xml_float(self.tab.item(self.ro,2).text())
    def putCapWide(self, v):    self.tab.item(self.ro,2).setText(str(v))
    def getCapLen(self):        return xml_float(self.tab.item(self.ro,3).text())
    def putCapLen(self, v):     self.tab.item(self.ro,3).setText(str(v))
    def getEndLen(self):        return xml_float(self.tab.item(self.ro,4).text())
    def putEndLen(self, v):     self.tab.item(self.ro,4).setText(str(v))
    def getPadLen(self):        return xml_float(self.tab.item(self.ro,5).text())
    def putPadLen(self, v):     self.tab.item(self.ro,5).setText(str(v))
    def getSlack(self):         return xml_float(self.tab.item(self.ro,6).text())
    def putSlack(self, v):      self.tab.item(self.ro,6).setText(str(v))
    def getPosts(self):         return xml_int(self.tab.item(self.ro,7).text())
    def putPosts(self, v):      self.tab.item(self.ro,7).setText(str(v))
    def getPostOffset(self):    return xml_float(self.tab.item(self.ro,8).text())
    def putPostOffset(self, v): self.tab.item(self.ro,8).setText(str(v))
    def getPostID(self):        return xml_float(self.tab.item(self.ro,9).text())
    def putPostID(self, v):     self.tab.item(self.ro,9).setText(str(v))
    def getPostOD(self):        return xml_float(self.tab.item(self.ro,10).text())
    def putPostOD(self, v):     self.tab.item(self.ro,10).setText(str(v))
    def getLegThik(self):       return xml_float(self.tab.item(self.ro,11).text())
    def putLegThik(self, v):    self.tab.item(self.ro,11).setText(str(v))
    def getCapThik(self):       return xml_float(self.tab.item(self.ro,12).text())
    def putCapThik(self, v):    self.tab.item(self.ro,12).setText(str(v))
    def getBridges(self):       return xml_int(self.tab.item(self.ro,13).text())
    def putBridges(self, v):    self.tab.item(self.ro,13).setText(str(v))
    def getBridgeOffset(self):  return xml_float(self.tab.item(self.ro,14).text())
    def putBridgeOffset(self, v): self.tab.item(self.ro,14).setText(str(v))
    def getBridgeWide(self):    return xml_float(self.tab.item(self.ro,15).text())
    def putBridgeWide(self, v): self.tab.item(self.ro,15).setText(str(v))

    @staticmethod          #    Column #   Format     Id           Column-name 
    def colLabel():        return  0   #      s     Label          Spec-Label
    @staticmethod
    def colUse():          return  1   #      r     Use            Use
    @staticmethod
    def colCapWide():      return  2   #      f     CapWide        Cap Width
    @staticmethod
    def colCapLen():       return  3   #      f     CapLen         Cap Len
    @staticmethod
    def colEndLen():       return  4   #      f     EndLen         Cap End-Len
    @staticmethod
    def colPadLen():       return  5   #      f     PadLen         End-padding
    @staticmethod
    def colSlack():        return  6   #      f     Slack          Slack
    @staticmethod
    def colPosts():        return  7   #      i     Posts          Posts
    @staticmethod
    def colPostOffset():   return  8   #      f     PostOffset     Post Offset
    @staticmethod
    def colPostID():       return  9   #      f     PostID         Post ID
    @staticmethod
    def colPostOD():       return 10   #      f     PostOD         Post OD
    @staticmethod
    def colLegThik():      return 11   #      f     LegThik        Leg-Thick
    @staticmethod
    def colCapThik():      return 12   #      f     CapThik        Cap-Thick
    @staticmethod
    def colBridges():      return 13   #      i     Bridges        Bridges
    @staticmethod
    def colBridgeOffset(): return 14   #      f     BridgeOffset   Brg Offset
    @staticmethod
    def colBridgeWide():   return 15   #      f     BridgeWide     Brg Width

class Table3:  # Class: Accessors for a row of tab3 / makes / Units to Make
    def __init__(self,tab,ro):  self.tab, self.ro = tab, ro
    ''' __init__ sets values of .tab and .ro variables'''
    def row(self):              return self.ro
    def setRow(self,ro):        self.ro = ro
    def tab(self):              return self.tab
    def setTab(self,ro):        self.tab = tab
    @staticmethod
    def tabN():                 return "3"
    @staticmethod
    def tabCue():               return "makes"
    @staticmethod
    def tabName():              return "Units to Make"
    @staticmethod
    def colCids():              return ['Ttype', 'VolRO']
    @staticmethod
    def colCues():              return ['ttype', 'volRO']
    @staticmethod
    def colFmts():              return ['s', 'f']
    @staticmethod
    def colNames():             return ['Tape Type', 'Unit volume']

    def getTtype(self):         return self.tab.item(self.ro,0).text()
    def putTtype(self, v):      self.tab.item(self.ro,0).setText(str(v))
    def getVolRO(self):         return xml_float(self.tab.item(self.ro,1).text())
    def putVolRO(self, v):      self.tab.item(self.ro,1).setText(str(v))

    @staticmethod          #    Column #   Format     Id           Column-name 
    def colTtype():        return  0   #      s     Ttype          Tape Type
    @staticmethod
    def colVolRO():        return  1   #      f     VolRO          Unit volume

class Table4:  # Class: Accessors for a row of tab4 / hints / Instructions
    def __init__(self,tab,ro):  self.tab, self.ro = tab, ro
    ''' __init__ sets values of .tab and .ro variables'''
    def row(self):              return self.ro
    def setRow(self,ro):        self.ro = ro
    def tab(self):              return self.tab
    def setTab(self,ro):        self.tab = tab
    @staticmethod
    def tabN():                 return "4"
    @staticmethod
    def tabCue():               return "hints"
    @staticmethod
    def tabName():              return "Instructions"
    @staticmethod
    def colCids():              return ['Item']
    @staticmethod
    def colCues():              return ['item']
    @staticmethod
    def colFmts():              return ['s']
    @staticmethod
    def colNames():             return ['How to use these tables:']

    def getItem(self):          return self.tab.item(self.ro,0).text()
    def putItem(self, v):       self.tab.item(self.ro,0).setText(str(v))

    @staticmethod          #    Column #   Format     Id           Column-name 
    def colItem():         return  0   #      s     Item           How to use these tables:

def tableCount():       return 4
def tableCues():        return ['tapes', 'rails', 'makes', 'hints']
def tableNums():        return ['1', '2', '3', '4']
def tableNames():       return ['Tape Data', 'Unit Specs', 'Units to Make', 'Instructions']
