import _thread
import socket
import random
import pygame #only used for it's time.Clock() class
import math

#constants for starting Square() objects
consts_lock = _thread.allocate_lock()
SIZE = 10

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
    #with obj.pos_lock: #next we send our own data...
    pos = str(inobj.pos)
    #with obj.size_lock:
    size = str(inobj.size)
    #with obj.score_lock:
    score = str(inobj.score)
    #with obj.direction_lock:
    direction = str(inobj.direction)
    Odata = "[" + pos + ",[" + size + " , " + score + " , " + direction + "], " + str(inobj.connected) + " , " + "'" + str(inobj.name) + "'" + "]" #next we join it all into one big string...
    #Odata = justify(Odata, 200) #right-justify our data to 100 characters in size
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

        self.speedT = 1 #pixels per tick
        self.speedS = self.speedT * 30 #pixels per second
        self.speedThreshold = 2 #due to ping, etc. we need to give people a little give/take regarding policing their speeds...
        self.slowdown = 0.3 #slowdown factor - bigger = slower

        self.pos_lock = _thread.allocate_lock()
        self.size_lock = _thread.allocate_lock()
        self.score_lock = _thread.allocate_lock()
        self.direction_lock = _thread.allocate_lock()
        self.name_lock = _thread.allocate_lock()
        self.clientnum_lock = _thread.allocate_lock()
        self.food_diffs_lock = _thread.allocate_lock()

    def eat(self,other): #checks whether this Square() instance is completely surrounding another. if so, the other one's DEAD.
        selfposition = [] #list format: [[x1,y1,x2,y2], [x1,y1,x2,y2]]
        for x in range(0,len(self.pos)):
            tmpposition = [] #list format: [x1,y1,x2,y2]
            tmpposition.append(self.pos[x][0] - (self.size[x] / 2.0)) #x1
            tmpposition.append(self.pos[x][1] - (self.size[x] / 2.0)) #y1
            tmpposition.append(self.pos[x][0] + (self.size[x] / 2.0)) #x2
            tmpposition.append(self.pos[x][1] + (self.size[x] / 2.0)) #y2
            selfposition.append(eval(str(tmpposition)))
##        with other.pos_lock: #get the position of the other player
##            with other.size_lock:
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
                                #with self.size_lock:
                                self.size[meself] += otherposition[otherself][2] - otherposition[otherself][0] #change the server's recognition of the player's size
                                return [meself,otherself] #we[meself] ate something[otherself]!!!
        return False #if we didn't eat anything?

    def set_stats(self,inlist,clientnum): #ez way to decode a set of stats and verify that the client IS NOT CHEATING
        #[[posX,posY],[size,score,[directionX,directionY]]]
##        with self.pos_lock: #set our pos to the client's
##            with sqrt_lock:
        self.pos = inlist[0][:]
        #with self.size_lock:
        Ctotalsize = 0 #we need to check that the player hasn't enabled sizehax...
        for addup in range(0,len(inlist[1][0])): #so we add up their total mass...
            Ctotalsize += inlist[1][0][addup]
        Stotalsize = 0 #and we add up
        for addup in range(0,len(self.size)):
            Stotalsize += self.size[addup]
        if(Ctotalsize <= Stotalsize): #they didn't cheat? (their size is smaller or equal to what the server thinks?)
            self.size = inlist[1][0] #then we can sync our sizes
        else: #print a cheating message
            printer.msgs.append("Cheater at " + str(clientnum) + " detected with sizehax!")
        #the server also controls score...
##        with self.score_lock:
##            self.score = inlist[1][1]
        #with self.direction_lock: #but not direction. ***need to add AC here...***
        self.direction = inlist[1][2][:]
        #with self.name_lock:
        self.name = inlist[3]

#food constants
FOOD_MAX = 75 #maximum food allowed on arena at one time
FOOD_THRESHOLD = 25 #minimum food amount we can have onscreen before the server spawns more...

#manage the client setups and food population
food = [] #create some food
food_lock = _thread.allocate_lock()
for x in range(0,FOOD_MAX): #create 75 pieces of food
    food.append(Square([random.randint(0,640),random.randint(0,480)])) #randomly choose a position
    food[len(food) - 1].size = [random.randint(2,7)] #give us a little bit of size variation...
    food[len(food) - 1].name = ""

def manage_client(IP,PORT): #manages a single client connection
    global obj #obj is a large object which holds ALL the data for ALL players.
    global clients
    global tickComplete
    global tickPhase
    global s
    global client_connected
    #create a socket connection to the client
    buffersize = 10 #default buffer size
    Cs, Caddress = s.accept() #connect to a client
    with print_lock: #let the WORLD of terminal know...how exciting
        print("[OK] Client at " + str(Caddress) + " connected successfully.")

    #next, we have to let the client know our default buffer size.
    with print_lock:
        print("[INFO] Sending buffersize to client " + str(Caddress))
    Cs.send(bytes(justify(str(buffersize),buffersize), "utf-8")) #it must occupy (buffersize) characters

    #then we need to receive a confirmation signal so we know everything is working.
    print("    [WAIT] Waiting for acknowledge from client " + str(Caddress))
    confirm = Cs.recv(buffersize)
    with print_lock: #and let the USER know
        print("    [OK] Client at " + str(Caddress) + " acknowledged signal!")

    #create a square object for our client to manipulate
    clientnum = None
    with join_lock:
        with obj_lock:
            for x in range(0,len(obj)):
                if(obj[x].connected == False):
                    clientnum = x + 1 #give us a client number
                    obj[clientnum - 1].connected = True
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
    with print_lock:
        print("[ATTEMPT] Sending start data for client " + str(clientnum))
    with obj_lock:
        tmpdata = gather_data(obj[clientnum - 1])
    Cs.send(bytes(justify(str(len(list(tmpdata))),buffersize), 'utf-8'))
    Cs.send(bytes(tmpdata,'utf-8'))
    with print_lock:
        print("    [OK] Send start data for client " + str(clientnum))

    #get the name of the player
    with print_lock:
        print("[ATTEMPT] Recieving name of client " + str(clientnum))
    Nbuffersize = Cs.recv(buffersize) #get the buffersize of incoming payload
    payload = eval(Cs.recv(int(Nbuffersize.decode('utf-8'))).decode('utf-8'))
    with obj_lock:
        obj[clientnum - 1].set_stats(payload,clientnum)
    with print_lock:
        with obj_lock:
            print("    [OK] Recieved client name " + str(obj[clientnum - 1].name))

    #now we send the state of all the food particles
    with print_lock:
        print("[ATTEMPT] Sending food particle states...")
    with food_lock:
        Fdata = '['
        for x in range(0,len(food)): #gather the food data into a list...
            Fdata += gather_data(food[x])
            if(x < (len(food) - 1)): #make sure to add a comma after each bunch of data except on the last one!
                Fdata += " , "
        Fdata += "]"
        Cs.send(bytes(justify(str(len(list(str(Fdata)))),10),'utf-8')) #send our buffersize
        Cs.send(bytes(Fdata,'utf-8')) #send our data string

    #make sure we do the good ol' 30TPS
    Sclock = pygame.time.Clock()

    with print_lock:
        print("    [OK] Successfully joined server!")

    with client_connected_lock: #make sure the server thread knows that we got a client on us!
        client_connected = True

    running = True

    #then we need to start continually feeding with data...
    while running:
        with obj_lock: #check if anyone has eaten food? or food eaten them, for that matter...
            with food_lock:
                while True:
                    for x in range(0,len(food)):
                        foodeaten = obj[clientnum - 1].eat(food[x])
                        if(foodeaten != False): #so they ate the food...now we have to update a million players food lists...
                            obj[clientnum - 1].size[foodeaten[0]] += food[x].size[foodeaten[1]] #make sure we grow that hungry player
                            del(food[x]) #delete the eaten food
                            for b in range(0,len(obj)):
                                obj[b].food_diffs.append([x,'eat']) #tell everyone connected that X got eaten
                            break #restart the calculations now that "food" is 1 index shorter than it should be
                    break #we finished calculations without anything being eaten?
        with obj_lock:
            with clients_lock:
                Sdata = "[" #gather all the square data
                for x in range(0,len(obj)):
                    if(x == (clientnum - 1)): #we don't want to send the client's own data back.
                        continue
                    Sdata += gather_data(obj[x])
                    if(x != len(obj) - 1): #so long as we're not adding the last player's data to the list, we add a comma in between each chunk.
                        Sdata += " , "
                Sdata += "]"
                try: #if the client closed the connection...
                    Cs.send(bytes(justify(str(len(list(Sdata))),10),'utf-8')) #we start by sending a buffersize.
                    Cs.send(bytes(Sdata, 'utf-8')) #then we send a truckload of data.
                except socket.error: #disconnect the thread, and open up a client number
                    obj[clientnum - 1].connected = False
                    running = False
                    break
                except ConnectionResetError: #a guaranteed disconnect? Connection DROPPED, player gets shoe.
                    obj[clientnum - 1].connected = False
                    running = False
                    break

        #now we send data about changes in the food list...
        with obj_lock:
            foodupdate = obj[clientnum - 1].food_diffs[:]
            Cs.send(bytes(justify(str(len(list(str(foodupdate)))), 10),'utf-8')) #send what would be our buffersize
            Cs.send(bytes(str(foodupdate),'utf-8')) #send the food update
            obj[clientnum - 1].food_diffs = [] #clear the food_diffs cache once its been sent

        with obj_lock: #now we send changes about the client's size data...
            sizeupdate = eval(str(obj[clientnum - 1].size_diffs))
            Cs.send(bytes(justify(str(len(list(str(sizeupdate)))), 10),'utf-8')) #send what would be our buffersize
            Cs.send(bytes(str(sizeupdate),'utf-8')) #send the size update
            obj[clientnum - 1].size_diffs = [] #clear the size_diffs cache once its been sent
                        
        #Recieve client data...
        Cs.settimeout(5) #set a timeout of (x) seconds for Cs
        try:
            Nbuffersize = Cs.recv(buffersize) #then we recieve the client's data.
            Nbuffersize = int(Nbuffersize.decode('utf-8')) #first get our buffersize

            Cdata = Cs.recv(Nbuffersize) #then we get the client data
            Cdata = eval(Cdata.decode('utf-8'))
        except socket.timeout: #we're not getting any data in 5 SECONDS?? a ping of 5000 is unplayable, so the person probably disconnected.
            obj[clientnum - 1].connected = False
            running = False
            break
        except ConnectionResetError: #a guaranteed disconnect? Connection DROPPED, player gets shoe.
            obj[clientnum - 1].connected = False
            running = False
            break
        except ValueError: #we timed out, and as a result got '' instead of an int. ValueError occurs then...
            obj[clientnum - 1].connected = False
            running = False
            break
        Cs.settimeout(None) #clear the timeout

        #now we need to decode the client's data...
        with obj_lock:
            obj[clientnum - 1].set_stats(Cdata,clientnum) #*BOOM* - that was easy
        
        Sclock.tick(30) #get our sweet 30TPS
    with print_lock:
        print("[DISCONNECT, " + str(clientnum) + "] Client has disconnected from server.")

clock = pygame.time.Clock()
while True:
    with clients_lock:
        old_clientct = clients #this is how many clients we *had*...
    with print_lock: #debug
        print("[SERVER] New Client thread initialized...")
    _thread.start_new_thread(manage_client,(IP,PORT)) #we start a thread to join a client up...
    while True: #wait for another client to connect, and handle other things in the meantime...
        with obj_lock:
            with food_lock:
                if(len(food) < FOOD_THRESHOLD): #we might need to spawn some more then...
                    foodchanges = []
                    for x in range(0,FOOD_MAX - FOOD_THRESHOLD): #spawn some more!
                        food.append(Square([random.randint(0,640),random.randint(0,480)])) #randomly choose a position
                        food[len(food) - 1].size = [random.randint(2,7)] #give us a little bit of size variation...
                        food[len(food) - 1].name = ""
                        foodchanges.append(["spawn", eval(gather_data(food[len(food) - 1]))]) #make sure we keep track of what we did so the clients know...
                    for x in range(0,len(obj)): #let all the clients know!
                        for y in range(0,len(foodchanges)):
                            obj[x].food_diffs.append(foodchanges[y][:]) #add the changes to the food_diffs inside each client OBJ...
        printer.print_msgs() #print any thread messages
        with client_connected_lock: #if we got a client on our last launched thread, then...
            if(client_connected == True):
                client_connected = False
                break #break out of this dumb loop and get another client connection ready to go!!!
        clock.tick(30) #make it so we're not CONSTANTLY hogging clients / client_lock
