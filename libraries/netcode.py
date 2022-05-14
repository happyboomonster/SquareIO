#NETCODE.PY library by Lincoln V. ---VERSION 0.24---

import socket
import time #for getting ping

#a constant which tells how long the recieve_data() command will wait for extra packets to arrive.
PACKET_TIME = [0.25] #in seconds - This is a list because recieve_data() can have different packet time values for individual clients.
PACKET_TIME_MIN = 0.05 #the minimum packet timeout PACKET_TIME can have

#a counter for our packets - this number can grow quite large, which is why there is a reset counter constant below it...
packet_count = 0
MAX_PACKET_CT = 65535

#the default timeout value for socket.recv() functions
DEFAULT_TIMEOUT = 5.0 #seconds

#some premade error messages, as well as some constants to help show which message corresponds to which index in the error msgs list
ERROR_MSGS = [
    "[PACKET LOSS] Failed to retrieve buffersize!",
    "[PACKET LOSS] Failed to retrieve an initial data burst through the socket connection!",
    "[PACKET WARNING] Couldn't evaluate the data string INITIALLY - Retrying...",
    "[PACKET WARNING] Couldn't evaluate the data string - Retrying...",
    "[PACKET LOSS] Lost the packet during final evaluation!",
    "[DISCONNECT] Lost 25 packets in a row, and a client has been disconnected!",
    "[PACKET WARNING] Initial error with buffersize data"
    ]
BUFFERSIZE_FAIL = 0 #failed to retrieve buffersize
INITIAL_DATA_BURST = 1 #failed to retrieve the initial burst of data through the socket
INITIAL_EVAL = 2 #this is the first time we try to evaluate a data string. Sometimes works, sometimes doesn't.
EVAL = 3 #>1 time that we try to evaluate a data string. Most packets which enter this phase of recovery come out unscathed.
LOST_EVAL = 4 #>1 time we try to evaluate a data string, and fails.
CONNECTION_LOST = 5 #when we lose so many packets that our connection is considered lost
BUFFERSIZE_WARNING = 6 #we don't get any data initially when we use .recv() to grab the buffersize

#configures a socket so that it works with this netcode library's send/recieve commands - also resets the timeout value to DEFAULT_TIMEOUT
def configure_socket(a_socket):
    a_socket.setblocking(True)
    a_socket.settimeout(DEFAULT_TIMEOUT)

def justify(string,size): #a function which right justifies a string
    if(size - len(list(string)) > 0):
        tmpstr = " " * (size - len(list(string)))
        string = tmpstr + string
    return string

def socket_recv(Cs,buffersize): #recieves data, and catches errors.
    errors = None
    data = None
    try:
        data = Cs.recv(buffersize)
    except socket.error: #the socket is broken?
        errors = "disconnect"
    except: #a timeout or something else happened?
        errors = "timeout"
    return data, errors

def send_data(Cs,buffersize,data): #sends some data without checking if the data made it through the wires
    datalen = justify(str(len(list(str(data)))),buffersize)
    data = str(data)
    bytes_ct = 0 #how many characters we have sent
    total_data = datalen + data #the total data string we need to send
    try:
        while (bytes_ct < len(str(data))): #send our our data, making sure that all bytes of it are sent successfully
            bytes_ct += Cs.send(bytes((datalen + data)[bytes_ct:],'utf-8'))
    except: #this exception occurs when the socket dies, or if we simply can't send the data for some reason (connection refused?)
        return False #our connection is dead
    return True #our socket is still fine

def recieve_data(Cs,buffersize,client_number=0): #tries to recieve some data without checking its validity
    #   --- Basic setup with some preset variables ---
    global packet_count #a variable which keeps track of how many packets we've recieved.
    global PACKET_TIME #constant which is how long packets should be waited for
    errors = [] #a list of errors - we can append strings to it, which we can then log once the function is completed.
    ping_start = time.time() #set a starting ping time
    data = "" #we set a default value to data, just so we don't get any exceptions from the variable not existing.
    connected = True #are we still connected to the socket properly?
    #   --- Make sure there is an initial value of 0.25 seconds inside PACKET_TIME[client_number] if it doesn't exist ---
    if(len(PACKET_TIME) - 1 < client_number):
        for x in range(0,client_number - (len(PACKET_TIME) - 1)): #add values of 0.25 seconds to PACKET_TIME until it is length of client_number
            PACKET_TIME.append(0.25)
    #   --- Handling packet numbering ---
    packet_count += 1
    if(packet_count > MAX_PACKET_CT):
        packet_count = 0
    #   --- get our data's buffersize ---
    Nbuffersize = "" #empty value for our buffersize
    Nbuffersize_data_pack = socket_recv(Cs,buffersize)
    if(Nbuffersize_data_pack[1] == "disconnect"): #we lost da connection
        connected = False
    elif(Nbuffersize_data_pack[1] == 'timeout'):
        errors.append("(" + justify(str(packet_count),5) + ") " + ERROR_MSGS[BUFFERSIZE_WARNING])
    else:
        Nbuffersize = Nbuffersize_data_pack[0].decode('utf-8')
    Cs.settimeout(PACKET_TIME[client_number]) #shorten our socket timeout
    while len(list(Nbuffersize)) < buffersize: #If Nbuffersize isn't a length of buffersize yet, we need to try recieve a bit more...
        data_pack = socket_recv(Cs,buffersize - len(list(Nbuffersize)))
        if(data_pack[1] == "disconnect"): #we got socket.error?
            connected = False #connection lost then...
            break
        elif(data_pack[1] == "timeout"): #we just timed out???
            data = None
            errors.append("(" + justify(str(packet_count),5) + ") " + ERROR_MSGS[BUFFERSIZE_FAIL])
            break
        else:
            Nbuffersize += data_pack[0].decode('utf-8')
    try:
        Nbuffersize = int(Nbuffersize)
    except:
        errors.append("(" + justify(str(packet_count),5) + ") " + ERROR_MSGS[BUFFERSIZE_FAIL])
        data = None
    configure_socket(Cs) #reset our socket timeout to what it was
    #   --- now we try to grab an initial burst of data ---
    if(data != None):
        data_pack = socket_recv(Cs,Nbuffersize)
        if(data_pack[1] == 'disconnect'): #connection lost?
            connected = False
        elif(data_pack[1] == 'timeout'):
            errors.append("(" + justify(str(packet_count),5) + ") " + ERROR_MSGS[INITIAL_DATA_BURST])
        else:
            data = data_pack[0].decode('utf-8')
    #   --- Now we try to evaluate our data, and hope it just works the first time ---
    if(data != None):
        initial_success = True
        try:
            data = eval(data)
        except: #it didn't work? Well then we set this flag so that we know we need to try something else before we count the data as lost...
            errors.append("(" + justify(str(packet_count),5) + ") " + ERROR_MSGS[INITIAL_EVAL])
            initial_success = False
    #   --- IF we lost our data somewhere in this mess, we need to make sure to empty the data buffer ---
    if(data == None):
        Cs.settimeout(PACKET_TIME[client_number]) #shorten our socket timeout value
        while True:
            data_pack = socket_recv(Cs,pow(10,buffersize))
            if(data_pack[1] == 'timeout'): #we're out of data?
                break
            elif(data_pack[1] == 'disconnect'): #the socket died on us???
                connected = False
                break
        configure_socket(Cs) #set our socket timeout back to a large value
    #   --- IF we can't evaluate the data string as-is, we try to see if there is ANYTHING left in the socket buffer ---
    else: #this occurs if data != None
        if(initial_success == False):
            Cs.settimeout(PACKET_TIME[client_number]) #shorten our socket timeout value
            while len(list(data)) < Nbuffersize: #grab some data if we can
                data_pack = socket_recv(Cs,Nbuffersize - len(list(data)))
                if(data_pack[1] == 'timeout'): #if we got a timeout error, we ran out of data to retrieve...packet LOST
                    errors.append("(" + justify(str(packet_count),5) + ") " + ERROR_MSGS[LOST_EVAL])
                    break
                elif(data_pack[1] == 'disconnect'): #well if this happens, we're really out of luck.
                    connected = False
                    break
                else: #nothing went wrong yet???
                    data += data_pack[0].decode('utf-8')
                try: #try to evaluate the data string again after recieving more tidbits of it
                    data = eval(data) #IF we can evaluate the data, then we break this loop.
                    break
                except: #else, we repeat this loop, trying to grab more data from the buffer cache, and hoping that it completes this data string...
                    errors.append("(" + justify(str(packet_count),5) + ") " + ERROR_MSGS[EVAL])
                    pass
            configure_socket(Cs) #set our socket timeout back to a large value
    #   --- calculate our ping ---
    ping = int(1000.0 * (time.time() - ping_start))
    #   --- Account for laggy packets ---
    if(len(errors) > 0):
        if(PACKET_TIME[client_number] < ping / 995.0): #if our PACKET_TIME is smaller than our ping, set PACKET_TIME to the new ping value.
            PACKET_TIME[client_number] = (ping / 995.0) #set our packet time wait to our ping time to compensate for bad latency spikes
        elif(PACKET_TIME[client_number] > (ping/1000.0) * 1.1): #if our ping is below PACKET_TIME by roughly 10%, we decrease our PACKET_TIME by 9%
            PACKET_TIME[client_number] = PACKET_TIME[client_number] * 0.91
    #   --- Restrict our packet time variable from going too low ---
    if(PACKET_TIME_MIN > PACKET_TIME[client_number]): #is our minimum packet time greater than our packet time value???
        PACKET_TIME[client_number] = PACKET_TIME_MIN #set our packet time to the minimum because we went too low
    return [data, ping, errors, connected] #return the data this function gathered

def send_data_noerror(Cs,buffersize,data,ack="ACK"): #sends a packet of data as a string. Uses some basic error correction to lower the chances of disconnection
    datalen = justify(str(len(list(str(data)))),buffersize)
    data = str(data)
    while True:
        Cs.sendall(bytes(datalen + data,'utf-8')) #send the buffersize of our data with the data at the same time
        acknowledge = Cs.recv(buffersize) #get a confirm signal after sending data
        acknowledge = acknowledge.decode('utf-8')
        if(acknowledge == justify(ack,buffersize)): #we got a successful data packet through?
            break #exit this annoying loop!

def recieve_data_noerror(Cs,buffersize,evaluate=False,returnping=False,ack="ACK"): #recieves a packet of data as a string. Uses some basic error correction to lower the chances of disconnection
    pingstart = time.time() #set a starting ping time
    while True:
        donteval = False
        Nbuffersize = Cs.recv(buffersize).decode('utf-8') #get our data's buffersize
        try:
            Nbuffersize = int(Nbuffersize)
        except:
            donteval = True
            Cs.sendall(bytes(justify("nak",buffersize),'utf-8')) #we didn't get through...
        data = Cs.recv(Nbuffersize).decode('utf-8') #recieve our data
        #once we get our data, now we have to check it for errors...
        if(evaluate and not donteval): #if we're planning on pre-evaluating our data, use that as a check to check for errors.
            try:
                eval(data)
            except: #that data didn't get through?
                Cs.sendall(bytes(justify("nak",buffersize),'utf-8')) #we didn't get through...
                continue
        #also, we know that our data should be a certain length. Check the recieved length against what was supposed to be recieved...
        if(not donteval and Nbuffersize != len(list(data))):
            Cs.sendall(bytes(justify("nak",buffersize),'utf-8')) #we didn't get through...
        elif(not donteval):
            Cs.sendall(bytes(justify(ack,buffersize),'utf-8'))
            break #exit this loop for crying out loud!
    ping = int(1000.0 * (time.time() - pingstart)) #calculate our ping
    if(evaluate):
        data = eval(data)
    if(returnping == False):
        return data
    else:
        return data, ping
