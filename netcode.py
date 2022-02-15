import netcode
import time #for getting ping

def justify(string,size): #a function which right justifies a string
    if(size - len(list(string)) > 0):
        tmpstr = " " * (size - len(list(string)))
        string = tmpstr + string
    return string

def send_data(Cs,buffersize,data):
    datalen = justify(str(len(list(str(data)))),10)
    data = str(data)
    Cs.send(bytes(datalen,'utf-8')) #send the buffersize of our data
    acknowledge = Cs.recv(buffersize) #get a confirm signal in between sending data...which we do nothing with
    Cs.send(bytes(data,'utf-8')) #send the actual data

def recieve_data(Cs,buffersize,evaluate=False,returnping=False):
    pingstart = time.time() #set a starting ping time
    Nbuffersize = int(Cs.recv(buffersize).decode('utf-8')) #get our data's buffersize
    Cs.send(bytes(justify("ACK",buffersize),'utf-8')) #send an acknowledge signal
    data = Cs.recv(Nbuffersize) #recieve our data
    ping = int(1000.0 * (time.time() - pingstart)) #calculate our ping
    if(evaluate):
        data = eval(data)
    if(returnping == False):
        return data
    else:
        return data, ping
