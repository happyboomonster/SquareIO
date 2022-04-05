import socket
import time #for getting ping

def justify(string,size): #a function which right justifies a string
    if(size - len(list(string)) > 0):
        tmpstr = " " * (size - len(list(string)))
        string = tmpstr + string
    return string

def send_data(Cs,buffersize,data): #sends some data without checking if the data made it through the wires
    datalen = justify(str(len(list(str(data)))),buffersize)
    data = str(data)
    Cs.send(bytes(datalen + data,'utf-8')) #send the buffersize of our data followed by the data itself

def recieve_data(Cs,buffersize,returnping=False,timeout=20): #tries to recieve some data without checking its validity
    pingstart = time.time() #set a starting ping time
    Nbuffersize = Cs.recv(buffersize) #get our data's buffersize
    try:
        Nbuffersize = int(Nbuffersize.decode('utf-8'))
        try:
            data = Cs.recv(Nbuffersize) #recieve our data
            data = data.decode('utf-8')
        except:
            data = None
    except:
        moredata = ""
        Cs.settimeout(0.02) #we need to temporarily set this to a low value so we can resync our send/recieve socket buffers to continue packet exchange.
        while True: #try to empty the Cs buffer of data so we can get back into sync next packet
            try:
                moredata += Cs.recv(pow(10,buffersize)).decode('utf-8') #recieve 10^buffersize bytes
            except: #this exception should only occur once we empty the buffer of data we were sent.
                break #Which will in turn exit this loop, and we should be back into sync with the server!
        #Now that we've recieved any extra data that hasn't exited the buffer yet, add it to "data" so that *maybe*(?) we still get a packet through???
        try: #if things go wrong..."data" won't even exist, causing this to throw up an error.
            data += moredata
        except:
            data = None
        Cs.settimeout(timeout) #reset the packet timeout to its normal state
    try: #now we *try* to evaluate our data
        data = eval(data)
    except: #we couldn't evaluate our data???
        moredata = ""
        Cs.settimeout(0.02) #we need to temporarily set this to a low value so we can resync our send/recieve socket buffers to continue packet exchange.
        while True: #try to empty the Cs buffer of data so we can get back into sync next packet
            try:
                moredata += Cs.recv(pow(10,buffersize)).decode('utf-8') #recieve 10^buffersize bytes
            except: #this exception should only occur once we empty the buffer of data we were sent.
                break #Which will in turn exit this loop, and we should be back into sync with the server!
        #Now that we've recieved any extra data that hasn't exited the buffer yet, add it to "data" so that *maybe*(?) we still get a packet through???
        try: #if we didn't even get data through, this variable won't even exist!
            data += moredata
        except:
            data = None
        Cs.settimeout(timeout) #reset the packet timeout to its normal state
        try: #we try to evaluate our data one more time...
            data = eval(data)
        except:
            data = None
    ping = int(1000.0 * (time.time() - pingstart)) #calculate our ping
    if(returnping == False):
        return data
    else:
        return data, ping

def send_data_noerror(Cs,buffersize,data,ack="ACK"): #sends a packet of data as a string. Uses some basic error correction to lower the chances of disconnection
    datalen = justify(str(len(list(str(data)))),buffersize)
    data = str(data)
    while True:
        Cs.send(bytes(datalen + data,'utf-8')) #send the buffersize of our data with the data at the same time
        acknowledge = Cs.recv(buffersize) #get a confirm signal after sending data
        acknowledge = acknowledge.decode('utf-8')
        if(acknowledge == justify(ack,buffersize)): #we got a successful data packet through?
            break #exit this annoying loop!

def recieve_data_noerror(Cs,buffersize,evaluate=False,returnping=False,ack="ACK"): #recieves a packet of data as a string. Uses some basic error correction to lower the chances of disconnection
    pingstart = time.time() #set a starting ping time
    while True:
        donteval = False
        Nbuffersize = Cs.recv(buffersize).decode('utf-8') #get our data's buffersize
        print(Nbuffersize)
        try:
            Nbuffersize = int(Nbuffersize)
        except:
            donteval = True
            Cs.send(bytes(justify("nak",buffersize),'utf-8')) #we didn't get through...
        data = Cs.recv(Nbuffersize).decode('utf-8') #recieve our data
        #once we get our data, now we have to check it for errors...
        if(evaluate and not donteval): #if we're planning on pre-evaluating our data, use that as a check to check for errors.
            try:
                eval(data)
            except: #that data didn't get through?
                Cs.send(bytes(justify("nak",buffersize),'utf-8')) #we didn't get through...
                continue
        #also, we know that our data should be a certain length. Check the recieved length against what was supposed to be recieved...
        if(not donteval and Nbuffersize != len(list(data))):
            Cs.send(bytes(justify("nak",buffersize),'utf-8')) #we didn't get through...
        elif(not donteval):
            Cs.send(bytes(justify(ack,buffersize),'utf-8'))
            break #exit this loop for crying out loud!
    ping = int(1000.0 * (time.time() - pingstart)) #calculate our ping
    if(evaluate):
        data = eval(data)
    if(returnping == False):
        return data
    else:
        return data, ping
