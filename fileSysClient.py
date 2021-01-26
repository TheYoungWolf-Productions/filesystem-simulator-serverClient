import socket
import pickle
import time

ClientMultiSocket = socket.socket()
host = '127.0.0.1'
# host = '192.356.31.3'
port = 21018
attempts = 0
print('Waiting for connection response...\n')

while True:
    try:
        ClientMultiSocket.connect((host, port))
        print('CONNECTED')
        break
    except socket.error as e:
        attempts += 1
        if (attempts > 4):
            print('No response from server, try again later.')
            exit(0)
        print('Server is offline, trying again in 2 seconds...')
        time.sleep(2)

res = ClientMultiSocket.recv(32768)
usernameInput = input('\nEnter your username: ')
ClientMultiSocket.send(str.encode(usernameInput))
print('Logged into filesystem with the username, ' + usernameInput + '\n')

print('>> ', end='')
while True:
    Input = input()
    ClientMultiSocket.send(str.encode(Input))
    if(Input == 'exit'):
        break
    res = ClientMultiSocket.recv(32768)
    res_data = pickle.loads(res)
    if(res_data[0] == 'exit'):
        print('\nServer Inaccessible: Request quota exceeded, try later.')
        print('Bye!')
        break
    print('\n' + res_data[0])
    print(res_data[1] + '>> ', end='')
ClientMultiSocket.close()
