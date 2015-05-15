
'environment of agent'

import os.path

import basics
import re

class WumpusWorld(object):
    def __init__(self, fileName):
        'map size'
        self.size = 0
        ' create map '
        self.map = {}
        #self.map = basics.init2darray(self.size)
        ''' store tag about whether a square has been visited by the agent'''
        self.explorMap = basics.init2darray(self.size)
        self.isDeadWumpus = False
        
        ''' position'''
        self.goldcoord = (-1, -1)
        self.Wumpcoord = (-1, -1)
        self.Pitcoord  = []
        
        self.readMap(fileName)
        'wumpus scream. agent check this tag at each time step t. if shoot() makes wumpus dead, update to True,\
        then sensor can percept at time step t+1'
        self.scream = False
        
        # init assumHistory.txt
        ofile = open("assumHistory.txt", "w")
        ofile.write("\nformulas(assumptions).\n")
        for x in range(self.size):
            for y in range(self.size):
                #(x,y,t)
                ofile.write("\n-Visited(%i,%i).\n" % (x, y))
        ofile.write("\nend_of_list.\n")
        ofile.close()
        
        ' check if face with boundary'
    def faceWall(self, x, y):
        return (x >= 0 and y >= 0 and x <= self.size - 1  and y <= self.size - 1)
        ''' read map from file'''
    def readMap(self, fileName):
        ''' read size first'''
        for line in open(fileName, "r"):
            (tag, p, pos) = line.partition(": ")
            self.size = int(pos)
            break;
        
        ''' init map'''
        for x in range(self.size):
            for y in range(self.size):
                self.map[(x, y)] = (False, False, False)
        
        for line in open(fileName, "r"):
            (tag, p, pos) = line.partition(": ")
            (x, d, y) = pos.partition(",")
            ''' from string to int'''
            #print pos
            if tag != "s":
                x = int(x)
                y = int(y)
                ''' check what's in the square'''
                wumpus = "w" in tag
                gold   = "g" in tag
                pit    = "p" in tag
                
                (wt, gt, pt) = self.map[(x, y)]
                wumpus = wumpus or wt
                gold   = gold or gt
                pit    = pit or pt
                
                self.map[(x, y)] = (wumpus, gold, pit)
            
        self.findPosition()
            
    def neighbors(self, x, y):
        
        ''' calculate all neighbors and check each of them whether they are valid  '''
        neiSet = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        
        return filter(lambda n: self.faceWall(*n), neiSet)
    
    def sensor(self, x, y):
        x = int(x)
        y = int(y)
        ' sensor tag'
        senStench = False
        senGold   = False
        senPit    = False
        
        ''' if not out of bound, used for percept sensors of all neighbors of a square '''
        if (x, y) in self.map:
            senGold = self.map[(x, y)][1]
            
            for nNeighbor in self.neighbors(x, y):
                if nNeighbor in self.map:
                    (w, g, p) = self.map[nNeighbor]
                    senStench = senStench or w
                    #senGold   = senGold or g
                    senPit    = senPit or p 
        
        return (senStench, senGold, senPit)
    def sense(self, x, y):
        (w,g,p) = self.sensor(*(x, y))

        b = self.faceWall(*(x, y))
        s = self.scream
#        if s == True:
#            self.scream = False
        
        return (w,g,p,b,s)
        ''' if current place's neighbors contain wumpus or pit '''
    def inDanger(self, x, y):
        w = False
        g = False
        p = False

        for nei in self.neighbors(x, y):
            (mw, mg, mp) = self.map[nei]
            w = (w and not self.isDeadWumpus) or mw
            p = p or mp
            
        if w == True or p == True:
            return True
        else:
            return False
        ''' print environment'''
    def printEnv(self):
        
        for x in range(self.size):
            print"|",
            for y in range(self.size):
                (wumpus,gold, pit) = self.map[(x,y)]
                print ("%s%s%s|" % ( "p" if pit else " ", "w" if wumpus else " ", "g" if gold else " " )),
                #print"\n"
            print"\n"
            
        ''' return gold position'''    
    def findPosition(self):
        for x in range(self.size):
            for y in range(self.size):
                if self.map[(x, y)][1] == True:
                   self.goldcoord = (x, y)
                elif self.map[(x, y)][0] == True:
                   self.Wumpcoord = (x, y)
                elif self.map[(x, y)][2] == True and ((x,y) not in self.Pitcoord):
                    self.Pitcoord.append((x,y))

    #test
#if __name__ == "__main__":
#    env = WumpusWorld("./maps/4_0")
#    coord = (0, 2)
##    print env.map[coord]
#    print "Wumpus Gold Pit"
#    print env.sensor(*coord)
#    print "in danger?",
#    print env.inDanger(*coord)
#    env.printEnv()
#    
#    env.findPosition()
#    print "gold position:",
#    print env.goldcoord
#    print "pit list:",
#    print env.Pitcoord
#    print "wumpus:",
#    print env.Wumpcoord
#    
#        