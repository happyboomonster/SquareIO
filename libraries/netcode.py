import netcode
import time #for getting ping

def justify(string,size): #a function which right justifies a string
    if(size - len(list(string)) > 0):
        tmpstr = " " * (size - len(list(string)))
        string = tmpstr + string
    return string

def send_data(Cs,buffersize,data): #sends some data without checking if the data made it through the wires
    datalen = justify(str(len(list(str(data)))),buffersize)
    data = str(data)
    Cs.send(bytes(datalen,'utf-8')) #send the buffersize of our data
    Cs.send(bytes(data,'utf-8')) #send the actual data

def recieve_data(Cs,buffersize,evaluate=False,returnping=False): #tries to recieve some data without checking its validity
    pingstart = time.time() #set a starting ping time
    Nbuffersize = int(Cs.recv(buffersize).decode('utf-8')) #get our data's buffersize
    data = Cs.recv(Nbuffersize).decode('utf-8') #recieve our data
    ping = int(1000.0 * (time.time() - pingstart)) #calculate our ping
    if(evaluate):
        try:
            data = eval(data)
        except: #if we didn't get good data, just return none.
            data = None
    if(returnping == False):
        return data
    else:
        return data, ping

def send_data_noerror(Cs,buffersize,data,ack="ACK"): #sends a packet of data as a string. Uses some basic error correction to lower the chances of disconnection
    datalen = justify(str(len(list(str(data)))),buffersize)
    data = str(data)
    while True:
        Cs.send(bytes(datalen,'utf-8')) #send the buffersize of our data
        acknowledge = Cs.recv(buffersize).decode('utf-8') #get a confirm signal in between sending data...which we do nothing with
        Cs.send(bytes(data,'utf-8')) #send the actual data
        acknowledge = Cs.recv(buffersize).decode('utf-8') #get a confirm signal after sending data
        if(acknowledge == justify(ack,buffersize)): #we got a successful data packet through?
            break #exit this annoying loop!

def recieve_data_noerror(Cs,buffersize,evaluate=False,returnping=False,ack="ACK"): #recieves a packet of data as a string. Uses some basic error correction to lower the chances of disconnection
    pingstart = time.time() #set a starting ping time
    while True:
        Nbuffersize = int(Cs.recv(buffersize).decode('utf-8')) #get our data's buffersize
        Cs.send(bytes(justify(ack,buffersize),'utf-8')) #send an acknowledge signal
        data = Cs.recv(Nbuffersize).decode('utf-8') #recieve our data
        #once we get our data, now we have to check it for errors...
        if(evaluate): #if we're planning on pre-evaluating our data, use that as a check to check for errors.
            try:
                eval(data)
            except: #that data didn't get through?
                Cs.send(bytes(justify("nak",buffersize),'utf-8')) #we didn't get through...
                continue
        #also, we know that our data should be a certain length. Check the recieved length against what was supposed to be recieved...
        if(Nbuffersize != len(list(data))):
            Cs.send(bytes(justify("nak",buffersize),'utf-8')) #we didn't get through...
        else:
            Cs.send(bytes(justify(ack,buffersize),'utf-8'))
            break #exit this loop for crying out loud!
    ping = int(1000.0 * (time.time() - pingstart)) #calculate our ping
    if(evaluate):
        data = eval(data)
    if(returnping == False):
        return data
    else:
        return data, ping
