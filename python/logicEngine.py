
import os
import subprocess

''' load current state, put it into prove9 and return result '''
class Engine(object):

    def query(self, query):
        #start the process
        com = "./prover9"
        process = subprocess.Popen([com, "-f", query], stdin=subprocess.PIPE,\
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        #give the process the body of logical rules and facts
        process.communicate(query)
        
        if process.returncode == 1:
            print query
            raise Exception("syntax error!")
        
        #prover 9 only exits with status 0 when the query was found to be true
        return process.returncode == 0
        
        
#if __name__ == "__main__":
#    logic = Engine();
#    r = logic.query("kbIn.txt")
#    print r        