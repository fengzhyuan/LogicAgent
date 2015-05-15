
''' agent class '''
import os
import os.path
import re
import envWorld
import logicEngine
import random
import time
from threading import Thread, Condition, currentThread
import sys
import basics


class HybridAgent(object):

    def __init__(self, env, logic):
        
        #thread init
       # Thread.__init__(self)
        # if agent has arrow
        self.hasArrow   = True
        # if agent is dead
        self.isdead     = False
        # agent logic engine, logicEngine class, connected by prover9
        self.logicEng   = None
        # store current map
        self.env        = None
        # if success or not
        self.success    = False
        # if found gold or not
        self.foundgold  = False
        self.position   = (3,0)
        # time step
        self.action = 0
        
        self.env = env
        self.logicEng = logic
        
        #store visit tag
        self.visited = basics.init2darray(self.env.size)
        # string for rules and assumption history during program runtime
        self.assumHistory = ""
        #read init history from file
        #self.assumHistory = open("assumHistory.txt",'r').read()
        
        self.rules = ""
        self.Query = ""
        
        ''' global constants for rbfs'''
        self.NMAX = 10000
        self.MAX_NUM = 1000000
        self.SUCCESS = 1
        self.FAIL = -1
        self.rbfpath = []
        self.rbfTag = 1
        self.searchEngine = ""
        
    def updateLoc(self, (x, y)):
        self.position = (x, y)
        
    def updateVisitHistory(self, fileName, srcStr, dstStr):

        substr1 = '-Visited(%i,%i).' % self.position
        substr2 = 'Visited(%i,%i).' % self.position
        #visited
        data = open(fileName, 'r').read()
        data = data.replace(srcStr,dstStr)
        F = open(fileName, 'w')
        F.write(data)
        F.close()
        #open(fileName, 'w').write(data)
    def updateRule(self, fileName, rules):
        ofile = open(fileName, 'a')
        ofile.write("\n" + rules + "\n")
        ofile.close()
        
    def TELL(self, (wumpus, gold, pit, bump, scream), t):         
        x = self.position[0]
        y = self.position[1]
        
        '''
        --------------------------------------------------------
        get rules
        --------------------------------------------------------
        '''
        uFirst = "formulas(usable).\n"
        uLast =  "end_of_list.\n\n"
        uSent = "B(%i,%i) <->" % (x,y)
        tag = 0
        for nei  in self.env.neighbors(x, y):
            if tag == 0:
                uSent = uSent + "P(%i,%i)" % nei #+ "&-Visited(%i,%i)" % nei
                tag = 1
            else:
                uSent = uSent + "|P(%i,%i)" % nei #+ "&-Visited(%i,%i)" % nei
        uSent = uSent + ".\n"
        
        tag = 0
        uSent = uSent + "S(%i,%i) <->" % self.position
        for nei in self.env.neighbors(x, y):
            if tag == 0:
                uSent = uSent + "W(%i,%i)" % nei #+ "&-Visited(%i,%i) & TimePoint(%i)" % (nei[0], nei[1], t)
                tag = 1
            else:
                uSent = uSent + "|W(%i,%i)" % nei #+ "&-Visited(%i,%i)& TimePoint(%i)" % (nei[0], nei[1], t)
        uSent = uSent + ". \n"

        
        '''
        Loc(x, y, t) -> (Breeze(t) <-> B(x, y))
        Loc(x, y, t) -> (Stench(t) <-> W(x, y))
        Loc(x, y, t) -> -P(x, y)
        Loc(x, y, t) -> -W(x, y)
        '''
        uSent = uSent + "Loc(%i,%i,%i)->(Breeze(%i)<-> B(%i,%i)).\n" % (x,y,t,  t,  x,y)
        uSent = uSent + "Loc(%i,%i,%i)->(Stench(%i)<-> W(%i,%i)).\n" % (x,y,t,  t,  x,y) 
        uSent = uSent + "Loc(%i,%i,%i)->-P(%i,%i).\n" %(x,y,t, x,y) 
        uSent = uSent + "Loc(%i,%i,%i)->(-W(%i,%i)) | (W(%i,%i) & -WumpusAlive(%i)).\n" %(x,y,t, x,y, x,y, t)
        
        '''OK(x, y, t) <-> -P(x,y) & -(W(x, y) &WumpusAlive(t))'''
        #uSent = uSent + "OK(%i,%i,%i)<->-P(%i,%i)&-(W(%i,%i)&WumpusAlive(%i)).\n" % (x,y,t,  x,y,  x,y,  t)
        for x1 in range(self.env.size):
            for y1 in range(self.env.size):
                if t > 0:
                    substr1 = "OK(%i,%i,%i)<->-P(%i,%i)&-(W(%i,%i)&WumpusAlive(%i)).\n" % (x1,y1,t-1,  x1,y1,  x1,y1,  t-1)
                    substr2 = "OK(%i,%i,%i)<->-P(%i,%i)&-(W(%i,%i)&WumpusAlive(%i)).\n" % (x1,y1,t,  x1,y1,  x1,y1,  t)
                    self.rules = self.rules.replace(substr1, substr2)
                else:                    
                    uSent = uSent + "OK(%i,%i,%i)<->-P(%i,%i)&-(W(%i,%i)&WumpusAlive(%i)).\n" % (x1,y1,t,  x1,y1,  x1,y1,  t)

                #uSent = uSent + "Visited(%i,%i) -> -W(%i,%i) | (W(%i,%i) & -WumpusAlive(%i)).\n" % (x1,y1, x1,y1, x1,y1, t)
                #uSent = uSent + "Visited(%i,%i) -> OK(%i,%i,%i) .\n" % (x1,y1, x1,y1,t)
                #if t > 0:
                #uSent = uSent + "OK(%i,%i,%i)->OK(%i,%i,%i).\n" % (x1,y1,t,  x1,y1, t+1)
        '''%glitter(t) G(x, y) & Loc(x, y,t) -> Grab(t)'''  
        uSent = uSent + "G(%i,%i)&Loc(%i,%i,%i)->Grab(%i).\n" % (x,y,  x,y,t,  t)
        
        ''' HaveArrow(t+1) <-> HaveArrow(t) & -Shoot(t)'''
        #uSent = uSent + "HaveArrow(%i) <-> HaveArrow(%i) & -Shoot(%i).\n" %((t+1), t, t)
        
        ''' 
        % scream
        Scream(t) -> -WumpusAlive(t + 1)
        -WumpusAlive(t) -> -WumpusAlive(t + 1)
        WumputAlive(t+1)-> WumputAlive(t)
        '''
#        uSent = uSent + 'Scream(%i) -> -WumpusAlive(%i).\n' % (t, t + 1)
#        uSent = uSent + '-WumpusAlive(%i) -> -WumpusAlive(%i).\n' %(t, t+1 )
#        uSent = uSent + 'WumpusAlive(%i) -> WumpusAlive(%i).\n' %(t+1, t )
#        uSent = uSent + 'Scream(%i) -> -WumpusAlive(%i).\n' %(t, t+1 )
        usable = uFirst + uSent + uLast

        self.rules = self.rules + usable 
#        ruleFileName = "rules.txt"
#        self.updateRule(ruleFileName, usable)
        
        '''
        --------------------------------------------------------
        get assumptions. current + history
        --------------------------------------------------------
        ''' 
        '''
        contents need to be recorded : visited(x,y), wumpusalive(t) havearrow(t)
        '''
#        fileName = "assumHistory.txt"
#
        substr1 = '-Visited(%i,%i).' % self.position
        substr2 = 'Visited(%i,%i).' % self.position
#        self.updateVisitHistory(fileName, substr1, substr2)
        #self.assumHistory = self.assumHistory.replace(substr1, substr2)
        self.visited[x][y] = 1
        '''
        .
        . update shoot(t) in function Plan-Shot()
        '''
        # wumpusalive
        #outfile = open(fileName, 'a')
        aSent = ""
        #outfile.write("\nformulas(assumptions).\n\n")
        aSent = aSent + "\nformulas(assumptions).\n\n"
        #current location

#        outfile.write("%s(%i).\n" %("WumpusAlive" if not scream else "-WumpusAlive", t))
#        outfile.write("%s(%i).\n" %("-Shoot" , t)) #if self.hasArrow else "Shoot", t))
#        outfile.write("%s(%i).\n" %("HaveArrow" if self.hasArrow else "-HaveArrow", t))
        aSent = aSent + "%s(%i).\n" %("WumpusAlive" if not scream else "-WumpusAlive", t) \
                      + "%s(%i).\n" %("-Shoot" , t) \
                      + "%s(%i).\n" %("HaveArrow" if self.hasArrow else "-HaveArrow", t)
                      
        
        
        #outfile.write("% --------------\n")
        ''' known assumptions '''
        aSent = aSent + "%s(%i,%i).\n" % ( "S" if wumpus else "-S", x,y)\
                      + "%s(%i,%i).\n" % ( "G" if gold else "-G", x,y)\
                      + "%s(%i,%i).\n" % ( "B" if pit else "-B", x, y)\
                      + "%s(%i,%i,%i).\n" % ("Loc", x, y, t)    
        # wumpus is dead
        #aSent = aSent + "W(%i,%i).\n" % self.env.Wumpcoord
        
        '''
        time t
        '''
        #aSent = aSent + "TimePoint(%i).\n" % t
            
        #outfile.write(aSent)
        #outfile.write("\nend_of_list.\n\n")
        aSent = aSent + "\nend_of_list.\n\n"
        #outfile.close()
        self.assumHistory = self.assumHistory + aSent
        
    def ASK(self, goals, t, position):
        goal = ""
        px = position[0]
        py = position[1]
        if goals == "Grab":
            goal = "Grab(%i).\n" % t
        elif goals == "Loc":
            goal = "Visited(%i,%i).\n" % position
        elif goals == "HaveArrow":
            goal = "HaveArrow(%i).\n" % t
        elif goals == "OK":
            goal = "OK(%i,%i,%i).\n" %(px, py, t)
        elif goals == "NoOK":
            goal = "-OK(%i,%i,%i).\n" %(px, py, t)
        elif goals == "NoWumpus":
            goal = "-W(%i,%i).\n" % position    
            
        ''' goals '''
        gFirst = "formulas(goals).\n"
        gLast  = "end_of_list.\n\n"
        Goal  = gFirst + goal + gLast
        #print Goal
        '''
        get rule, assumption and goal, send message into logic engine
        '''
#        usable = open("rules.txt", 'r').read()
#        assumption = open("assumHistory.txt", 'r').read()

        self.Query = self.rules + self.assumHistory + Goal
        '''
        save message into file for query(self, filename)
        '''
        queryfileName = "KBQuery.txt"
        ofile = open(queryfileName, 'w')
        #ofile.write("\n" + Message)
        ofile.write("\n" + self.Query)
        ofile.close()
        
        #print Message
        result = False
        result = self.logicEng.query(queryfileName)
        #print position, goals, result
        return result
    

    def heuris(self, start, goal):
        return abs(start[0] - goal[0]) * 2 + abs(start[1] - goal[1]) * 2

        ''' a* algo. see wikipedia'''
    def A_star(self, cn, goal, allowedSet):
        self.searchEngine = "ASTAR"
        openList = []
        path = []
#        for e in allowedSet:
#            ND = (e[0], e[1], 0,0)
#            openList.append(ND)
        
        # add root node into allowed set
        #allowedSet.append(cn)
        firstTime = 1
        ND = (cn[0],cn[1],0,self.heuris(cn, goal))
        openList.append(ND)
        closeList = []

        '''
        'x, y, g_value, f_value'
        '''
#        Node = (cn[0],cn[1],0,self.heuris(cn, goal))
#        openList.append(Node)
        
        while len(openList) != 0:
            openList.sort(cmp, key = lambda k: k[3])
            curNode = openList[0]
            #if curNode[0] == goal[0] and curNode[1] == goal[1]:
            if (curNode[0], curNode[1]) == goal:
                path.append(curNode)
                return path
            
            openList.remove(curNode)
            closeList.append((curNode[0], curNode[1]))
            # track storage
            if (curNode[0], curNode[1]) != cn:
                path.append(curNode)
            if firstTime:
                firstTime = False
            else:
                if (curNode[0],curNode[1]) not in allowedSet:# and (curNode[0],curNode[1]) == cn:
                       path.remove(curNode)
                       continue
            
            child = self.env.neighbors(curNode[0],curNode[1])
#            children = []
#            for e in child:
#                curN = (e[0],e[1],0,0)
#                children.append(curN)
                
            for idx,e in enumerate(child):
                if (e) in closeList:
                    continue
                t_g = curNode[2] + 1
                bNOpLst = e not in openList
                
                if bNOpLst == True :
                    e2 = t_g
                    
                    e3 =  self.heuris(e, goal)
                    children = (e[0], e[1], e2, e3)
                    
                    if bNOpLst == True:
                        for e1 in openList:
                            if e1 == e:
                                continue
                        #if children[idx] not in openList:
                        openList.append(children)
        
        path = []                
        return path
        
    '''
    rbf search
    NOTE: cn: (cn[0], cn[1], 0, 0)
    '''
    def RBFS(self, cn, goal, flimit, closeList, allowedSet):
        self.rbfpath.append((cn[0],cn[1]))
        closelist = []
        closelist = closeList[:]
        cnSub = (cn[0], cn[1])

        if cnSub != goal:
            successor = []
            # check if current node are valid
            if self.rbfTag:
                self.rbfTag = 0
            else:
                
                if cnSub not in allowedSet:
                    return self.FAIL * self.MAX_NUM
                
            neis = self.env.neighbors(cnSub[0], cnSub[1])
            for e in neis:
                if e not in closelist:
                    '''x, y, g_value, f_value'''
                    successor.append((e[0], e[1], 0, 0))
                    closelist.append(e)
            
            if len(successor) == 0:
                self.rbfpath.remove((cn[0],cn[1]))
                return self.FAIL * self.MAX_NUM
            
            for idx,e in enumerate(successor):
                h_val = self.heuris((e[0],e[1]), goal)
                
                curGV = cn[3] + 1
                curFV = (e[3] + h_val) if (e[3] + h_val) > cn[2] else cn[2] 
                successor[idx] = (e[0],e[1],curGV,curFV)
                
                
            while 1:
                best = None
                subBest = self.MAX_NUM
                
                successor.sort(cmp, key = lambda k: k[3])
                best = successor[0]
                
                if best[3] > flimit:
                    return best[3] * self.FAIL
                if len(successor) > 1:
                    subBest = successor[1][3]
                    
                minVal = flimit if flimit < subBest else subBest
                result = self.RBFS(best, goal, minVal, closelist, allowedSet)
                
                if result > 0:
                    return result
                if result == self.FAIL:
                    return self.FAIL
                firstN = successor[0]
                successor[0] = (firstN[0],firstN[1], firstN[2], abs(result))
                bnod = (best[0],best[1])
                if bnod in self.rbfpath:
                    self.rbfpath.remove(bnod)
        return self.SUCCESS      
    
    def RBFSTrav(self, current, goal, allowed):
        self.searchEngine = "RBFS"
        self.rbfpath = []
        
        cn = (current[0], current[1], 0, 0)
        flimit = 10000
        closeList = []
        closeList.append(current)
        
        self.rbfTag = 1
        self.RBFS(cn, goal, flimit, closeList, allowed)
       
        #self.rbfpath = list(set(self.rbfpath))
        tmp = []
        for e in self.rbfpath:
            if e not in tmp:
                tmp.append(e)
        self.rbfpath = tmp
        
        self.rbfpath.remove(current)
        
        return self.rbfpath
                        
    ''' 
    plan a route
    current, goals, allowed
    '''
    def planRoute(self, current, goals, allowed):
        r = []
        for e in goals:
            #print "current goal:", e
            #r = self.A_star(current, e, allowed) 
            r = self.RBFSTrav(current, e, allowed)
            
            if r != []:
                break
        
        return r
#        pathset = []
#        curpath = []
#        problem = None
#        #print len(goals)
#        while 1:
#            rn = random.randint(0,15)
#            if rn <= len(goals):
#                problem = goals[rn]
#                break
#            
#        return self.A_star(current, problem, allowed)
        
        '''
        try to shoot
        '''
    def planShoot(self, current, goals, t):
        
        ''' update file first'''
        #fAH = "assumHistory.txt"
        #fKB = "KBQuery.txt"
        '''
        -Shoot(0).
        HaveArrow(0).
        '''
        substr1 = '-Shoot(%i).' % t
        substr2 = 'Shoot(%i).' % t
        #self.updateVisitHistory(fAH, substr1, substr2)
        self.assumHistory = self.assumHistory.replace(substr1, substr2)
        #self.updateVisitHistory(fKB, substr1, substr2)
        self.Query = self.Query.replace(substr1, substr2)

        
        pshot = []
        NORTH = 0
        SOUTH = 1
        EAST  = 2
        WEST  = 3
        
        direction = -1;
        we = 0
        ea = 0
        nor= 0
        sou= 0
        
        for e in goals:
            if e[1] == current[1]:
                if e[0] > current[0]:
                    sou = sou + 1 #south
                else:
                    nor = nor + 1 #north
            elif e[0] == current[0]:
                if e[1] > current[1]:
                    ea = ea + 1; #east
                else:
                    we = we + 1; #west
                    
        idx = [nor, sou, ea, we]
        r = idx.index(max(idx) ) 
        if r == 0: #
            direction = NORTH
        elif r == 1:
            direction = SOUTH
        elif r == 2:
            direction = EAST
        else:
            direction = WEST         
        

        """
        an arrow is shot from x,y in the given direction, returns true if the agent
        hears the screem
        """
        hit = False
        
        #find the square with the wumpus
        (wx, wy) = self.env.Wumpcoord
        (x, y) = current
        #check the directions to see if the arrow hit the wumpus
        if direction == NORTH:
            if y == wy and wx < x:
                hit = True
        
        elif direction == SOUTH:
            if y == wy and wx > x:
                hit = True
        
        elif direction == EAST:
            if x == wx and wy > y:
                hit = True
        
        else:
            if x == wx and wy < y:
                hit = True
    
        if hit:
            self.env.scream = True
        
        pshot.append ("shot")
        self.hasArrow = False    
        return pshot
#        return hit
        '''
        return safe list for agent at current location and at time point t 
        '''    
    def safeList(self, t):
        safeSq = []
        len = self.env.size
        for x in range(len):
            for y in range(len):
                 if self.ASK("OK", t, (x, y)) == True:
                     #print "%i,%i OK\n" % (x, y)
                     safeSq.append((x, y))
        
        #print safeSq
        return safeSq
    
        ''' route each element in path set and update agent position for each loop'''
    def letsGo(self, pathSet):
        # if path or action: shoot
        if pathSet[0] != "shot":
            e = None
            if self.searchEngine == "ASTAR":
                e = pathSet[0]
            elif self.searchEngine == "RBFS":
                e = pathSet[0]
            pos = (e[0], e[1])
            self.position = pos
            #update visit tag
            #fileName1 = "assumHistory.txt"
            #fileName2 = "KBQuery.txt"
            substr1 = '-Visited(%i,%i).' % self.position
            substr2 = 'Visited(%i,%i).' % self.position
#                #self.updateVisitHistory(fileName1, substr1, substr2)
#                self.assumHistory = self.assumHistory.replace(substr1, substr2)
#                #self.updateVisitHistory(fileName2, substr1, substr2)
#                self.Query = self.Query.replace(substr1, substr2)
            self.visited[self.position[0]][self.position[1]] = 1
            self.action = self.action + 1
            # print updated info
            self.printMap()
            #time.sleep(1)
#                if (self.position == self.env.Wumpcoord and self.env.scream == False)or self.position in self.env.Pitcoord:
#                    self.isdead = True
#                    return
#                if self.position == self.env.goldcoord:
#                    self.foundgold = True
#                    return

        else:
            #print "Arrow shot"
            print "\n------->>>>>>>>>>--------->\n"
            self.action = self.action + 1
            if self.env.scream == True:
                #print "scream heard"
                print "\n---------X_X------------\n"
                       
        '''
        too tired to write any comment
        see chapter 8 ALGO HYBRID-AGENT-SEARCH 
        '''                
    def HybridSearch(self, sensor, t):
        (stench, gold, pit, bump, scream) = sensor
        #print sensor
        self.TELL((stench, gold, pit, bump, scream), t)
        
        safe = self.safeList(t)
        
        size = self.env.size
        #print "safeList:", safe
        plan = []
        unvisit = []
        unvisit_and_safe = []
        possible_wumpus = []
        unvisited_and_not_unsafe = []
        
        if self.ASK("Grab", t, self.position) == True:
            self.foundgold = True
            return True#plan.append("Grab")
        
        if len(plan) == 0:
            for x in range(size):
                for y in range(size):
                    #if self.ASK("Loc", t, (x, y)) == False:
                    if self.visited[x][y] == 0:
                        unvisit.append((x, y))
                        
            #print "unvisited list:", unvisit                 
            for e in safe:
                if e in unvisit:
                    unvisit_and_safe.append(e)
            #print "unvisit_and_safe list:", unvisit_and_safe 
            
            # plan route
            #print "position, unvisit_and_safe, unvisit", self.position, unvisit_and_safe, unvisit
            plan = self.planRoute(self.position, unvisit_and_safe, safe)
            #print "plan unvisit and safe plan:", plan
            if len(plan) != 0:
                self.letsGo(plan)#self.position = (plan[0][0], plan[0][1])
        if len(plan) == 0 and self.ASK("HaveArrow", t, self.position) == True:
            for x in range(size):
                for y in range(size):
                    if self.ASK("NoWumpus", t, (x, y)) == False:
                        possible_wumpus.append((x,y))
            #print "possible wumpus list:", possible_wumpus 
            plan = self.planShoot(self.position, possible_wumpus, t)
            #print "plan shoot", plan
            if len(plan) != 0:
               self.letsGo(plan) 
        if len(plan) == 0:
             not_unsafe = []
             for x in range(size):
                for y in range(size):
                    if not self.ASK("NoOK", t, (x, y)) == True:
                        not_unsafe.append((x, y))
            #
             for e in unvisit:
                if e in not_unsafe and( not e in unvisited_and_not_unsafe):
                    unvisited_and_not_unsafe.append(e)
             plan = self.planRoute(self.position, unvisited_and_not_unsafe, safe) 
             #print "plan unvisited and not unsafe:", unvisited_and_not_unsafe
             if len(plan) != 0:
                 e = plan[0]
                 if (e[0],e[1]) != self.position:
                     self.letsGo(plan)
             
        if len(plan) == 0:
            return False#plan = self.planRoute(self.position, [(1,1)], )
        
        return True
        ''' search gold in current map'''
    
    def search(self):
        # search gold
        self.printMap()
        
        ## clean up files
#        open("rules.txt", 'w+').read()
#        open("rules.txt", 'w+').close()
#        open('KBQuery.txt', 'w+').read()
#        open('KBQuery.txt', 'w+').close()
        while not (self.isdead or self.foundgold):

            sensor = self.env.sense(*self.position)
            act    = self.HybridSearch(sensor, self.action)
            #self.action = self.action + 1
            if self.position == self.env.Wumpcoord and not self.env.scream: #or self.position in self.env.Pitcoord:
                self.isdead = True
                print "you were eaten by wumpus. "
                return False
                
            elif self.position in self.env.Pitcoord:
                self.isdead = True
                print "you fell into pit."
                return False
                            
            elif self.foundgold == True:
                print "Gold found."
                return True
            # if not invoke print function in HybridSearch()
            elif act == False:
                print "cannot find gold, go back"
                return False
                #self.printMap()
                #self.action = self.action + 1
            #self.isdead = True
        return Fal   
    def printMap(self):
        
        for x in range(self.env.size):
            print"|",
            for y in range(self.env.size):
                (wumpus,gold, pit) = self.env.map[(x,y)]
                print ("%s%s%s%s|" % ( "p" if pit else " ", "w" if wumpus else " ", "g" if gold else " ", "A" if self.position == (x,y) else " ")),
            #print"\n"
            print"\n"
        print "\n"        
###                        
#if __name__ == "__main__":
#    env = envWorld.WumpusWorld("./maps/4_0")
#    logic = logicEngine.Engine();
#    agent = HybridAgent(env, logic)
#    
#    agent.search()
#    
    
#    loc = (3,2)
#    agent.updateLoc(loc)
    
#    sensor = agent.env.sense(*loc)
#    print "Wumpus,gold,pit,bump,scream",
#    print sensor
#    agent.TELL(sensor, agent.action)
#    print "OK?",
#    agent.ASK("OK", agent.action, agent.position)
#    print "Grab?",
#    agent.ASK("Grab", agent.action, agent.position)
#    agent.env.printEnv()
          
            