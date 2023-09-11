#!/usr/bin/env python

"""This is the Controller Starter Code for ECE50863 Lab Project 1
Author: Xin Du
Email: du201@purdue.edu
Last Modified Date: December 9th, 2021
"""

import sys
from datetime import date, datetime
import socket
from queue import PriorityQueue as prioq
import threading as thd
import time

# Please do not modify the name of the log file, otherwise you will lose points because the grader won't be able to find your log file
LOG_FILE = "Controller.log"
TIMEOUT = 6
K_TIME = 2

glob_links = []
glob_routes = []
glob_rem_links = []
glob_rem_routes = []
glob_swAddresses = []
glob_inactive = []

# Those are logging functions to help you follow the correct logging standard

# "Register Request" Format is below:
#
# Timestamp
# Register Request <Switch-ID>

def register_request_received(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Request {switch_id}\n")
    write_to_log(log)

# "Register Responses" Format is below (for every switch):
#
# Timestamp
# Register Response <Switch-ID>

def register_response_sent(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Response {switch_id}\n")
    write_to_log(log) 

# For the parameter "routing_table", it should be a list of lists in the form of [[...], [...], ...]. 
# Within each list in the outermost list, the first element is <Switch ID>. The second is <Dest ID>, and the third is <Next Hop>, and the fourth is <Shortest distance>
# "Routing Update" Format is below:
#
# Timestamp
# Routing Update 
# <Switch ID>,<Dest ID>:<Next Hop>,<Shortest distance>
# ...
# ...
# Routing Complete
#
# You should also include all of the Self routes in your routing_table argument -- e.g.,  Switch (ID = 4) should include the following entry: 		
# 4,4:4,0
# 0 indicates ‘zero‘ distance
#
# For switches that can’t be reached, the next hop and bandwidth should be ‘-1’ and ‘9999’ respectively. (9999 means infinite distance so that that switch can’t be reached)
#  E.g, If switch=4 cannot reach switch=5, the following should be printed
#  4,5:-1,9999
#
# For any switch that has been killed, do not include the routes that are going out from that switch. 
# One example can be found in the sample log in starter code. 
# After switch 1 is killed, the routing update from the controller does not have routes from switch 1 to other switches.

def routing_table_update(routing_table):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append("Routing Update\n")
    for row in routing_table:
        log.append(f"{row[0]},{row[1]}:{row[2]},{row[3]}\n")
    log.append("Routing Complete\n")
    write_to_log(log)

# "Topology Update: Link Dead" Format is below: (Note: We do not require you to print out Link Alive log in this project)
#
#  Timestamp
#  Link Dead <Switch ID 1>,<Switch ID 2>

def topology_update_link_dead(switch_id_1, switch_id_2):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Link Dead {switch_id_1},{switch_id_2}\n")
    write_to_log(log) 

# "Topology Update: Switch Dead" Format is below:
#
#  Timestamp
#  Switch Dead <Switch ID>

def topology_update_switch_dead(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Switch Dead {switch_id}\n")
    write_to_log(log) 

# "Topology Update: Switch Alive" Format is below:
#
#  Timestamp
#  Switch Alive <Switch ID>

def topology_update_switch_alive(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Switch Alive {switch_id}\n")
    write_to_log(log) 

def write_to_log(log):
    with open(LOG_FILE, 'a+') as log_file:
        log_file.write("\n\n")
        # Write to log
        log_file.writelines(log)

def setNeighborAddresses(neighbors):
    for i in neighbors.keys():
        for j in neighbors[i][1]:
            neighbors[i][2].append(neighbors[j][0])


def entrytoStr(entry):
    msg = ''

    msg = entry[0][0][0] + '~' + str(entry[0][0][1]) + '|'

    for k in entry[1]:
        msg += ' '
        msg += str(k)

    msg += '|'

    for k in entry[2]:
        msg += ' '
        msg += k[0][0] + '~' + str(k[0][1])


    return msg


def findNeighbors(links):

    neighbors = {}

    for i in range(len(links)):
        links[i] = links[i].split(' ')
        for j in range(len(links[i])):
            links[i][j] = int(links[i][j])

        if links[i][0] not in neighbors.keys():
            neighbors[links[i][0]] = ([],[],[])
            neighbors[links[i][0]][1].append(links[i][1])
        else:
            neighbors[links[i][0]][1].append(links[i][1])

            
        if links[i][1] not in neighbors.keys():
            neighbors[links[i][1]] = ([],[],[])
            neighbors[links[i][1]][1].append(links[i][0])
        else:
            neighbors[links[i][1]][1].append(links[i][0])
    
    return neighbors

def buildGraph(links,numlinks):
    g = Graph(numlinks)
    for i in links:
        g.newConnect(i[0],i[1],i[2])
    return g

class Graph:
    def __init__(self, numVert):
        self.vertex = numVert
        self.edges = [[-1 for i in range(numVert)] for j in range(numVert)]
        self.visited = []
        self.path = [[] for j in range(numVert)]
    
    def newConnect(self, x, y, length):
        self.edges[y][x] = length
        self.edges[x][y] = length

def rich_dijkstra(graph, begin):
    final_minCost = {curr:9999 for curr in range(graph.vertex)}
    
    final_minCost[begin] = 0
    graph.path[begin].append(begin)

    pq = prioq()
    pq.put((0, begin))

    while not pq.empty():
        (dist, topVert) = pq.get()
        graph.visited.append(topVert)

        for adj in range(graph.vertex):
            if graph.edges[topVert][adj] != -1:
                distance = graph.edges[topVert][adj]
                if adj not in graph.visited:
                    ogLen = final_minCost[adj]
                    newLen = final_minCost[topVert] + distance
                    
                    if newLen < ogLen:
                        pq.put((newLen, adj))
                        final_minCost[adj] = newLen

                        graph.path[adj] = []
                        for i in graph.path[topVert]:
                            graph.path[adj].append(i)
                        graph.path[adj].append(adj)

    res = {}
    for i in range(graph.vertex):
        res[i] = (graph.path[i],final_minCost[i])
        
    return res

def encodeRoute(rt):
    msg = 'rt'
    for i in rt:
        for j in range(4):
            msg += str(i[j])
            msg += ' '

    return(msg)

def encodeAddr(addrs):
    msg = 'true addrs:'

    for a in range(len(addrs)):
        msg += ' ' + str(a) + '-' + str(addrs[a][0]) + '_' + str(addrs[a][1])
    
    return msg


def sendRoutingUpdate(svSck,route,recipients,ids):
    for i in range(len(ids)):
        currRt = []
        for j in route:
            if j[0] == ids[i]:
                currRt.append(j)
        msg = encodeRoute(currRt)
        #print('recip:', recipients[i])
        svSck.sendto(msg.encode(),recipients[i])

        msg_addr = encodeAddr(glob_swAddresses)
        svSck.sendto(msg_addr.encode(),recipients[i])

def updateRouting(links,switches):
    #print(links)
    #print(switches)
    d = []
    num_sw = len(switches)
    resarr = []

    for i in switches:
       
        G = buildGraph(links,num_sw)
        res = rich_dijkstra(G,i)
        resarr.append(res)



    routearr = [[0 for i in range(4)] for j in range(num_sw * num_sw)]

    longarr = []

    for i in range(num_sw):
        for j in switches:
            if len(resarr[i][j][0]) == 0:
                hop = -1
            elif len(resarr[i][j][0]) == 1:
                hop = resarr[i][j][0][0]
            else:
                hop = resarr[i][j][0][1]
            longarr.append(i)
            longarr.append(j)
            longarr.append(hop)
            longarr.append(resarr[i][j][1])

    for i in range(num_sw*num_sw):
        routearr[i][0] = longarr.pop(0)
        routearr[i][1] = longarr.pop(0)
        routearr[i][2] = longarr.pop(0)
        routearr[i][3] = longarr.pop(0)

    toRem = []
    for j in glob_inactive:
        for i in range(num_sw*num_sw):
            if routearr[i][0] == j:
                toRem.append(routearr[i])
    
    for k in toRem:
        routearr.remove(k)

    return(routearr)

def updateSWaddress(swid,addr):
    # assume 0 index
    glob_swAddresses[swid] = addr

def addNode(swid):
    toDelete = []
    print('glob links start addnode:',glob_links)
    print('rem links start addnode:',glob_rem_links)

    for l in range(len(glob_rem_links)):
        if glob_rem_links[l][0] == swid or glob_rem_links[l][1] == swid:
            glob_links.append(glob_rem_links[l])
            toDelete.append(glob_rem_links[l])
    
    if len(toDelete) != 0:
        for i in toDelete:
            glob_rem_links.remove(i)

    print('glob links end addnode:',glob_links)
    print('rem links end addnode:',glob_rem_links)
    #print('all links including new:',glob_links)


def removeNode(swid):
    print('glob links start remnode:',glob_links)
    print('rem links start remnode:',glob_rem_links)
    toDelete = []

    for l in range(len(glob_links)):
        if glob_links[l][0] == swid or glob_links[l][1] == swid:
            glob_rem_links.append(glob_links[l])
            toDelete.append(glob_links[l])
    
    if len(toDelete) != 0:
        for i in toDelete:
            glob_links.remove(i)
    
    print('glob links end remnode:',glob_links)
    print('rem links end remnode:',glob_rem_links)
    #print('removed links:',glob_rem_links)

def removeLink(linkTuple):
    toDelete = []

    for l in range(len(glob_links)):
        if (glob_links[l][0] == linkTuple[0] and glob_links[l][1] == linkTuple[1]) or (glob_links[l][0] == linkTuple[1] and glob_links[l][1] == linkTuple[0]):
            glob_rem_links.append(glob_links[l])
            toDelete.append(glob_links[l])
    
    if len(toDelete) != 0:
        for i in toDelete:
            glob_links.remove(i)
    
    #print('removed links:',toDelete,'list of removed links',glob_rem_links)

def decodeLink(inp):
    inp = inp.split(' ')[1]
    inp = inp.split('-')
    #print('inp test',inp[0],inp)

    return(int(inp[0]),int(inp[1]))

def listenAlive(servSck,numsw,switches,neighbors):
    # whole function assumes 0 indexed switch numbers
    active = [0] * numsw
    numDead = 0
    while(True):
        print('glob links at start:',glob_links)
        print('rem links at start:',glob_rem_links)
        numActive = 0
        for i in range(numsw):
            if active[i] == 1:
                active[i] = 0
        
        end = time.time() + TIMEOUT

        # wait for keep alive messages for all switches
        #print('before key while',active)
        while(end - time.time() > 0):
            servSck.settimeout(end - time.time())
            try:
                currSw = servSck.recvfrom(1024)
            except:
                #print('one or more switches disconnected')
                pass

            data = currSw[0].decode()
            if(data[0] != 'D' and data[0] != 'A'):
    
                swid = int(data[0])
                ##print('received data:',swid, 'with left time',end - time.time())
                if active[swid] != 1:
                    numActive += 1

                # check for reactivation
                if active[swid] == 2:
                    numDead -= 1
                    #print('dead switch has become alive')
                    
                    updateSWaddress(swid,currSw[1])
                    msgconf = entrytoStr(neighbors[swid])

                    # send register response to switch that has reconnected
                    servSck.sendto(msgconf.encode(),glob_swAddresses[swid])

                    topology_update_switch_alive(swid)
                    glob_inactive.remove(swid)
                    addNode(swid)
                    new_routearr = updateRouting(glob_links,list(range(numsw)))
                    routing_table_update(new_routearr)
                    sendRoutingUpdate(servSck,new_routearr,glob_swAddresses,list(range(numsw)))

                active[swid] = 1
            
            elif(data[0] == 'D'):
                # handle link disconnect update and update routing accordingly
                # and send it out
                toDelete = decodeLink(data)
                if (toDelete[0] not in glob_inactive) and (toDelete[1] not in glob_inactive):
                    cancel = False
                    for l in range(len(glob_rem_links)):
                        if (glob_rem_links[l][0] == toDelete[0] and glob_rem_links[l][1] == toDelete[1]) or (glob_rem_links[l][0] == toDelete[1] and glob_rem_links[l][1] == toDelete[0]):
                            cancel = True
                            print('canceled')
                    if not cancel:
                        topology_update_link_dead(toDelete[0],toDelete[1])
                        removeLink(toDelete)
                        new_routearr = updateRouting(glob_links,list(range(numsw)))
                        routing_table_update(new_routearr)
                        sendRoutingUpdate(servSck,new_routearr,glob_swAddresses,list(range(numsw)))
                

            elif(data[0] == 'A'):
                #print('received alive signal:',data)
                #print('shouldnt reach this case, but included it to print error')
                pass
                
        
        #print('after key while',active)
        # check if there are any dead switches - right now shouldnt trigger
    
        for i in range(numsw):
            if active[i] == 0:
                numDead += 1
                topology_update_switch_dead(i)
                glob_inactive.append(i)
                removeNode(i)
                new_routearr = updateRouting(glob_links,list(range(numsw)))
                routing_table_update(new_routearr)
                sendRoutingUpdate(servSck,new_routearr,glob_swAddresses,list(range(numsw)))
                active[i] = 2

def main():
    #Check for number of arguments and exit if host/port not provided
    num_args = len(sys.argv)
    if num_args < 3:
        print ("Usage: python controller.py <port> <config file>\n")
        sys.exit(1)
    
    # Write your code below or elsewhere in this file

    # open file and copy in each line, as well as find the number of switches
    with open(sys.argv[2], 'r') as cfg_file:
        num_sw = int(cfg_file.readline())
        links = cfg_file.readlines()
    
    # neighbors is a dict that will keep track of addresses and neighbors for each switch
    # make sure to sort it by key value
    neighbors = findNeighbors(links)
    neighKeys = list(neighbors.keys())
    neighKeys.sort()
    neighbors = {i: neighbors[i] for i in neighKeys}

    # links is a 2d array containing each line of the config

    
    # prepare the controller to bind to the given port
    servSock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    udp_host = socket.gethostname()	
    udp_port = int(sys.argv[1])	# well known

    # bind the controller to the given port
    servSock.bind((udp_host,udp_port))

    sw_ct = 0 # current count of switches received

    while sw_ct != num_sw:
        #print("Waiting for switch...")
        data = servSock.recvfrom(1024)    
        currID = int(data[0].decode()) # receive data from switch

        currAddress = data[1] # get the host/port of the switch

        neighbors[currID][0].append(currAddress) # insert host/port in 1st dict entry
        sw_ct += 1

        #print("Received Messages:",data)
        register_request_received(currID) # acknowledge the reception of the switch
    
    setNeighborAddresses(neighbors)
    
    for i in neighbors.keys():

        # convert the dict entry into a string so it can be binary
       msg = entrytoStr(neighbors[i])

        # send each key of the dict along with its entry back to each switch
       register_response_sent(i)
       servSock.sendto(msg.encode(),neighbors[i][0][0])
    
    routes = updateRouting(links,neighbors.keys())


    routing_table_update(routes)

    for g in links:
        glob_links.append(g)
    for r in routes:
        glob_routes.append(r)

    for i in neighbors.keys():
        glob_swAddresses.append(neighbors[i][0][0])

    #print(glob_swAddresses)
    sendRoutingUpdate(servSock,routes,glob_swAddresses,list(neighbors.keys()))
    
    # start thread listening for keep alive signals
    c1 = thd.Thread(target = listenAlive,args = (servSock,num_sw,neighbors.keys(),neighbors))
    #print('before running thread')
    c1.start()
    #thd.start_new_thread(listenTopol)
    

if __name__ == "__main__":
    main()