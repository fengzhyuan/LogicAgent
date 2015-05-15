

import os.path
import os
import random


def init2darray(size):
    list=[]
    for row in range(size):
        list.append([0]*size)
    return list

def maptofile(mp):
    ofile = open("map.txt", 'a')
    for x in range(mp.size):
        ofile.write("|")
        for y in range(mp.size):
            (wumpus,gold, pit) = mp.map[(x,y)]
            ofile.write("%s%s%s|" % ( "p" if pit else " ", "w" if wumpus else " ", "g" if gold else " "))
        ofile.write("\n")
    ofile.write( "\n"  )
    
    ofile.close()