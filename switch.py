#!/usr/bin/env python

"""This is the Switch Starter Code for ECE50863 Lab Project 1
Author: Xin Du
Email: du201@purdue.edu
Last Modified Date: December 9th, 2021
"""

import sys
from datetime import date, datetime
import socket
import threading as thd
import time


# Please do not modify the name of the log file, otherwise you will lose points because the grader won't be able to find your log file
LOG_FILE = "switch#.log" # The log file for switches are switch#.log, where # is the id of that switch (i.e. switch0.log, switch1.log). The code for replacing # with a real number has been given to you in the main function.
TIMEOUT = 6
K_TIME = 2
glob_neighbors = {}
# Those are logging functions to help you follow the correct logging standard

# "Register Request" Format is below:
#
# Timestamp
# Register Request Sent

def register_request_sent():
    #print("called")
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Request Sent\n")
    write_to_log(log)

# "Register Response" Format is below:
#
# Timestamp
# Register Response Received

def register_response_received():
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Response received\n")
    write_to_log(log)

# For the parameter "routing_table", it should be a list of lists in the form of [[...], [...], ...].
# Within each list in the outermost list, the first element is <Switch ID>. The second is <Dest ID>, and the third is <Next Hop>.
# "Routing Update" Format is below:
#
# Timestamp
# Routing Update
# <Switch ID>,<Dest ID>:<Next Hop>
# ...
# ...
# Routing Complete
#
# You should also include all of the Self routes in your routing_table argument -- e.g.,  Switch (ID = 4) should include the following entry:
# 4,4:4

def routing_table_update(routing_table):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append("Routing Update\n")
    for row in routing_table:
        log.append(f"{row[0]},{row[1]}:{row[2]}\n")
    log.append("Routing Complete\n")
    write_to_log(log)

# "Unresponsive/Dead Neighbor Detected" Format is below:
#
# Timestamp
# Neighbor Dead <Neighbor ID>

def neighbor_dead(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Neighbor Dead {switch_id}\n")
    write_to_log(log)

# "Unresponsive/Dead Neighbor comes back online" Format is below:
#
# Timestamp
# Neighbor Alive <Neighbor ID>

def neighbor_alive(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Neighbor Alive {switch_id}\n")
    write_to_log(log)

def write_to_log(log):
    with open(LOG_FILE, 'a+') as log_file:
        log_file.write("\n\n")
        # Write to log
        log_file.writelines(log)

def real(val):
    if val == '':
        return False
    else:
        return True

def notx(line):
    if line == 'x':
        return False
    else:
        return True

def extractNeighbors(rawStr,excpt):
    partition = rawStr.split('|')

    neighList = list(filter(real,partition[1].split(' ')))
    addr_indiv = list(filter(real,partition[2].split(' ')))

    toRemove = []
    for i in excpt:
        toRemove.append(neighList.index(i))

    for j in toRemove:
        addr_indiv[j] = 'x'
        neighList[j] = 'x'

    addr_indiv = list(filter(notx,addr_indiv))
    neighList = list(filter(notx,neighList))
    for n in range(len(neighList)):
        neighList[n] = int(neighList[n])

    numNeigh = len(neighList)

    each_arr = []

    for i in addr_indiv:
        params = i.split('~')
        each_arr.append(params[0])
        each_arr.append(int(params[1]))

    neighbors = []
    for j in range(numNeigh):
        neighbors.append((each_arr.pop(0),each_arr.pop(0)))

    return neighList,neighbors

def decodeRoute(rt):
    rt = rt.split('rt')[1]
    raw = []

    rt_split = list(filter(real,rt.split(' ')))

    for i in rt_split:
        raw.append(int(i))

    lenRt = len(raw)//4

    route = [[0 for i in range(4)] for j in range(lenRt)]

    for i in range(lenRt):
        for j in range(4):
            route[i][j] = raw.pop(0)

    return route

def sendAlive(swSock,control_addr,id,noSend):
    msg = str(id) + ' - alive'
    while(True):
        swSock.sendto(msg.encode(),control_addr)
        for i in glob_neighbors.keys():
            if i != noSend:
                swSock.sendto(msg.encode(),glob_neighbors[i])
        time.sleep(K_TIME)

def link_dead(swSock,myid,swid,control_addr):
    msg = 'Deadlink ' + str(myid) + '-' + str(swid)
    swSock.sendto(msg.encode(),control_addr)

def decodeAddr(inp):
    #print('starting decode')
    inp = inp.split('true addrs:')[1]
    raw = {}

    #print(inp)
    inp_split = list(filter(real,inp.split(' ')))
    #print('inp split:',inp_split)

    for i in inp_split:
        tmp = i.split('-')
        #print(tmp)
        tmpa = tmp[1].split('_')
        #print(tmpa)
        raw[int(tmp[0])]= (tmpa[0],int(tmpa[1]))

    #print('glob_neighbors;',glob_neighbors)
    #print('raw',raw)

    for g in glob_neighbors.keys():
        glob_neighbors[g] = raw[g]

    #print('successfully updated glob_neighbors')

def send_link_alive(swSock,cont_addr,myid,swid):
    msg = 'Alivelink ' + str(myid) + '-' + str(swid)
    swSock.sendto(msg.encode(),cont_addr)

def listenNeigh(recSock,ids,myid,cont_addr):
    numid = len(ids)
    active = {}
    waitingForUpdate = 0
    for i in ids:
        active[i] = 0

    while(True):
        numActive = 0
        for i in ids:
            if active[i] == 1:
                active[i] = 0

        end = time.time() + TIMEOUT

        # wait for keep alive messages for all switches
        while(end - time.time() > 0):
            swid = -2
            recSock.settimeout(end - time.time())
            try:
                #print('Waiting at',end - time.time(),' seconds left')
                curr = recSock.recvfrom(1024)
                data = curr[0].decode()
                #print('received msg:',data,'0th:',data[0])
                if data[0] != 'r' and data[0] != 't':
                    #print('received a swid call: ',data)
                    swid = int(data[0])
                elif data[0] == 'r':
                    #print('received an update')
                    waitingForUpdate = 0
                    route = decodeRoute(data)
                    #print(route)
                    routing_table_update(route)
                elif data[0] == 't':
                    #print('new addresses')
                    glob_neighbors = decodeAddr(data)
            except:
                #print('cant receive anything')
                pass

            #print('ids: ',ids,'swid: ',swid, 'if: ',swid in ids)
            if swid in ids and active[swid] != 1:
                numActive += 1
                #print('added new sw with',end-time.time(),' seconds left before timeout')
                # check for reactivation
                if active[swid] == 2:
                    neighbor_alive(swid)
                    if waitingForUpdate == 1:
                        send_link_alive(recSock,cont_addr,myid,swid)
                        #print('relink- link is now reachable')
                active[swid] = 1
        #print(active)

        # check if there are any dead switches
        for i in ids:
            if active[i] == 2 and waitingForUpdate == 1:
                #link_dead(recSock,myid,i,cont_addr)
                waitingForUpdate = 0

        for i in ids:
            if active[i] == 0:
                neighbor_dead(i)
                link_dead(recSock,myid,i,cont_addr)
                active[i] = 2
                waitingForUpdate = 1





def main():
    global LOG_FILE

    #Check for number of arguments and exit if host/port not provided
    num_args = len(sys.argv)
    if num_args < 4:
        print ("switch.py <Id_self> <Controller hostname> <Controller Port>\n")
        sys.exit(1)

    my_id = int(sys.argv[1])
    LOG_FILE = 'switch' + str(my_id) + ".log"

    # Write your code below or elsewhere in this file

    #send register request

    controller_hostname = sys.argv[2]
    controller_port = int(sys.argv[3])

    currSock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    udp_host = socket.gethostname() # likely needs to be changed to input arg
    print(udp_host)
    udp_port = controller_port # well known port
    #print(udp_host,udp_port)

    id = sys.argv[1] # get id of current switch

    currSock.sendto(id.encode(),(udp_host,udp_port)) # send id and address
    register_request_sent() # log that request was sent


    data = currSock.recvfrom(1024) # wait for the response to the network initialization
    #print("Received Messages:",data[0].decode()) # show the neighbors, status, and address from controller
    toFail = [] #dummy variable, ignore
    newFail = -9998
    if num_args == 6:
        if sys.argv[4] == '-f':
            newFail = int(sys.argv[5])
    neigh_ids,neigh_addr = extractNeighbors(data[0].decode(),toFail)
    register_response_received() # log the controller response
    data = currSock.recvfrom(1024) # wait for the first routing update
    route = decodeRoute(data[0].decode())
    #print(route)
    routing_table_update(route)

    #print(neigh_addr)

    for i in range(len(neigh_ids)):
        glob_neighbors[neigh_ids[i]] = neigh_addr[i]

    # start thread to send keep alive signals
    s1 = thd.Thread(target = sendAlive,args = (currSock,(udp_host,udp_port),id,newFail))
    #print('before starting s1')

    s1.start()

    #thd.Thread(target = listenAlive,args = (currSock,(len(neigh_addr),id,(udp_host,udp_port))))
    ##print('ids: ',neigh_ids)

    t2 = thd.Thread(target=listenNeigh,args = (currSock,neigh_ids,id,(udp_host,udp_port)))
    t2.start()

if __name__ == "__main__":
    main()
