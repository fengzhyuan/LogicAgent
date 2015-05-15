
'generate map'

import os.path
import os
import random
import basics
"""
some declarations:
g: gold
w: wumpus
p: pits
"""

class wumpusMap(object):
    def __init__(self, size):
        'variables'
        
        'map size'
        self.size   = size
        
        'gold position'
        self.gold   = None
        
        'wumpus position'
        self.wumpus = None
        
        'pits lists'
        self.pits   = list()
        
        'for print'
        self.mapArr = basics.init2darray(self.size)
        
        'add gold '
    def addGold(self, x, y):
        self.gold = (x, y)
        self.mapArr[x][y] = 9
        
        'add a pit'
    def addPit(self, x, y):
        self.pits.append((x, y))
        self.mapArr[x][y] = 8
        ' add wumpus '
    def addWumpus(self, x, y):
        self.wumpus = (x, y)
        self.mapArr[x][y] = 7
        
        'generate random position'
    def randPos(self, size):
        x = 0 
        y = 0
        
        while x == 0 and y == 0:
            x = random.randint(0, size - 1)
            y = random.randint(0, size - 1)
            
        return (x, y)      
    
        'print map'
    def printMap(self):
        #print self.mapArr
        
#        for i in range(0,self.size):
#            print
#            for j in range(0,self.size):
#                print self.mapArr[i][j],
                
        for i in range(self.size):
            print
            for j in range(self.size):
                print "|%s%s%s" %("G" if (i,j) == self.gold else " ", "W" if (i,j) == self.wumpus else " ", "P" if (i,j) in self.pits else " "),
            print "|",
        print
        print
                      

        'generate map'
    def genMaps(self):
        agentPos = (3,0)        
        for i in range(self.size):
            for j in range(self.size):
                'generate random position'
                if random.random() < 0.2 and not(i == 0 and j == 0) and (i,j) != agentPos: 
                    'not at first square'
                    self.addPit(i, j)
        
        'add gold'
        while 1:
            rposGold = self.randPos(self.size)
            if rposGold not in self.pits and rposGold != agentPos:
                self.addGold( *rposGold )
                break 
        
        'add wumpus'
        while 1:
            rposW = self.randPos(self.size)
            if rposW != rposGold and rposW not in self.pits and rposW != agentPos:
                self.addWumpus( *rposW )
                break
        
       
        'write to files'
    def saveMap(self, mName):
        
        ofile = open(mName, "w")
        'size'
        ofile.write("s: %i\n" % self.size)
        'gold pos.'
        ofile.write("g: %i,%i\n" % self.gold)
        'wumpus pos'
        ofile.write("w: %i,%i\n" % self.wumpus)
        'for all pits'
        for pos in self.pits:
            ''' print pos'''
            if pos != self.gold or pos != self.wumpus:
                ofile.write("p: %i,%i\n" % pos)
    
#    if __name__ == "__main__"  :  
#        mapSize = 4
#        mMap = wumpusMap(mapSize)
#        mMap.genMaps()
#        mMap.printMap()    
        
        