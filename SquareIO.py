#import libraries
import pygame #for graphics
import _thread #pretty obvious, for multicore process tasking allowing me to perform rendering + computation on separate threads
import math #for trigonometry + sqrt, used in find_slope()
import socket #for netcode

def find_slope(distance,speed): #used in determining direction of your player's movement
    #distance is an [x,y] list which is the distance between you and the mouse pointer
    #use trigonometry to determine angle between mouse cursor and player, then return vector 1 unit
    if(distance[1] > 0): #above center
        if(distance[0] > 0): #right of center
            rotated = abs(math.atan(distance[1] / (distance[0] * 1.0)))
        else: #left of center
            rotated = abs(math.atan((distance[0] * 1.0) / distance[1])) + math.radians(90)
    else: #below center
        if(distance[0] > 0): #right of center
            if(distance[1] != 0): #need to avoid nasty 0div errors...
                rotated = abs(math.atan((distance[0] * 1.0) / distance[1])) + math.radians(270)
            else:
                rotated = math.radians(0)
        else: #left of center
            if(distance[0] != 0): #need to avoid nasty 0div errors...
                rotated = abs(math.atan(distance[1] / (distance[0] * 1.0))) + math.radians(180)
            else:
                rotated = math.radians(90)
    #return the calculated slope thingy
    return [math.cos(rotated) * speed, math.sin(rotated) * speed]

#a single font which can be used on pygame's screen surface in any size of position
def draw_words(words, coords, color, scale):
    global screen
    dictionary = [ #a list which interprets the match of a symbol to a number index
        ["a",0],
        ["b",1],
        ["c",2],
        ["d",3],
        ["e",4],
        ["f",5],
        ["g",6],
        ["h",7],
        ["i",8],
        ["j",9],
        ["k",10],
        ["l",11],
        ["m",12],
        ["n",13],
        ["o",14],
        ["p",15],
        ["q",16],
        ["r",17],
        ["s",18],
        ["t",19],
        ["u",20],
        ["v",21],
        ["w",22],
        ["x",23],
        ["y",24],
        ["z",25],
        ["0",26],
        ["1",27],
        ["2",28],
        ["3",29],
        ["4",30],
        ["5",31],
        ["6",32],
        ["7",33],
        ["8",34],
        ["9",35],
        ["-",36],
        [" ",37]]

    font = [ #a line based font (abcdefghijklmnopqrstuvwxyz0123456789-), size 10PX
        [[0,0],[10,0],[10,10],[10,3],[0,3],[0,0],[0,10]], #A
        [[0,10],[0,0],[10,3],[0,5],[10,8],[0,10]], #B
        [[10,0],[0,0],[0,10],[10,10]], #C
        [[0,0],[10,5],[0,10],[0,0]], #D
        [[10,0],[0,0],[0,5],[10,5],[0,5],[0,10],[10,10]], #E
        [[10,0],[0,0],[0,5],[10,5],[0,5],[0,10]], #F
        [[10,0],[0,0],[0,10],[10,10],[10,8],[8,8]], #G
        [[0,0],[0,10],[0,5],[10,5],[10,0],[10,10]], #H
        [[0,0],[10,0],[5,0],[5,10],[0,10],[10,10]], #I
        [[0,0],[10,0],[5,0],[5,10],[0,8]], #J
        [[0,0],[0,10],[0,5],[10,0],[0,5],[10,10]], #K
        [[0,0],[0,10],[10,10]], #L
        [[0,10],[0,0],[5,5],[10,0],[10,10]], #M
        [[0,10],[0,0],[10,10],[10,0]], #N
        [[0,0],[10,0],[10,10],[0,10],[0,0]], #O
        [[0,10],[0,0],[10,3],[0,6]], #P
        [[5,5],[0,10],[0,0],[10,0],[5,5],[10,10]], #Q
        [[0,10],[0,0],[10,3],[0,6],[10,10]], #R
        [[10,0],[0,3],[10,6],[0,10]], #S
        [[5,10],[5,0],[0,0],[10,0]], #T
        [[0,0],[0,10],[10,10],[10,0]], #U
        [[0,0],[5,10],[10,0]], #V
        [[0,0],[2,10],[5,0],[8,10],[10,0]], #W
        [[0,0],[10,10],[5,5],[10,0],[0,10]], #X
        [[0,0],[5,5],[10,0],[5,5],[5,10]], #Y
        [[0,0],[10,0],[0,10],[10,10]], #Z
        [[10,10],[0,10],[0,0],[10,0],[10,10],[0,0]], #0
        [[5,0],[5,10]], #1
        [[0,2],[5,0],[10,2],[0,10],[10,10]], #2
        [[0,0],[10,0],[10,5],[0,5],[10,5],[10,10],[0,10]], #3
        [[0,0],[0,4],[10,4],[8,4],[8,0],[8,10]], #4
        [[10,0],[0,0],[0,5],[10,8],[0,10]], #5
        [[10,2],[10,0],[0,0],[0,10],[10,10],[10,7],[0,7]], #6
        [[0,0],[10,0],[0,10]], #7
        [[0,3],[5,0],[10,3],[0,8],[5,10],[10,8],[0,3]], #8
        [[0,10],[10,7],[5,0],[0,5],[5,6],[10,7]], #9
        [[0,5],[10,5]], #-
        [[0,0],[0,0]] #[space]
        ]

    words = list(words)
    for x in range(0,len(words)): #draw each letter in the string entered
        for findindex in dictionary: #find the index of the letter we used
            if(findindex[0] == words[x].lower()): #we found the letter's index?
                for drawletter in range(0,len(font[findindex[1]]) - 1): #then DRAW IT!
                    pointA = font[findindex[1]][drawletter][:] #find the points we need
                    pointB = font[findindex[1]][drawletter + 1][:]
                    pointA[0] = int(pointA[0] * 1.0 * scale) #scale them correctly
                    pointA[1] = int(pointA[1] * 1.0 * scale)
                    pointB[0] = int(pointB[0] * 1.0 * scale)
                    pointB[1] = int(pointB[1] * 1.0 * scale)
                    pointA[0] += coords[0] + (x * 11 * scale) #position them correctly
                    pointA[1] += coords[1]
                    pointB[0] += coords[0] + (x * 11 * scale)
                    pointB[1] += coords[1]
                    pygame.draw.line(screen,color,pointA,pointB,int(1.0 * scale) + 1) #draw the line between those points
                break #exit this "findletter's index" loop, and move on to the next one

#a class which is for all players - the SQUARE! This is also what is going to be used for all the edible pellets in the game, strangely enough.
#Multithreading capable?!?!
class Square():
    def __init__(self):
        #basic attrib variables
        self.pos = [[0.0, 0.0]]
        self.size = [100]
        self.score = 0
        self.direction = [[0.0, 0.0, 1.0]]

        self.color = [0,255,0] #color of player

        self.connected = True #tells us whether someone's actually controlling this player or not - which tells us whether we should bother drawing it
        self.name = "default"

        #speed limits
        self.speedT = 1 #pixels per tick
        self.speedS = self.speedT * 30 #pixels per second
        self.slowdown = 0.3 #slowdown factor - bigger = slower

    def draw_square(self): #draws the player onscreen with his pos as the center point of his player
        for x in range(0,len(self.size)):
            pygame.draw.rect(screen,self.color,[int(self.pos[x][0] - self.size[x] / 2), int(self.pos[x][1] - self.size[x] / 2), int(self.size[x]), int(self.size[x])],0)
            draw_words(self.name,[self.pos[x][0] - (len(list(self.name)) * 6) / 2,self.pos[x][1] - 3],[255,255,255],0.5)

    def split(self,pos):
        totalmass = 0 #get a sum of all our mass
        for x in range(0,len(self.size)):
            totalmass += self.size[x]
        if(totalmass / len(self.size) > 10): #make sure we can't split ourselves beyond a certain size (10px)
            splitmass = totalmass / (len(self.size) + 1) #get an idea of how much mass we're going to take into the new split...
            for x in range(0,len(self.size)):
                self.size[x] -= splitmass / len(self.size) #take away a bit of mass from all player's other cells to create a new cell
            self.direction.append([0.0,0.0,5.0]) #make new direction vector for new instance of Square with a 5x speedup
            self.size.append(splitmass) #add the new mass size to our newest addition
            self.pos.append([self.pos[0][0], self.pos[0][1]]) #make a new pos for the duplicate

    def rejoin(self): #checks if any cells of this Square() object are touching; if so, it adds their mass to join them
        while True:
            continueflag = False
            for x in range(0,len(self.pos)): #iterate through all the cells to check if any are touching
                if(self.direction[x][2] > 1.1): #is this a fresh split? if so, we can't rejoin until its finished its boost.
                    continue
                collidecoordsA = [] #[x1,y1,x2,y2]
                sizeoffsetA = self.size[x] / 2.0 #the offset from our position we use to get our collision coordinates
                collidecoordsA.append(self.pos[x][0] - sizeoffsetA) #x1
                collidecoordsA.append(self.pos[x][1] - sizeoffsetA) #y1
                collidecoordsA.append(self.pos[x][0] + sizeoffsetA) #x2
                collidecoordsA.append(self.pos[x][1] + sizeoffsetA) #y2
                for y in range(0,len(self.pos)):
                    if(y == x): #we'd BETTER not be checking collision of ourselves against ourselves...
                        continue
                    if(self.direction[y][2] > 1.1): #is this a fresh split? if so, we can't rejoin until its finished its boost.
                        continue
                    collidecoordsB = [] #[x1,y1,x2,y2]
                    sizeoffsetB = self.size[y] / 2.0 #the offset from our position we use to get our collision coordinates
                    collidecoordsB.append(self.pos[y][0] - sizeoffsetB) #x1
                    collidecoordsB.append(self.pos[y][1] - sizeoffsetB) #y1
                    collidecoordsB.append(self.pos[y][0] + sizeoffsetB) #x2
                    collidecoordsB.append(self.pos[y][1] + sizeoffsetB) #y2
                    if(collidecoordsA[2] > collidecoordsB[0]): #right side of CollideCoordsA smaller than left side of CollideCoordsB?
                        if(collidecoordsA[0] < collidecoordsB[2]): #left side of CollideCoordsA smaller than right side of CollideCoordsB?
                            if(collidecoordsA[1] < collidecoordsB[3]): #top side of CollideCoordsA smaller than bottom side of CollideCoordsB?
                                if(collidecoordsA[3] > collidecoordsB[1]): #bottom side of CollideCoordsA greater than top side of CollideCoordsB?
                                    self.size[x] += self.size[y] #add the mass of [x+1] to [x]
                                    del(self.size[y]) #remove the [x+1] mass item
                                    del(self.direction[y]) #remove the [x+1] direction item
                                    del(self.pos[y]) #remove the [x+1] position item
                                    continueflag = True #now that we removed an object and changed another one, we have to restart the calculations.
                                    break
                if(continueflag == True):
                    break
            if(continueflag == False):
                break #once calculations finish, exit the loop!
                            

    def set_stats(self,inlist): #ez way to decode a set of stats
        #[[posX,posY],[size,score,[directionX,directionY]]]
        self.pos = inlist[0][:] #set our pos to the server's
        self.size = inlist[1][0]
        self.score = inlist[1][1]
        self.direction = inlist[1][2][:]
        self.connected = inlist[2]
        self.name = inlist[3]

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
    Odata = "[" + pos + ",[" + size + " , " + score + " , " + direction + "], " + str(connected) + " , " + "'" + name + "'" + "]" #next we join it all into one big string...
    #Odata = justify(Odata, 200) #right-justify our data to 200 characters in size
    return Odata

#get a player name
name = input("Please give a name: ")

#a list full of Square() objects which gets computed/drawn/updated by the Compute,Render,and Netcode threads.
Serversquares = []
Serversquares_lock = _thread.allocate_lock()

#netcode buffer size in BYTES (needs to be big enough to recieve a number up to 5 digits as a string)
buffersize = 10

#attempt to connect to the server
ipaddr = input("Please give me the IP of the server: ") #get the IP address of the server
while True: #get the port number of the server
    portnum = input("Please give me the port number of the server: ")
    try: #valid port number?
        int(portnum)
        break #exit the endless loop of faulty port numbers
    except: #if not...
        print("Bad portnum. Not an integer?")
Cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create a python Socket object for our Client/game
Cs.connect((ipaddr, int(portnum))) #try to establish a socket connection with the server
print("[OK] Connection established with server " + ipaddr) #debug info

#attempt to retrieve the firstfruits of our connection - the server's pick of a connection buffer size
buffersize = Cs.recv(buffersize)
buffersize = int(buffersize.decode("utf-8"))
print("[OK] Successfully grabbed buffer size: " + str(buffersize) + " bytes")
Cs.send(justify("[ACK]",buffersize).encode('utf-8')) #we have to send back an acknowledgement packet. The content of it doesn't matter, as strange as it may seem.

#create a display
screen = pygame.display.set_mode([640,480],pygame.SCALED)
pygame.display.set_caption("SquareIO Online Multiplayer")

#we need a local player object
player = Square()
player_lock = _thread.allocate_lock()

#now we need to recieve some data from the server. The square's starting position, mainly.
print("[INFO] Recieving start data...")
Rbuffersize = Cs.recv(buffersize) #get the buffersize
Rbuffersize = int(Rbuffersize.decode("utf-8"))
print("    [OK] Grabbed start data buffersize of " + str(Rbuffersize))
Cdata = Cs.recv(Rbuffersize) #now we recieve the actual server data.
player.set_stats(eval(Cdata.decode('utf-8')))
print("    [OK] Recieved start data.")

#next we need to send back some info - our name.
print("[INFO] Sending player name...")
player.name = name
Sendstuff = gather_data(player)
Cs.send(bytes(justify(str(len(list(Sendstuff))),10),'utf-8'))
Cs.send(bytes(Sendstuff,'utf-8'))
print("    [OK] Successfully sent name!")

#now we need to get all the pieces of food in the game.
#a list full of Square() objects which can only be eaten @ the moment (could change)
food = []
food_lock = _thread.allocate_lock()
print("[INFO] Getting food positions...")
Nbuffersize = int(Cs.recv(buffersize).decode('utf-8')) #get our buffersize for all the data
Fdata = eval(Cs.recv(Nbuffersize).decode('utf-8')) #get all the data
for x in range(0,len(Fdata)): #load it into our Food array
    food.append(Square()) #create a new Square() object
    food[len(food) - 1].set_stats(Fdata[x]) #load stats into it
    food[len(food) - 1].color = [255,255,0]
print("    [OK] Recieved food stats!")


#stats variables
CPS = 1 #Compute cycles Per Second (Compute thread)
CPS_lock = _thread.allocate_lock()
FPS = 1 #Frames Per Second (Renderer thread)
FPS_lock = _thread.allocate_lock()
TPS = 1 #Ticks Per Second (Networking thread)
TPS_lock = _thread.allocate_lock()

#we don't want to stop yet, do we?
running = True
running_lock = _thread.allocate_lock()

def renderer(): #the SquareIO renderer thread. Drawing EVERYTHING. (perhaps the most computationally heavy part of the game)
    global player
    global FPS
    global TPS
    global CPS

    #local unlocked variables
    Rclock = pygame.time.Clock()
    performance = [0,0,0]
    
    global running #we wants the global version so we can end all our tasks at once

    while True: #main renderer loop
        
        with running_lock: #if we doesn't wants to be here anymore?
            if(running == False):
                break

        with food_lock: #draw all the food
            for drawfood in range(0,len(food)):
                food[drawfood].draw_square()
        with player_lock: #draw our player
            player.draw_square()
        with Serversquares_lock: #draw all the other opponents
            for drawothers in range(0,len(Serversquares)):
                if(Serversquares[drawothers].connected == True):
                    Serversquares[drawothers].draw_square()

        #draw our performance stats
        draw_words("FPS - " + justify(str(performance[0]),3) + " CPS - " + justify(str(performance[1]),3) + " TPS: " + justify(str(performance[2]),3),[10,10],[255,0,0],1)

        pygame.display.flip() #update our screen
        screen.fill([0,0,0]) #fill our screen with everyone's favorite color

        Rclock.tick(900) #we want this running AS FAST AS POSSIBLE (within 3 digits)

        with FPS_lock: #get our FPS counter
            FPS = int(Rclock.get_fps())
            performance[0] = FPS
        with CPS_lock:
            performance[1] = CPS
        with TPS_lock:
            performance[2] = TPS

def compute(): #the computation thread of SquareIO; handling movement, mostly at the moment.
    global player
    global running #we wants the global version so we can end all our tasks at once
    global CPS

    #local variables, no threading needed
    mousepos = [0,0] #a local function variable which we DON'T need to lock at ALL.
    Cclock = pygame.time.Clock()

    while True: #main computation loop
        
        with running_lock: #if we doesn't wants to be here anymore?
            if(running == False):
                break

        for event in pygame.event.get(): #run the pygame event loop
            if(event.type == pygame.QUIT): #does we wants to leave?
                with running_lock:
                    running = False
            elif(event.type == pygame.MOUSEMOTION):
                mousepos = event.pos[:]
            elif(event.type == pygame.MOUSEBUTTONDOWN): #then we split!!!
                with player_lock:
                    player.split(mousepos)

        with CPS_lock:
            tmpCPS = CPS
        with player_lock:
            player.rejoin() #check if we can rejoin any of our player's cells, and if so, do that.
            for x in range(0,len(player.direction)):
                TMPspeed = ((player.speedS - (player.size[x] * player.slowdown)) / tmpCPS) * player.direction[x][2]
                if(TMPspeed < (5 / tmpCPS)): #if we're not moving??? or backwards???
                    TMPspeed = (5.0 / tmpCPS) #let's be nice, let people move 5 pixels per second then...
                TMPplayerdirection = find_slope([mousepos[0] - player.pos[x][0], mousepos[1] - player.pos[x][1]],TMPspeed)
                player.direction[x][0] = TMPplayerdirection[0]
                player.direction[x][1] = TMPplayerdirection[1]
                if(player.direction[x][2] > 1): #decrease the player's boost amount each CPS
                    player.direction[x][2] -= 1 / tmpCPS
                player.pos[x][0] += player.direction[x][0]
                player.pos[x][1] += player.direction[x][1]

        with Serversquares_lock: #update ALL the other players positions
            for computesquares in range(0,len(Serversquares)):
                for x in range(0,len(Serversquares[computesquares].pos)):
                    Serversquares[computesquares].pos[x][0] += Serversquares[computesquares].direction[x][0]
                    Serversquares[computesquares].pos[x][1] += Serversquares[computesquares].direction[x][1]

        Cclock.tick(900) #run AS FAST AS WE CAN!!! (almost)

        with CPS_lock: #get our Compute cycles Per Second
            pCPS = int(Cclock.get_fps()) #"potential CPS"
            if(pCPS != 0):
                CPS = pCPS

def netcode(): #the netcode thread!
    global TPS #these global variables are very near the top of the program. (except TPS, kinda more in the middle)
    global Cs
    global buffersize
    global player
    global Serversquares

    Nclock = pygame.time.Clock() #a pygame clock we use to try achieve 30TPS

    while True: #main netcode loop
        Nbuffersize = Cs.recv(buffersize) #we then recieve the other players' data, which means getting the buffer size needed for that data.
        Nbuffersize = int(Nbuffersize.decode("utf-8"))
        Sdata = Cs.recv(Nbuffersize) #next we get the actual data...

        #now we decode it...and it turns into a list! (if all goes well, that is)
        Sdata = eval(Sdata.decode('utf-8'))
        with Serversquares_lock:
            for x in range(0,len(Sdata)):
                while True:
                    try: #due to the changing client list size...sometimes we need to add another player to the client list...
                        Serversquares[x].set_stats(Sdata[x])
                        break
                    except IndexError: #we don't have enough players here...add another!
                        Serversquares.append(Square())

        #Here we need to recieve data about changes in the Food list...
        Nbuffersize = int(Cs.recv(buffersize).decode('utf-8')) #recieve the buffersize for the data
        Fdata = Cs.recv(Nbuffersize) #recieve the actual data
        Fdata = eval(Fdata.decode('utf-8')) #next we need to do something with it.
        for x in range(0,len(Fdata)):
            if(Fdata[x][1] == 'eat'): #someone (or ourselves) ate something?
                with food_lock:
                    del(food[Fdata[x][0]])
            if(Fdata[x][0] == "spawn"): #the server spawned more food?
                for copyfood in range(0,len(Fdata)):
                    with food_lock:
                        food.append(Square()) #create a new food object
                        food[len(food) - 1].set_stats(Fdata[x][1]) #load some stats into it

        #here we need to recieve data about changes in our player's size...
        Nbuffersize = int(Cs.recv(buffersize).decode('utf-8')) #recieve buffersize
        Sdata = eval(Cs.recv(Nbuffersize).decode('utf-8')) #recieve size changes
        for x in range(0,len(Sdata)): #use the data - format: [index,sizechange]
            with player_lock:
                try:
                    player.size[Sdata[x][0]] += Sdata[x][1] #increment/decrement the sizechange coming from the server
                except IndexError: #we rejoined our cells within the 30th of a second that it takes this data to come through?
                    print("Couldn't find grow index.")
                    player.size[0] += Sdata[x][1] #then just increment cell 0 of player's size
                
        with running_lock: #if we doesn't wants to be here anymore?
            if(running == False):
                print("Server acknowledged closedown. Exiting...")
                Cs.close() #close the connection
                break #kill the thread

        with player_lock:
            Cdata = gather_data(player)
        Cs.send(bytes(justify(str(len(list(Cdata))),10),"utf-8"))
        Cs.send(bytes(Cdata,"utf-8")) #encode it, and send it away!

        #make sure we only tick 30 times a second so we don't run out of server bandwidth/processing power
        Nclock.tick(30)

        #and set our TPS so we can see our swwwwwweeet performance stats
        with TPS_lock:
            TPS = justify(str(int(Nclock.get_fps())), 3)

#thread start code
#_thread.start_new_thread(compute,())

_thread.start_new_thread(netcode,())

_thread.start_new_thread(renderer,())

compute()
##aclock = pygame.time.Clock()
##while True:
##    with running_lock:
##        if(running == False):
##            break
##    aclock.tick(10)