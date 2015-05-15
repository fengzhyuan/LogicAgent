import os
import os.path
import genMap
import HybAgent
import envWorld
import logicEngine
import profile
import time
import basics

if __name__ == "__main__"  :  
    #'path for saving maps'
    mapPath = "./maps/"
    mapSize = 5
    numMaps = 40
    for nMaps in range(numMaps):
        mMap = genMap.wumpusMap(mapSize)
        mMap.genMaps()
        mMap.saveMap(os.path.join(mapPath, "%i_%i" % (mapSize, nMaps)))
        
   
    fileName = "rbfs.txt"
    ofile = open(fileName, 'w')
    open("map.txt",'w+').read()
    
    nSuccess = 0
    for nMap in range(0, numMaps):
        print "\n\n%i th map\n" % nMap
        mapName = mapPath + "%i_%i" % (mapSize, nMap)   
        env = envWorld.WumpusWorld(mapName)
        
        #write map into file
        basics.maptofile(env)
        
        logic = logicEngine.Engine();
        
        agent = HybAgent.HybridAgent(env, logic)
        
        lol = False
        c1 = time.time()
        if agent.search():
            nSuccess = nSuccess + 1
            lol = True
        c2 = time.time()
        ' record performance. time, step result'
        ofile.write("%f\t%i\t%s\n" % ((c2 - c1), agent.action, "success" if lol else "fail"))
        
        #profile.run("agent.search()")
        #break
        
    print "success times: %i" %nSuccess
    ofile.write("s: %i \t \n" %nSuccess)
    ofile.close()

     