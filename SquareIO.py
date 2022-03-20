#import libraries
import pygame #for graphics
import sys
sys.path.insert(0, "libraries") #make sure we can import our local libraries
import _thread #pretty obvious, for multicore process tasking allowing me to perform rendering + computation on separate threads
import math #for trigonometry + sqrt, used in find_slope()
import socket
import netcode #for netcode
import menu #for a nice looking menu
import pickle #for storing and restoring our settings after restarting the game

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
        [" ",37],
        [".",38]
        ]

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
        [[0,0],[0,0]], #[space]
        [[5,10],[6,10],[6,9],[5,9],[5,10]] #period
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

        self.boostfactor = 0.5 #the acceleration multiplier that a cell gets upon splitting
        self.slowdown = 0.001 #the slowdown factor for usage after a cell splits (smaller = longer boost time)

        self.color = [0,255,0] #color of player
        self.textcolor = [255,255,255] #text color
        self.food = False #are we food? if so, we don't draw player name.

        self.connected = True #tells us whether someone's actually controlling this player or not - which tells us whether we should bother drawing it
        self.name = "default"

        #speed limits
        self.speedS = 60 #pixels per second
        self.slowdown = 0.5 #slowdown factor - bigger = slower

    def draw_square(self): #draws the player onscreen with his pos as the center point of his player
        for x in range(0,len(self.size)):
            pygame.draw.rect(screen,self.color,[int(self.pos[x][0] - self.size[x] / 2), int(self.pos[x][1] - self.size[x] / 2), int(self.size[x]), int(self.size[x])],0)
            if(self.textcolor != None):
                draw_words(self.name,[self.pos[x][0] - (len(list(self.name)) * 6) / 2,self.pos[x][1] - 3],self.textcolor,0.5)

    def split(self,pos):
        totalmass = 0 #get a sum of all our mass
        for x in range(0,len(self.size)):
            totalmass += self.size[x]
        try:
            if(totalmass / len(self.size) > 10): #make sure we can't split ourselves beyond a certain size (10px)
                splitmass = totalmass / (len(self.size) + 1) #get an idea of how much mass we're going to take into the new split...
                for x in range(0,len(self.size)):
                    self.size[x] -= splitmass / len(self.size) #take away a bit of mass from all player's other cells to create a new cell
                self.direction.append([0.0,0.0,self.boostfactor * self.size[0]]) #make new direction vector for new instance of Square with a 5x speedup
                self.size.append(splitmass) #add the new mass size to our newest addition
                self.pos.append([self.pos[0][0], self.pos[0][1]]) #make a new pos for the duplicate
        except ZeroDivisionError:
            pass #don't split if we're not existent!

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

class Printer(): #class which allows threads to add messages to a queue which then gets printed by the main client thread
    def __init__(self):
        self.msgs = []
        self.msgs_lock = _thread.allocate_lock()

    def print_msgs(self): #prints all the queued messages
        with self.msgs_lock:
            for x in range(0,len(self.msgs)):
                print(self.msgs[x])
            self.msgs = [] #clear the message cache

#create a display
STARTSIZE = [640,480]
DEFAULTSIZE = [640,480] #different name, same function. One for the "renderer" thread, one for the main thread.
screen = pygame.Surface(STARTSIZE)
display = pygame.display.set_mode(STARTSIZE,pygame.RESIZABLE)
pygame.display.set_caption("SquareIO Online Multiplayer")

#create a printer object
printer = Printer()

#create a menu object
Mhandler = menu.Menuhandler()

#this flag goes positive when a player needs to respawn. The server keeps resetting the player's position until he respawns.
RESPAWN = False
RESPAWN_lock = _thread.allocate_lock()

#stats variables
CPS = 1 #Compute cycles Per Second (Compute thread)
CPS_lock = _thread.allocate_lock()
FPS = 1 #Frames Per Second (Renderer thread)
FPS_lock = _thread.allocate_lock()
PPS = 1 #Ticks Per Second (Networking thread) - need to change this to PPS (Packets Per Second) next update!
PPS_lock = _thread.allocate_lock()
PING = 1 #ping time (ms)
PING_lock = _thread.allocate_lock()
LOSS = 0.0 #percentage of packets lost through transmission
LOSS_lock = _thread.allocate_lock()
lobbystats = ["connecting to server",15] #a list which gives us stats about the state of our lobby
lobbystats_lock = _thread.allocate_lock()

#we don't want to stop yet, do we?
running = True #if we managed to stay connected this whole time...
running_lock = _thread.allocate_lock()

#our mouse position
mousepos = [200,200]
mousepos_lock = _thread.allocate_lock()

#are we in the "in-game" menu?
in_menu = False
in_menu_lock = _thread.allocate_lock()

def renderer(stretch=True): #the SquareIO renderer thread. Drawing EVERYTHING. (perhaps the most computationally heavy part of the game)
    global player
    global FPS
    global PPS
    global CPS
    global PING
    global lobbystats
    global Serversquares
    global mousepos
    global in_menu
    global running #we wants the global version so we can end all our tasks at once

    #create a menu object so we can get a UI when ESC is pressed
    rm_handler = menu.Menuhandler()

    #create the menu
    rm_handler.create_menu([""],[["",""]],[],[],"") #the blank menu we get during gameplay
    rm_handler.create_menu(["Continue","Options","Disconnect"],[["",""],["",""],["",""]],[[0,0],[1,2]],[],"In-Game Menu")
    rm_handler.create_menu(["Back","Stretched Gameplay","Change Player Name"],[[""],["True","False"],[player.name]],[[0,1]],[],"In-Game Options")

    #menu option flags
    NAME_OPTION = [[2,None], 2]
    DISCONNECT_OPTION = [[2,None], 1]
    BACK_OPTION = [[0,None],2]
    CONTINUE_OPTION = [[0,None], 1]
    OPTIONS_OPTION = [[1,None], 1]

    #we pressed an option?
    pressed_option = None

    #local unlocked variables
    Rclock = pygame.time.Clock()
    performance = [0,0,0,0,100.0]

    while True: #main renderer loop
        #get our window scale sizes
        scaleX = display.get_width() / STARTSIZE[0] * 1.0
        scaleY = display.get_height() / STARTSIZE[1] * 1.0

        #flush out the printer queue
        printer.print_msgs()
        
        with running_lock: #if we doesn't wants to be here anymore?
            if(running == False):
                break

        for event in pygame.event.get(): #run the pygame event loop
            if(event.type == pygame.QUIT): #does we wants to leave?
                with running_lock:
                    running = False
            elif(event.type == pygame.MOUSEMOTION):
                with mousepos_lock:
                    if(stretch):
                        mousepos = [int(event.pos[0] / scaleX),int(event.pos[1] / scaleY)]
                    else:
                        if(scaleX > scaleY):
                            mousepos = [int((STARTSIZE[0] * scaleY / 2.0 - display.get_width() / 2.0) / 2.0 + event.pos[0] / scaleY),int(event.pos[1] / scaleY)]
                        else:
                            mousepos = [int(event.pos[0] / scaleX),int((STARTSIZE[1] * scaleX / 2.0 - display.get_height() / 2.0) + event.pos[1] / scaleX)]
            elif(event.type == pygame.MOUSEBUTTONDOWN): #then we split!!! (provided we're not in the menu ATM)
                if(rm_handler.currentmenu == 0):
                    with player_lock:
                        player.split(mousepos)
                else: #we triggered our menu collision system!!!
                    settings = rm_handler.grab_settings(["Stretched Gameplay","Change Player Name"])
                    with mousepos_lock:
                        pressed_option = rm_handler.menu_collision([0,0],[display.get_width(),display.get_height()],mousepos)
                    if(pressed_option == NAME_OPTION): #we wants to change our name, eh?
                        player.name = rm_handler.get_input(display,"Please input your new player name")
                        rm_handler.reconfigure_setting([player.name],player.name,0,"Change Player Name")
                    elif(pressed_option == DISCONNECT_OPTION): #we're done playing for now?
                        with running_lock:
                            running = False
                    elif(pressed_option == BACK_OPTION): #we need to check what we set "Stretched Gameplay" to!
                        stretch = eval(settings[0][0])
                    elif(pressed_option == CONTINUE_OPTION): #are we continuing gameplay? If so, we need to let the compute thread know...
                        with in_menu_lock:
                            in_menu = False
                    elif(pressed_option == OPTIONS_OPTION): #we entered the options menu? we need to load the settings in that case.
                        rm_handler.reconfigure_setting(["True","False"],str(stretch),["True","False"].index(str(stretch)),"Stretched Gameplay")
            elif(event.type == pygame.KEYDOWN):
                if(event.key == pygame.K_ESCAPE): #we opened the secret in-game menu!!!
                    rm_handler.currentmenu = 1
                    with in_menu_lock:
                        in_menu = True

        with food_lock: #draw all the food
            foodlen = len(food)
        for drawfood in range(0,foodlen):
            with food_lock:
                try:
                    food[drawfood].draw_square()
                except IndexError: #someone ate the food right before we tried to draw it??????? *ugh*
                    pass #just do nothing... *sigh*
        with player_lock: #draw our player
            player.draw_square()
        with Serversquares_lock: #draw all the other opponents
            Serversquareslen = len(Serversquares)
        for drawothers in range(0,Serversquareslen):
            try:
                if(drawothers == clientnum - 1): #we don't need to double-draw ourselves...
                    continue
                if(Serversquares[drawothers].connected == True):
                    Serversquares[drawothers].draw_square()
            except IndexError: #did somebody get eaten or someone disconnect while we were trying so hard to render?????? RRRRRRGH - I hate try catches
                pass #just ignore it...

        #draw our performance/lobby stats
        draw_words("FPS - " + justify(str(performance[0]),3) + " CPS - " + justify(str(performance[1]),3) + " PPS: " + justify(str(performance[2]),3) + " PING - " + justify(str(performance[3]),4) + " PACK. LOSS - " + justify(str(performance[4]),6),[1,1],[255,0,0],0.5)
        with lobbystats_lock:
            draw_words("Lobby status - " + justify(lobbystats[0],6) + " Time - " + justify(str(int(lobbystats[1])),3),[1,470],[255,0,0],0.5)

        #create a scoreboard
        scoreboard = []
        skip = []
        with Serversquares_lock:
            SS = Serversquares
        for c in range(0,len(SS)): #get the top len(SS) people
            largest = [0,0] #index 0 holds the index of the largest player, index 1 holds his size
            for x in range(0,len(SS)): #find the largest player in SS
                if(x in skip): #we don't want to check somebody we've already added to the scoreboard
                    continue
                addup = 0
                for addup in range(0,len(SS[x].size)):
                    addup += SS[x].size[addup]
                if(addup > largest[1]): #we found a larger player?
                    largest = [x,addup]
            #add his size + name to a scoreboard list, provided there's anything on the scoreboard list at all...
            if(len(SS) > 0 and SS[c].connected == True):
                scoreboard.append([SS[largest[0]].name,largest[1]])
                skip.append(largest[0]) #remove the person from the list so we can find the person who is 2nd place to him

        #draw the scoreboard
        for x in range(0,len(scoreboard)):
            posY = (x * 8) + 2
            posX = 640 - len(list(justify(str(x),2) + " - " + justify(scoreboard[x][0],30) + " - score - " + justify(str(int(scoreboard[x][1])),3))) * 6
            draw_words(justify(str(x + 1),2) + " - " + justify(scoreboard[x][0],30) + " - score - " + justify(str(int(scoreboard[x][1])),3),[posX,posY],[0,0,255],0.5)

        #draw the winner's name of the previous round if we're waiting for players...
        with lobbystats_lock:
            if(lobbystats[0] == "wait"): #we're in lobby waiting for game start?
                if(len(scoreboard) > 0):
                    xpos = 320 - len(list("Winner - " + scoreboard[0][0])) * 11
                    draw_words("Winner - " + scoreboard[0][0],[xpos,230],[0,0,255],2)

        #draw our menu...
        if(rm_handler.currentmenu != 0):
            with mousepos_lock:
                rm_handler.draw_menu([0,0],[screen.get_width(),screen.get_height()],screen,mousepos)

        #scale "screen", and blit it onto "display"
        if(stretch):
            tmpsurface = pygame.transform.scale(screen,[display.get_width(),display.get_height()])
            display.blit(tmpsurface,[0,0])
        else: #we decided NOT to stretch our window so much?
            if(scaleX > scaleY):
                tmpsurface = pygame.transform.scale(screen,[int(STARTSIZE[0] * scaleY),int(STARTSIZE[1] * scaleY)])
                display.blit(tmpsurface,[int(display.get_width() / 2.0 - STARTSIZE[0] * scaleY / 2.0),int(display.get_height() / 2.0 - STARTSIZE[1] * scaleY / 2.0)])
            else:
                tmpsurface = pygame.transform.scale(screen,[int(STARTSIZE[0] * scaleX),int(STARTSIZE[1] * scaleX)])
                display.blit(tmpsurface,[int(display.get_width() / 2.0 - STARTSIZE[0] * scaleX / 2.0),int(display.get_height() / 2.0 - STARTSIZE[1] * scaleX / 2.0)])
        
        pygame.display.flip() #update our screen
        screen.fill([0,0,0]) #fill our screen with everyone's favorite color
        display.fill([0,0,0])

        Rclock.tick(900) #we want this running AS FAST AS POSSIBLE (within 3 digits)

        with FPS_lock: #get our FPS counter
            FPS = int(Rclock.get_fps())
            performance[0] = FPS
        with CPS_lock:
            performance[1] = CPS
        with PPS_lock:
            performance[2] = PPS
        with PING_lock:
            performance[3] = PING
        with LOSS_lock:
            performance[4] = round(LOSS,3)
    return [stretch, player.name] #make sure we know if we changed anything regarding these flags!

def compute(): #the computation thread of SquareIO; handling movement, mostly at the moment.
    global player
    global running #we wants the global version so we can end all our tasks at once
    global CPS
    global mousepos
    global in_menu
    global player_lock
    global RESPAWN

    #local variables, no threading needed
    mousepos = [0,0] #a local function variable which we DON'T need to lock at ALL.
    Cclock = pygame.time.Clock()

    while True: #main computation loop
        with running_lock: #if we doesn't wants to be here anymore?
            if(running == False):
                break

        with CPS_lock:
            tmpCPS = CPS
        with mousepos_lock:
            cursorpos = mousepos[:]
        with in_menu_lock:
            tmp_menu_flag = in_menu
        with RESPAWN_lock:
            tmp_RESPAWN = RESPAWN
        if(tmp_menu_flag != True and tmp_RESPAWN == False): #make sure we're not moving while we're in a menu or respawning
            with player_lock:
                player.rejoin() #check if we can rejoin any of our player's cells, and if so, do that.
                for x in range(0,len(player.direction)):
                    TMPspeed = (player.speedS - (player.size[x] * player.slowdown)) * player.direction[x][2]
                    if(TMPspeed < 0): #if we're not moving??? or backwards???
                        TMPspeed = 20 #let's fix that, make them move at least not backwards.
                    if(player.pos[x][0] < cursorpos[0] + 5 and player.pos[x][0] > cursorpos[0] - 5): #to avoid jumpy standstill on players, if our mouse is centered on our cell, don't move it.
                        if(player.pos[x][1] < cursorpos[1] + 5 and player.pos[x][1] > cursorpos[1] - 5):
                            player.direction[x] = [0.0,0.0,1.0]
                        else:
                            TMPplayerdirection = find_slope([cursorpos[0] - player.pos[x][0], cursorpos[1] - player.pos[x][1]],TMPspeed)
                            player.direction[x][0] = TMPplayerdirection[0]
                            player.direction[x][1] = TMPplayerdirection[1]
                    else:
                        TMPplayerdirection = find_slope([cursorpos[0] - player.pos[x][0], cursorpos[1] - player.pos[x][1]],TMPspeed)
                        player.direction[x][0] = TMPplayerdirection[0]
                        player.direction[x][1] = TMPplayerdirection[1]
                    if(player.direction[x][2] > 1): #decrease the player's boost amount each CPS
                        player.direction[x][2] -= (player.slowdown * player.size[x]) / tmpCPS
                    player.pos[x][0] += player.direction[x][0] / tmpCPS * 1.0
                    player.pos[x][1] += player.direction[x][1] / tmpCPS * 1.0

        with Serversquares_lock: #update ALL the other players' positions
            for computesquares in range(0,len(Serversquares)):
                for x in range(0,len(Serversquares[computesquares].pos)):
                    Serversquares[computesquares].pos[x][0] += Serversquares[computesquares].direction[x][0] / tmpCPS * 1.0
                    Serversquares[computesquares].pos[x][1] += Serversquares[computesquares].direction[x][1] / tmpCPS * 1.0

        Cclock.tick(900) #run AS FAST AS WE CAN!!! (almost)

        with CPS_lock: #get our Compute cycles Per Second
            pCPS = int(Cclock.get_fps()) #"potential CPS"
            if(pCPS != 0):
                CPS = pCPS

def network(): #the netcode thread!
    global PPS
    global PING
    global LOSS
    global Cs
    global buffersize
    global player
    global Serversquares
    global lobbystats
    global running
    global food
    global RESPAWN

    Nclock = pygame.time.Clock() #a pygame clock for PPS

    loss_counter = [0,0] #a list of the packets which did and didn't make it through to us...[successful, lost]
    LOSS_UPDATE_TIME = 10 #every LOSS_UPDATE_TIME packets our loss counter gets updated to the LOSS variable

    while True: #main netcode loop
        #get data about whether we've been EATEN by someone?????!!!!!???
        try:
            pack = netcode.recieve_data(Cs,buffersize,evaluate=True,returnping=True) #get ALL the server data
        except Exception as e: #we REALLY lost connection?
            with printer.msgs_lock:
                printer.msgs.append(str(e))
            with running_lock:
                running = False
            with printer.msgs_lock:
                printer.msgs.append("[ERROR] Server did not send data to client!")
            break
        netpack = pack[0]
        if(netpack == None): #the packet didn't make it through?
            loss_counter[1] += 1 #add a failure signal to our packet loss counter
        else: #we got the data successfully?
            loss_counter[0] += 1 #add a success signal to our packet loss counter
            
            with PING_lock: #set our ping to its respective level
                PING = pack[1]

            #now we need to parse it...uggh
            with RESPAWN_lock: #get a temporary copy of the respawn variable
                tmp_RESPAWN = RESPAWN
            if(tmp_RESPAWN == False): #we're not respawning?
                Edata = netpack[0] #we start by checking if the server thinks we got eaten...
                for parse in range(0,len(Edata)):
                    with printer.msgs_lock:
                        printer.msgs.append(str(parse))
                    with player_lock:
                        del(player.size[parse])
                        del(player.direction[parse])
                        del(player.pos[parse])
                        
            Sdata = netpack[1] #Server-side square data needs to be recieved...
            #now we decode it...and it turns into a list! (if all goes well, that is)
            with Serversquares_lock:
                for x in range(0,len(Sdata)):
                    while True:
                        try: #due to the changing client list size...sometimes we need to add another player to the client list...
                            Serversquares[x].set_stats(Sdata[x])
                            break
                        except IndexError: #we don't have enough players here...add another!
                            Serversquares.append(Square())
                            Serversquares[len(Serversquares) - 1].color = [255,0,0] #set the color to red

            #Here we need to recieve data in the Food list...
            Fdata = netpack[2]
            if(Fdata != None): #we're getting food data on this packet?
                with food_lock:
                    del(food)
                    food = [] #here we clear the food list, and add the updated food to it.
                    for x in range(0,len(Fdata)):
                        food.append(Square())
                        food[len(food) - 1].set_stats(Fdata[x])
                        food[len(food) - 1].color = [255,255,0] #set the food color to yellow
                        food[len(food) - 1].food = True

            #here we need to recieve data about changes in our player's size...
            if(tmp_RESPAWN == False): #we're not respawning rn?
                Sdata = netpack[3]
                for x in range(0,len(Sdata)): #use the data - format: [index,sizechange]
                    with player_lock:
                        try:
                            player.size[Sdata[x][0]] += Sdata[x][1] #increment/decrement the sizechange coming from the server
                        except IndexError: #we rejoined our cells within the 30th of a second that it takes this data to come through?
                            try:
                                with printer.msgs_lock:
                                    printer.msgs.append("[WARNING] Couldn't find grow index.")
                                player.size[0] += Sdata[x][1] #then just increment cell 0 of player's size
                            except IndexError:
                                with printer.msgs_lock:
                                    printer.msgs.append("[WARNING] Couldn't grow!!!")

            with player_lock: #get server "sync" data
                Sdata = netpack[4]
                if(Sdata != None):
                    player.set_stats(Sdata)
            if(Sdata != None): #set the RESPAWN flag high if we're syncing
                with RESPAWN_lock:
                    RESPAWN = True
            else: #reset our RESPAWN flag if the server decides we're doin' OK.
                with RESPAWN_lock:
                    RESPAWN = False

            #get the stats of the lobby we're in (ingame/wait, timeleft)
            with lobbystats_lock:
                lobbystats = netpack[5]
                
        with running_lock: #if we doesn't wants to be here anymore?
            if(running == False):
                print("Server acknowledged closedown. Exiting...")
                Cs.close() #close the connection
                break #kill the thread

        with player_lock: #send our player data
            Cdata = gather_data(player)
        try:
            netcode.send_data(Cs,buffersize,Cdata)
        except: #we lost server connection?
            with running_lock:
                running = False
            with printer.msgs_lock:
                printer.msgs.append("[ERROR] Couldn't send client's data pack!")
            break

        if(loss_counter[0] + loss_counter[1] >= LOSS_UPDATE_TIME): #update our loss counter?
            with LOSS_lock:
                try: #get a percentage based packet loss
                    LOSS = 100.00 - ((loss_counter[0] + loss_counter[1]) / loss_counter[0] * 100.0)
                    if(LOSS < 0): #just make sure our packet loss counte doesn't go negative...
                        LOSS = LOSS * -1
                except ZeroDivisionError: #we have perfect packets?
                    LOSS = 100.00 #we lost 100% packets, oh no!
            loss_counter = [0,0]

##        with LOSS_lock:
##            tmp_LOSS = LOSS
##        if(tmp_LOSS > 85): #we're losing every packet but 15%???
##            with running_lock:
##                running = False
##            with printer.msgs_lock:
##                printer.msgs.append("[ERROR] Disconnected due to EXTREME packet loss!")

        Nclock.tick(100) #tick the clock so we can see our PPS (100 is limit so we don't end up with an infinity value)

        #and set our PPS so we can see our swwwwwweeet performance stats
        with PPS_lock:
            PPS = justify(str(int(round(Nclock.get_fps(),0))), 3)

def start_game(name,port,ip,stretch):
    global running
    global player_lock
    global food_lock
    global player
    global food
    global buffersize
    global Serversquares
    global Serversquares_lock
    global Cs
    global clientnum

    #get the server's IP address
    ipaddr = ip
    #get the server's port
    portnum = port

    #a list full of Square() objects which gets computed/drawn/updated by the Compute,Render,and Netcode threads.
    Serversquares = []
    Serversquares_lock = _thread.allocate_lock()

    #netcode buffer size in BYTES (needs to be big enough to recieve a number up to 5 digits as a string)
    buffersize = 100

    #a flag which tells us whether we already lost the connection
    connection = True

    #attempt to connect to the server
    Cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create a python Socket object for our Client/game
    try:
        Cs.connect((ipaddr, int(portnum))) #try to establish a socket connection with the server
    except:
        print("    [ERROR] Couldn't connect to server!")
        connection = False
    if(connection):
        print("[OK] Connected to server!")
        Cs.settimeout(20) #(?) second timeout limit
##        try: #empty out the recieve buffer
##            Cs.recv(8)
##        except: #once we get a timeout error, continue.
##            pass
    if(connection):
        print("[OK] Connection established with server " + ipaddr) #debug info

    #attempt to retrieve the firstfruits of our connection - the server's pick of a connection buffer size
    if(connection): #we made it this far?
        try:
            buffersize = Cs.recv(buffersize)
        except:
            print("    [ERROR] Couldn't even grab the starting buffersize! Recieved: " + str(buffersize))
            connection = False
    if(connection):
        buffersize = int(buffersize.decode("utf-8"))
        print("[OK] Successfully grabbed buffer size: " + str(buffersize) + " bytes")
        Cs.send(justify("[ACK]",buffersize).encode('utf-8')) #we have to send back an acknowledgement packet. The content of it doesn't matter, as strange as it may seem.

    #we need a local player object
    player = Square()
    player_lock = _thread.allocate_lock()

    #now we need to recieve some data from the server. The square's starting position, mainly.
    if(connection):
        print("[INFO] Recieving start data...")
        try:
            Cdata = netcode.recieve_data_noerror(Cs,buffersize)
        except:
            print("    [ERROR] Connection Lost!!!! Data recieved: " + str(Cdata))
            connection = False
    if(connection):
        player.set_stats(eval(Cdata))
        print("    [OK] Recieved start data.")

    #next we need to send back some info - our name.
    if(connection):
        print("[INFO] Sending player name...")
        player.name = name
        Sendstuff = gather_data(player)
        try:
            netcode.send_data_noerror(Cs,buffersize,Sendstuff)
        except: #we probably timed out on our recieve signal...
            print("    [ERROR] Couldn't send player name!")
            connection = False
    if(connection):
        print("    [OK] Successfully sent name!")

    #now we need to get all the pieces of food in the game.
    #a list full of Square() objects which can only be eaten @ the moment (could change)
    if(connection):
        food = []
        food_lock = _thread.allocate_lock()
        print("[INFO] Getting food positions...")
        Fdata = [] #our food list
        Foodlen = int(Cs.recv(buffersize).decode('utf-8')) #get the length of the food list
        Cs.send(bytes("          ",'utf-8')) #send an empty 10 byte confirm signal
        try:
            for getfood in range(0,Foodlen):
                print("Attempting to grab piece " + str(getfood) + " of food right now...")
                tmpfood = netcode.recieve_data_noerror(Cs,buffersize,evaluate=True)
                Fdata.append(tmpfood[:])
        except:
            print("    [ERROR] Failed to recieve food positions! Data: " + str(tmpfood))
            connection = False
    if(connection):
        for x in range(0,len(Fdata)): #load it into our Food array
            food.append(Square()) #create a new Square() object
            food[len(food) - 1].set_stats(Fdata[x]) #load stats into it
            food[len(food) - 1].color = [255,255,0]
            food[len(food) - 1].textcolor = None
            food[len(food) - 1].food = True
        print("    [OK] Recieved food stats!")

    #we also need to get our client number...which can be sent without the need for extensive buffersize setups and all that.
    if(connection):
        print("[INFO] Recieving client number...")
        try:
            clientnum = Cs.recv(buffersize).decode('utf-8')
            clientnum = int(clientnum)
            Cs.send(bytes("          ",'utf-8')) #send an acknowledge signal
        except:
            print("    [ERROR] Failed to get our client number! Data recieved: " + str(clientnum))
            connection = False
    if(connection):
        print("    [OK] Recieved client number " + str(clientnum))

    pygame.time.delay(500) #delay a bit so we don't disconnect over a connection error

    #make sure our "running" variable is synced with our connection variable
    running = connection

    #thread start code
    _thread.start_new_thread(network,())
    _thread.start_new_thread(compute,())

    #start our main thread
    return renderer(stretch)

def get_port(m_handler):
    faulty = False
    while True: #get the port number of the server
        if(faulty == False):
            portnum = m_handler.get_input(display,"Please give me the port number of the server")
        else:
            portnum = m_handler.get_input(display,"Bad Portnum. Try again...")
        try: #valid port number?
            int(portnum)
            break #exit the endless loop of faulty port numbers
        except: #if not...
            faulty = True
    return portnum

#we needs to set up a menu system!
m_handler = menu.Menuhandler()

#we're still running our menu?
playing = True

#we needs to know where mouse is...
mouse_pos = [0,0]

#we pressed anything?
pressed_option = None

#default name, IP, and port settings
NAME = "Default"
IP = "0.0.0.0"
PORT = "5030"

#add some menus!
m_handler.create_menu(["Play","Options","Exit"],[[""],[""],[""]],[[1,1]],[],"Square-IO Multiplayer")
m_handler.create_menu(["Back","Stretched Gameplay","Server IP","Server Port Number","Player Name"],[[""],["True","False"],[IP],[PORT],[NAME]],[[0,0]],[],"Options")

#we're going to need this file to store, and recover our settings
options_file = open("save/options.pkl","rb+")
settings = pickle.load(options_file)[:]
options_file.close()

#use this to generate a settings file if you accidentally delete yours! Just re-comment out this line after shutting the game down the first time!
#settings = [["True",0],["0.0.0.0",0],["5000",0],["default",0]]

#load IP, PORT, and NAME variables
IP = settings[1][0]
PORT = settings[2][0]
NAME = settings[3][0]

#our exit buttons constant
EXIT_BUTTONS = [[[2, None], 0]]

#our options menu button
OPTIONS_BUTTON = [[1,None], 0]

#the back button from the settings menu
BACK_BUTTON = [[0,None], 1]

#our name, server IP and server port buttons
NAME_BUTTON = [[4,None], 1]
PORT_BUTTON = [[3,None], 1]
IP_BUTTON = [[2,None], 1]

#start button
GAME_START_BUTTON = [[0,None], 0]

#we're not ingame yet, so this variable goes false.
with running_lock:
    running = False

while playing: #basic menu setup to make the game more UI friendly
    m_handler.menuscale = display.get_width() / DEFAULTSIZE[0] * 1.0
    
    #event loop
    for event in pygame.event.get():
        if(event.type == pygame.QUIT): #we wants out???
            playing = False
        elif(event.type == pygame.MOUSEMOTION): #sync our mouse position to the mouse_pos variable
            mouse_pos = event.pos[:]
        elif(event.type == pygame.MOUSEBUTTONDOWN): #implement our menu collision system
            if(m_handler.currentmenu == 1): #if we're inside our settings menu...
                settings = m_handler.grab_settings(["Stretched Gameplay","Server IP","Server Port Number","Player Name"])
            pressed_option = m_handler.menu_collision([0,0],[display.get_width(),display.get_height()],mouse_pos)
            #check if we wants to quit?
            if(pressed_option in EXIT_BUTTONS):
                playing = False
            #does we wants to change our IP?
            elif(pressed_option == IP_BUTTON):
                IP = m_handler.get_input(display,"Please enter the server IP address")
                m_handler.reconfigure_setting([IP],IP,0,"Server IP")
            #does we wants to change our PORT?
            elif(pressed_option == PORT_BUTTON):
                PORT = get_port(m_handler)
                m_handler.reconfigure_setting([PORT],PORT,0,"Server Port Number")
            #does we wants to change our player name?
            elif(pressed_option == NAME_BUTTON):
                NAME = m_handler.get_input(display,"Please enter your player name")
                m_handler.reconfigure_setting([NAME],NAME,0,"Player Name")
            #does we wants to START THE GAME???
            elif(pressed_option == GAME_START_BUTTON):
                with running_lock:
                    running = True
                with in_menu_lock:
                    in_menu = False
                flags = start_game(NAME,PORT,IP,eval(settings[0][0]))
                settings[0][0] = str(flags[0])
                settings[0][1] = ["True","False"].index(str(flags[0]))
                settings[3][0] = flags[1]
            #we're going into our options menu?
            elif(pressed_option == OPTIONS_BUTTON):
                m_handler.reconfigure_setting(["True","False"],settings[0][0],settings[0][1],"Stretched Gameplay")
                m_handler.reconfigure_setting([settings[1][0]],settings[1][0],0,"Server IP")
                m_handler.reconfigure_setting([settings[2][0]],settings[2][0],0,"Server Port Number")
                m_handler.reconfigure_setting([settings[3][0]],settings[3][0],0,"Player Name")
            #if we're heading back from the settings menu, we need to check that we synced our settings with the ones in the menu...
            elif(pressed_option == BACK_BUTTON):
                NAME = settings[3][0]
                IP = settings[1][0]
                PORT = settings[2][0]

    #draw our menu
    m_handler.draw_menu([0,0],[display.get_width(),display.get_height()],display,mouse_pos)

    #flip the screen
    pygame.display.flip()

    #fill it with black for next frame
    display.fill([0,0,0])

#save our settings (SOS!) LOL
options_file = open("save/options.pkl","wb+")
pickle.dump(settings, options_file)
options_file.close()

pygame.quit()
