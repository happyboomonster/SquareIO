import sys
sys.path.insert(0, "libraries") #make sure we can import our local libraries
import _thread
import socket
import random
import pygame #only used for it's time.Clock() class
import math
import netcode
import time

#constants for starting Square() objects
consts_lock = _thread.allocate_lock()
SIZE = 10
FOOD_EXCHANGES = 4 #we give clients food data every 1 in FOOD_EXCHANGES packets.

#round setup variables
timestart = None #when we started the round
roundtime = 100 #100 second round time
roundstats_lock = _thread.allocate_lock()
lobbytime = 15 #time the game waits for players before starting another round (seconds)
lobbystart = None #when the lobby time started
lobbystats_lock = _thread.allocate_lock()
game_phase = "wait" #the phase of our game: 'wait' or 'ingame'
game_phase_lock = _thread.allocate_lock()
timeleft = 0 #covered under the game_phase_lock(), used to tell how much time is left in either "wait" or "ingame" mode

#a broader lock object, for making sure we only add one client to the game at a time
join_lock = _thread.allocate_lock()

#a lock for print()
print_lock = _thread.allocate_lock()

#a lock for math.sqrt()
sqrt_lock = _thread.allocate_lock()

#how many clients do we have connected?
clients = 0
clients_lock = _thread.allocate_lock()

#on the last thread we started, did a client connect to it yet?
client_connected = False
client_connected_lock = _thread.allocate_lock()

#obj is a large list which holds the data for EVERY square
obj = []
obj_lock = _thread.allocate_lock()

#the port we're hosting the server on
while True:
    PORT = input("Port#? ")
    try:
        PORT = int(PORT)
        break
    except:
        print("Invalid Port#. Retry...")

#the IP of our server
HOST_NAME = socket.gethostname()
IP = socket.gethostbyname(HOST_NAME)

#create a socket object
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create a socket object
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((IP, PORT))
s.listen() #wait for connections
print("[SERVER] Successfully established socket setup on " + str(IP)) #we don't need to print lock this because it's not within threads yet...

class Printer(): #class which allows threads to add messages to a queue which then gets printed by the main server thread @ 30 messages a minute
    def __init__(self):
        self.msgs = []
        self.msgs_lock = _thread.allocate_lock()

    def print_msgs(self): #prints all the queued messages
        with self.msgs_lock:
            for x in range(0,len(self.msgs)):
                with print_lock:
                    print(self.msgs[x])
            self.msgs = [] #clear the message cache

#create a printer object
printer = Printer()

def justify(string,size): #a function which right justifies a string
    if(size - len(list(string)) > 0):
        tmpstr = " " * (size - len(list(string)))
        string = tmpstr + string
    return string

def gather_data(inobj): #gathers the stats from a square object
    pos = str(inobj.pos)
    size = str(inobj.size)
    score = str(inobj.score)
    direction = str(inobj.direction)
    name = inobj.name
    connected = str(inobj.connected)
    Odata = "[" + pos + ",[" + size + " , " + score + " , " + direction + "], " + connected + " , " + "'" + name + "'" + "]" #next we join it all into one big string...
    return Odata

class Square(): #the square/player class
    def __init__(self,pos=[0,0]):
        self.pos = [pos]
        with consts_lock:
            self.size = [SIZE]
        self.score = 0
        self.direction = [[0.0, 0.0, 1.0]] #the third index is a speed multiplier used when splitting the square

        self.connected = True #does this player have a client connected to it?
        self.name = "default"
        self.clientnum = None #use this to make sure we're not sending this object back to where we got it from...
        self.food_diffs = [] #list which is used to transmit changes to the food list rather than re-transmitting the food list each frame
        self.size_diffs = [] #list which is used to transmit size changes to the player
        self.respawn = True #value is in seconds; basically gives a player a few seconds of invincability after respawning.

        self.eaten = [] #list which holds the eaten cells of this player (ik, kinda wierd ngl)

        self.speedT = 1 #pixels per tick
        self.speedS = self.speedT * 30 #pixels per second
        self.speedThreshold = 2 #due to ping, etc. we need to give people a little give/take regarding policing their speeds...
        self.slowdown = 0.3 #slowdown factor - bigger = slower
        self.shrinkfactor = 0.025 #how fast we shrink...

        self.pos_lock = _thread.allocate_lock()
        self.size_lock = _thread.allocate_lock()
        self.score_lock = _thread.allocate_lock()
        self.direction_lock = _thread.allocate_lock()
        self.name_lock = _thread.allocate_lock()
        self.clientnum_lock = _thread.allocate_lock()
        self.food_diffs_lock = _thread.allocate_lock()
        self.eaten_lock = _thread.allocate_lock()

    def shrink(self,TPS):
        for x in range(0,len(self.size)):
            if(self.size[x] > 20):
                try:
                    self.size_diffs.append([x,-(self.shrinkfactor * self.size[x]) / TPS])
                    self.size[x] -= (self.shrinkfactor * self.size[x]) / TPS
                except ZeroDivisionError: #if our TPS is 0, just don't shrink them this time...
                    pass

    def eat(self,other): #checks whether this Square() instance is completely surrounding another. if so, the other one's DEAD.
        selfposition = [] #list format: [[x1,y1,x2,y2], [x1,y1,x2,y2]]
        for x in range(0,len(self.pos)):
            tmpposition = [] #list format: [x1,y1,x2,y2]
            tmpposition.append(self.pos[x][0] - (self.size[x] / 2.0)) #x1
            tmpposition.append(self.pos[x][1] - (self.size[x] / 2.0)) #y1
            tmpposition.append(self.pos[x][0] + (self.size[x] / 2.0)) #x2
            tmpposition.append(self.pos[x][1] + (self.size[x] / 2.0)) #y2
            selfposition.append(eval(str(tmpposition)))
        otherposition = [] #list format: [[x1,y1,x2,y2], [x1,y1,x2,y2]]
        for x in range(0,len(other.pos)):
            tmpposition = [] #list format: [x1,y1,x2,y2]
            tmpposition.append(other.pos[x][0] - (other.size[x] / 2.0)) #x1
            tmpposition.append(other.pos[x][1] - (other.size[x] / 2.0)) #y1
            tmpposition.append(other.pos[x][0] + (other.size[x] / 2.0)) #x2
            tmpposition.append(other.pos[x][1] + (other.size[x] / 2.0)) #y2
            otherposition.append(eval(str(tmpposition)))
        for meself in range(0,len(selfposition)): #now we check collision: one of my cells is eating any of his cells?
            for otherself in range(0,len(otherposition)):
                if(selfposition[meself][0] < otherposition[otherself][0]):
                    if(selfposition[meself][2] > otherposition[otherself][2]):
                        if(selfposition[meself][1] < otherposition[otherself][1]):
                            if(selfposition[meself][3] > otherposition[otherself][3]):
                                self.size_diffs.append([meself,otherposition[otherself][2] - otherposition[otherself][0]]) #add a size change to the player's size_diffs list
                                self.size[meself] += otherposition[otherself][2] - otherposition[otherself][0] #change the server's recognition of the player's size
                                return [meself,otherself] #we[meself] ate something[otherself]!!!
        return False #if we didn't eat anything?

    def set_stats(self,inlist,clientnum): #ez way to decode a set of stats and verify that the client IS NOT CHEATING
        self.pos = inlist[0][:]
        self.size = inlist[1][0] #then we can sync our sizes
        self.direction = inlist[1][2][:]
        self.name = inlist[3]

#food constants
FOOD_MAX = 50 #maximum food allowed on arena at one time
FOOD_THRESHOLD = 35 #minimum food amount we can have onscreen before the server spawns more...

#manage the client setups and food population
food = [] #create some food
food_lock = _thread.allocate_lock()
for x in range(0,FOOD_MAX): #create 75 pieces of food
    food.append(Square([random.randint(0,640),random.randint(0,480)])) #randomly choose a position
    food[len(food) - 1].size = [random.randint(2,7)] #give us a little bit of size variation...
    food[len(food) - 1].name = ""

#obj_and_food_lock = _thread.allocate_lock() #a lock for OBJ and Food [] at the same time

def manage_client(IP,PORT): #manages a single client connection
    global obj #obj is a large object which holds ALL the data for ALL players.
    global clients
    global s
    global client_connected
    global game_phase
    global timeleft
    #a constant which defines our goal Packets Per Second
    GOAL_PPS = 10

    #whether we need the client to respawn
    RESPAWN = False
    
    #we are still going ahead with this, aren't we?
    running = True

    #our packet count
    packet_ct = 0 #reset this once it reaches FOOD_EXCHANGES.
    
    #create a socket connection to the client
    buffersize = 10 #default buffer size
    Cs, Caddress = s.accept() #connect to a client
    Cs.settimeout(40) #set a timeout of (?) seconds for Cs
    with printer.msgs_lock: #let the WORLD of terminal know...how exciting
        printer.msgs.append("[OK] Client at " + str(Caddress) + " connected successfully.")

    #next, we have to let the client know our default buffer size.
    with printer.msgs_lock:
        printer.msgs.append("[INFO] Sending buffersize to client " + str(Caddress))
    Cs.send(bytes(justify(str(buffersize),buffersize), "utf-8")) #it must occupy (buffersize) characters

    #then we need to receive a confirmation signal so we know everything is working.
    with printer.msgs_lock:
        printer.msgs.append("    [WAIT] Waiting for acknowledge from client " + str(Caddress))
    try:
        confirm = Cs.recv(buffersize)
    except socket.timeout:
        with printer.msgs_lock:
            printer.msgs.append("    [ERROR] Failed to recieve data from client...")
            running = False #we're NOT going ahead with this!
    if(running): #we made it?
        with printer.msgs_lock: #then let the USER know
            printer.msgs.append("    [OK] Client at " + str(Caddress) + " acknowledged signal!")

    if(running):
        #create a square object for our client to manipulate
        clientnum = None
        with join_lock:
            with obj_lock:
                for x in range(0,len(obj)):
                    if(obj[x].connected == False):
                        clientnum = x + 1 #give us a client number
                        obj[clientnum - 1].connected = False #we don't want other people to be able to eat us quite yet...
                        obj[clientnum - 1].pos = [[random.randint(0,640),random.randint(0,480)]]
                        obj[clientnum - 1].direction = [[0.0, 0.0, 1.0]]
                        with consts_lock:
                            obj[clientnum - 1].size = [SIZE]
            with clients_lock:
                if(clientnum == None):
                    clients += 1
            with obj_lock:
                if(clientnum == None): #we couldn't find a free client position/number?
                    obj.append(Square([random.randint(0,640),random.randint(0,480)]))
                    clientnum = clients #give us a client number

    #send the starting coords for the player
    if(running):
        with printer.msgs_lock:
            printer.msgs.append("[ATTEMPT] Sending start data for client " + str(clientnum))
        with obj_lock:
            tmpdata = gather_data(obj[clientnum - 1])
        try:
            netcode.send_data_noerror(Cs,buffersize,tmpdata)
        except: #we get an EOF error sometimes, and a Socket.timeout error sometimes too
            with printer.msgs_lock:
                printer.msgs.append("    [ERROR] Failed to send start data for client " + str(clientnum))
                running = False #we're NOT going ahead with this in this case...
    if(running): #we made it?
        with printer.msgs_lock:
            printer.msgs.append("    [OK] Send start data for client " + str(clientnum))

    #get the name of the player
    if(running):
        with printer.msgs_lock:
            printer.msgs.append("[ATTEMPT] Recieving name of client " + str(clientnum))
        try:
            payload = netcode.recieve_data_noerror(Cs,buffersize,evaluate=True)
        except:
            with printer.msgs_lock:
                printer.msgs.append("    [ERROR] Connection to client timed out...")
                running = False #this one's not getting through! Thought he was so sneaky...
    if(running):
        with obj_lock:
            obj[clientnum - 1].set_stats(payload,clientnum)
        with printer.msgs_lock:
            with obj_lock:
                printer.msgs.append("    [OK] Recieved client name " + str(obj[clientnum - 1].name))

    #now we send the state of all the food particles
    if(running):
        with printer.msgs_lock:
            printer.msgs.append("[ATTEMPT] Sending food particle states...")
        try:
            totalFdata = []
            with food_lock:
                Cs.send(bytes(justify(str(len(food)),10),'utf-8')) #send the length of our food list
                Cs.recv(buffersize) #wait for a confirmation signal
                for x in range(0,len(food)): #send each individual piece of food one at a time...
                    Fdata = gather_data(food[x])
                    totalFdata.append(eval(Fdata))
                netcode.send_data_noerror(Cs,buffersize,totalFdata)
            with printer.msgs_lock:
                printer.msgs.append("[OK] Successfully sent food particle states!")
        except: #uhoh, something happened...I just know it.
            with printer.msgs_lock:
                printer.msgs.append("   [ERROR] Failed to send food particle states!")
                running = False

    if(running): #we're still going?
        #send the player's client number
        Cs.send(bytes(justify(str(clientnum),10),'utf-8'))
        try:
            Cs.recv(10)
        except:
            running = False
            
    if(running): #we're STILL making it???
        Sclock = pygame.time.Clock() #make sure get our goal PPS
        with printer.msgs_lock: #we managed to connect, did we?
            printer.msgs.append("    [OK] Successfully joined server!")
        with client_connected_lock: #make sure the server thread knows that we got a client on us!
            client_connected = True
        with obj_lock: #NOW other players can eat us...
            obj[clientnum - 1].connected = True
            obj[clientnum - 1].respawn = False

    with game_phase_lock:
        Cgamephase = game_phase

    netpack = [] #a list which we send to the client each tick

    #then we need to start continually feeding with data...
    while running:
        with obj_lock:
            eatenprint = obj[clientnum - 1].eaten[:]
        with printer.msgs_lock:
            if(eatenprint != []):
                printer.msgs.append("[INFO] A player ate index " + str(eatenprint) + " of another player.")
        with obj_lock: #check some external variables if we've been eaten?
            netpack.append(obj[clientnum - 1].eaten[:]) #add "selfeaten" to netpack list
            obj[clientnum - 1].eaten = [] #clear the player's "eaten" cache
            
        with obj_lock: #create clone objects of OBJ which we send ot our client (created clones due to threadlock possibilities)
            objclone = obj[:]
        gatheredobjs = []
        for getobjs in range(0,len(objclone)):
            gatheredobjs.append(eval(gather_data(objclone[getobjs])))
        netpack.append(gatheredobjs) #add all the square data to a list
        
        #now we send data about changes in the food list...
        if(packet_ct % FOOD_EXCHANGES == 1): #but we're only sending food data every FOOD_EXCHANGES packets!
            with food_lock:
                Fdata = []
                for x in range(0,len(food)):
                    Fdata.append(eval(gather_data(food[x]))[:])
            netpack.append(Fdata[:]) #add the food stuff to the netpack list
        else:
            Fdata = None #we're not giving food data this packet...SAVE THE BANDWIDTH!
            netpack.append(Fdata) #add the food stuff to the netpack list

        if(Cgamephase == 'ingame'):
            with obj_lock: #make sure we shrink if we're getting too big!
                obj[clientnum - 1].shrink(Sclock.get_fps())
        with obj_lock: #now we send changes about the client's size data...
            sizeupdate = eval(str(obj[clientnum - 1].size_diffs))
            netpack.append(sizeupdate) #add our size update to netpack
            obj[clientnum - 1].size_diffs = [] #clear the size_diffs cache once its been sent

        #we have what I like to call a "Sync" session here...if the server wants to set you somewhere else, you're going there!
        Sdata = None
        with game_phase_lock:
            if(Cgamephase == 'wait' and game_phase == 'ingame'):
                RESPAWN = True #set a flag which lets us know that we needs to reset this player to [SIZE], speed 1
            Cgamephase = game_phase #sync our local Client-thread gamephase variable with the one in the lobbyhandler thread AFTER checking if a new round started
        with obj_lock:
            if(len(obj[clientnum - 1].pos) == 0): #we got eaten???
                RESPAWN = True
        with obj_lock:
            if(RESPAWN == True):
                obj[clientnum - 1].respawn = True #A player can't be eaten until this flag goes false.
                obj[clientnum - 1].size = [SIZE]
                obj[clientnum - 1].pos = [[random.randint(0,640),random.randint(0,480)]]
                obj[clientnum - 1].direction = [[0.0,0.0,1.0]]
                Sdata = eval(gather_data(obj[clientnum - 1]))
        netpack.append(Sdata) #add our sync data to the netpack list
        with game_phase_lock: #add our time/game phase data to netpack
            netpack.append([game_phase,timeleft])
        try:
            netcode.send_data(Cs,buffersize,netpack) #send our "netpack"
        except: #we didn't get a client response???
            running = False
            break
        netpack = [] #clear the netpack for next tick
        
        #Recieve client data...
        try:
            Cdata = netcode.recieve_data(Cs,buffersize,evaluate=True)
        except socket.timeout: #we're not getting any data in 5 SECONDS?? a ping of 15000 is unplayable, so the person probably disconnected.
            running = False
            break
        except ConnectionResetError: #a guaranteed disconnect? Connection DROPPED, player gets shoe.
            running = False
            break
        except ValueError: #we timed out, and as a result got '' instead of an int. ValueError occurs then...
            running = False
            break

        #now we need to decode the client's data...
        with obj_lock:
            if(Cdata != None): #if we managed to evaluate the data in Cdata successfully...
                if(RESPAWN == True): #we need to make sure the client respawned properly
                    if(Cdata == Sdata): #if the player DID respawn like we asked them...
                        obj[clientnum - 1].set_stats(Cdata,clientnum) #set the client's stats to our server
                        RESPAWN = False
                        obj[clientnum - 1].respawn = False
                    else: #the player dropped the respawn packet OR they're cheating?
                        RESPAWN = True
                else:
                    obj[clientnum - 1].set_stats(Cdata,clientnum) #*BOOM* - that was easy

        packet_ct += 1 #increase how many packets we've sent so far...

        Sclock.tick(GOAL_PPS) #try to get as many packet exchanges per second as we can
        
    with obj_lock:
        try: #we only need to change this flag if the person disconnected AFTER the player's object was created
            obj[clientnum - 1].connected = False
        except:
            pass
    with printer.msgs_lock:
        try:
            printer.msgs.append("[DISCONNECT, " + str(clientnum) + "] Client has disconnected from server.")
        except UnboundLocalError: #we didn't get so far as to even get a clientnum???
            printer.msgs.append("[DISCONNECT, UNKNOWN]")

def player_handler(): #checks if anyone ate anyone else, or if somebody ate food
    global food
    global obj
    global running
    global game_phase

    GOAL_TPS = 30 #how many cycles we wants this to run (ideally) per second

    Eclock = pygame.time.Clock() #keeps us running at the server TPS speed
    ETPS = 1 #how many ticks we're managing a second in this loop

    while True:
        with game_phase_lock: #create a copy of the current game phase state
            Egame_phase = game_phase
            
        with obj_lock: #update ALL the players' positions so that we can calculate eating food MUCH better
            for computesquares in range(0,len(obj)):
                for x in range(0,len(obj[computesquares].pos)):
                    obj[computesquares].pos[x][0] += obj[computesquares].direction[x][0] / ETPS * 1.0
                    obj[computesquares].pos[x][1] += obj[computesquares].direction[x][1] / ETPS * 1.0

        if(Egame_phase == 'ingame'): #we're ingame currently?
            with obj_lock: #check if anyone ate food?
                with food_lock:
                    for objects in range(0,len(obj)):
                        for x in range(0,len(food)):
                            if(obj[objects].respawn == True): #we're not going to let newly respawned players to eat.
                                continue
                            foodeaten = obj[objects].eat(food[x])
                            if(foodeaten != False): #so they ate the food...now we have to update a million players food lists...
                                obj[objects].size[foodeaten[0]] += food[x].size[foodeaten[1]] #make sure we grow that hungry player
                                del(food[x]) #delete the eaten food
                                loopcontinue = True
                                break #restart the calculations now that "food" is 1 index shorter than it should be
            with obj_lock: #check if anyone has eaten anyone else???
                for players in range(0,len(obj)):
                    if(obj[players].connected == False): #we're NOT checking collision for people who aren't there!
                        continue
                    elif(obj[players].respawn == True): #we're not letting newly respawned players get eaten, or eat!
                        continue
                    for others in range(0,len(obj)):
                        if(players == others): #we're NOT going to try eat ourselves...
                            continue
                        elif(obj[others].connected == False): #we're NOT checking collision for people who aren't there!
                            continue
                        elif(obj[others].respawn == True): #we're not letting newly respawned players get eaten, or eat!
                            continue
                        playereaten = obj[players].eat(obj[others]) #did someone eat somebody else?
                        if(playereaten != False):
                            with printer.msgs_lock:
                                printer.msgs.append("[INFO] [" + str(players) + "] ate [" + str(others) + "] at cell: Playereaten: " + str(playereaten) + " Size: " + str(obj[others].size) + " Position: " +  str(obj[others].pos) + " Direction: " + str(obj[others].direction))
                            obj[others].eaten.append(playereaten[1]) #now we gather the eaten data into a list
                            obj[others].size.pop(playereaten[1]) #delete the eaten player's cell
                            obj[others].direction.pop(playereaten[1])
                            obj[others].pos.pop(playereaten[1])
                            continue #move on to the next player since this one already ate someone this tick
        else: #we're not ingame currently:
            with obj_lock:
                for x in range(0,len(obj)):
                    obj[x].eaten = [] #clear the eaten list
                        
        Eclock.tick(GOAL_TPS) #let's get that ticking goin'!
        ETPS = Eclock.get_fps()

def round_handler(): #governs the timing of when waiting for players happens, and when the game starts
    global lobbytime
    global lobbystart
    global roundtime
    global roundstart
    global obj
    global game_phase
    global timeleft
    global SIZE

    start = False

    Rclock = pygame.time.Clock() #make sure this isn't running too fast and hogging all resources...
    GOAL_TPS = 5 #for this loop, we only need 5 ticks/second
    
    while True:
        with lobbystats_lock:
            lobbystart = time.time() #keep track of when we started waiting for players
        start = False
        while not start: #wait till game start
            with game_phase_lock: #keep track of how much time left in round
                timeleft = lobbytime - (time.time() - lobbystart)
            with lobbystats_lock:
                if((time.time() - lobbystart) >= lobbytime): #do we start the round? (we waited for lobbytime seconds already)
                    start = True
            with obj_lock:
                clients_ct = 0 #how many clients are ready to go?
                for x in range(0,len(obj)):
                    if(obj[x].connected == True):
                        clients_ct += 1
            if(clients_ct < 2): #we have less than two players in game?
                start = False #then DO NOT start the game, it would be *pointless*
        with roundstats_lock:
            roundstart = time.time() #starting time for game!
        with game_phase_lock:
            game_phase = "ingame" #let everyone know about something called GAME START
        with printer.msgs_lock:
            printer.msgs.append("[LOBBY] ingame")
        with obj_lock: #now that we're ingame, we need to reset everybody's size to [SIZE] again.
            with consts_lock:
                for x in range(0,len(obj)):
                    obj[x].size = [SIZE]
        while True: #wait till the round is over
            with game_phase_lock: #keep track of how much time left in round
                timeleft = roundtime - (time.time() - roundstart)
            with lobbystats_lock:
                if((time.time() - roundstart) >= roundtime): #round over?
                    break
        with game_phase_lock: #let all the clients know the game state
            game_phase = "wait"
        with printer.msgs_lock:
            printer.msgs.append("[LOBBY] waiting for players")

        Rclock.tick(GOAL_TPS)

clock = pygame.time.Clock()
_thread.start_new_thread(round_handler,()) #keep track of our round times
_thread.start_new_thread(player_handler,()) #track anyone eating anyone else...
while True:
    with clients_lock:
        old_clientct = clients #this is how many clients we *had*...
    with printer.msgs_lock: #debug
        printer.msgs.append("[SERVER] New Client thread initialized...")
    _thread.start_new_thread(manage_client,(IP,PORT)) #we start a thread to join a client up...
    while True: #wait for another client to connect, and handle other things in the meantime...
        clock.tick(1) #we don't need this loop running too quickly...
        with obj_lock: #spawn more food???
            with food_lock:
                if(len(food) <= FOOD_THRESHOLD): #we might need to spawn some more then...
                    for x in range(0,FOOD_MAX - FOOD_THRESHOLD): #spawn some more!
                        food.append(Square([0,0])) #create a new piece of food
                        food[len(food) - 1].name = "" #give the food a blank name
                        food[len(food) - 1].pos = [[random.randint(0,640),random.randint(0,480)]] #give it a random position
                        food[len(food) - 1].size = [random.randint(2,7)] #give us a little bit of size variation...
        printer.print_msgs() #print any thread messages
        with client_connected_lock: #if we got a client on our last launched thread, then...
            if(client_connected == True):
                client_connected = False
                break #break out of this dumb loop and get another client connection ready to go!!!
