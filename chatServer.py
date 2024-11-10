from sql_db import * 
import socket
import select
import sys
import traceback
from User import User


# maps the clients username to their socket object
connected_clients = []
web_servers = []

def traceback_message():
  print("-"*60)
  traceback.print_exc(file = sys.stdout)
  print("-"*60)
    
    
# sends a message from the server to all the connected clients
def send_message(messages, include_sender = True, sender = ""):
  global connected_clients

  message = messages  
 
  for client in connected_clients:
    try:   
      if not include_sender:
        if client.username != sender:
          client.client_socket.sendall(message.encode("UTF-8"))

      else:
        client.client_socket.sendall(f"\n{message}".encode("UTF-8"))

    except Exception as e:
      print(f"Error occurred while sending a message to {client.username}: {e}")
      traceback_message()
  
  if include_sender:
    print(message)


# splits un the protocoled message sent by the client
def split_message(unfiltered_message):
  try:
    timestamp, username, message = None, None, None

    # format -> [timestamp] username: message
    if unfiltered_message:
      timestamp_part, rest = unfiltered_message.split("] ", 1)
      username, message = rest.split(": ", 1)
      timestamp = timestamp_part[1:]

  except ValueError as ve:
    print(f"Error occurred while parsing the message recieved: {ve}")
    traceback_message()

  return timestamp, username, message  


# adds a message to the messages db and updates clients' last seen message and number of messages sent
def add_message(cursor, connection, timestamp, sender, message):
  add_new_message(cursor, connection, timestamp, sender, message)
  
  update_messages_sent_number(cursor, connection, sender)
  update_client_last_seen_message(cursor, connection, cursor.lastrowid)

  # send to the other clients
  send_message(format_messages([(timestamp, sender, message)]), include_sender = False, sender = sender) 
     

# deals with the messages that are recieved    
def handle_message(cursor, connection, unfiltered_message, client_socket):   
  timestamp, sender, message = split_message(unfiltered_message)
  try:
    for client in connected_clients:
      if client.client_socket is client_socket and client.username != sender:
        client.changeUsername(sender)
    
        if find_client(cursor, sender):
          update_connection_status(cursor, connection, sender, 'active')
          send_last_and_unread_messages(cursor, connection, sender, client_socket)
        else:
          send_last_few_messages(cursor, connection, client_socket)
          add_client(cursor, connection, sender)
          send_message(f"{sender} has joined the chat.")
        break
  
    if timestamp and sender and message:
      if message == "quit chat" or message == "exit":
        remove_client(cursor, connection, sender, client_socket)
      elif message != "super secret entry message.":
        add_message(cursor, connection, timestamp, sender, message)

    else:
      raise Exception("A client disconnected incorrectly.")
  except Exception as e:
    print("Error:", e)
    remove_client(cursor, connection, sender, client_socket)
    traceback_message()


#recieves all the messages from a client
def receive_message(cursor, connection, client_socket):
  username = ''
  
  try:
    for client in connected_clients:
      if client.client_socket == client_socket:
        username = client.username
        break

    default_size = 1024
    full_message = b''
  
    while True:
      message_chunk = client_socket.recv(default_size)
      full_message += message_chunk

      if len(message_chunk) <= default_size: 
        break
    
    if full_message:
      unfiltered_messages_list = full_message.decode("UTF-8").split("\n")

      for unfiltered_message in unfiltered_messages_list:
        if unfiltered_message:
          handle_message(cursor, connection, unfiltered_message, client_socket)

    else:
      raise Exception("Client disconnected.")

  except Exception as e:
    print("Error:", e)
    remove_client(cursor, connection, username, client_socket)


# removes the client from the connected client list and closes the connection
def remove_client(cursor, connection, username, client_socket):
  global connected_clients

  update_connection_status(cursor, connection, username, 'inactive')

  try:
    client_socket.close()
    connected_clients = [client for client in connected_clients if client.username != username]
    print(f"{username} has disconnected")  

  except Exception as e:
    print(f"Error occurred while closing socket for {username}: {e}")
    traceback_message()

  send_message(f"{username} has left the chat.", include_sender = False, sender = username)


# formats the messages before sending them to the client
def format_messages(unformatted_messages_list):
  formatted_messages_list = []
  
  for timestamp, sender, message in unformatted_messages_list:
    formatted_message = f"[{timestamp}] {sender}: {message}"
    formatted_messages_list.append(formatted_message)
  
  messages_list = "\n".join(formatted_messages_list)
  
  return messages_list


# gets all the messages that the client has not seen and the last few messages from the chat 
def get_unread_messages(cursor, username):
  result = get_last_seen_msg_id(cursor, username)

  if result is None or result[0] is None:
    last_seen_message_id = 0
    last_few_messages = []
  else:
    last_seen_message_id = result[0]
    last_few_messages = get_last_30_msg_before_cutoff(cursor, last_seen_message_id)

  unread_messages = get_msg_after_cutoff(cursor, last_seen_message_id)

  return format_messages(list(reversed(last_few_messages))), format_messages(unread_messages)


# if the client is recurrng send them their unread messages and some of the last few messages
def send_last_and_unread_messages(cursor, connection, username, client_socket):
  last_few_messages, unread_messages = get_unread_messages(cursor, username)

  if unread_messages is not None and last_few_messages is not None:
    try:
      if last_few_messages:   
        client_socket.sendall(last_few_messages.encode("UTF-8"))

      if unread_messages:
        unread = f"\n\nUnread Messages:\n{unread_messages}\n"
        client_socket.sendall(unread.encode("UTF-8"))

      # update the clients last message seen 
      last_message_id = latest_msg_id(cursor)
      update_client_last_seen_message(cursor, connection, last_message_id[0])

    except Exception as e:
      print("Error occurred when sending unread messages to", username)
      remove_client(cursor, connection, username, client_socket)
      traceback_message()
    

# if the client is new to the db, send them the last 100 messages
def send_last_few_messages(cursor, connection, client_socket):
  last_few_messages = get_last_30_msg(cursor)
  
  formatted_messages_list = format_messages(list(reversed(last_few_messages))) + "\n"

  if formatted_messages_list:
    try:
      # send the previous 100 messages to the client
      client_socket.sendall(formatted_messages_list.encode("UTF-8"))

      # update the clients last message seen id
      last_message_id = latest_msg_id(cursor)
      update_client_last_seen_message(cursor, connection, last_message_id[0])

    except Exception as e:
      print("Error occurred when sending messages-log new client") 
      traceback_message()


# deals with the server's shutdown
def shutdown(cursor, connection, server_socket):
  global connected_clients

  print("\nShutting down server...")

  for client in connected_clients:
    try:
      (client.client_socket).sendall(b"The server is shutting down. This connection is closing...\n")
    except Exception as e:
      print(f"Error occured while sending shutdown message to {client.username}: {e}")
      traceback_message()
    finally: 
      try:
        update_connection_status(cursor, connection, client.username, 'inactive')
        (client.client_socket).close()
      except Exception as e:
        print(f"Error occured while closing socket for {client.username}: {e}")
        traceback_message()

  connection.close()
  connected_clients.clear()
  server_socket.close()
  sys.exit(0)


def handle_web_server_get(cursor, client_socket, timestamp):
  global web_servers
 
  try: 
    unformatted_messages = get_msg_for_web_client(cursor, timestamp)
    messages = format_messages(list(reversed(unformatted_messages)))
    client_socket.sendall(messages.encode("UTF-8"))  
    web_servers = [client for client in web_servers if client != client_socket]
    client_socket.close()
 
  except Exception as e:
    web_servers = [client for client in web_servers if client != client_socket]
    client_socket.close()
               

def handle_web_server_get_all(cursor, client_socket):
  global web_servers

  try: 
    unformatted_messages = get_all_msg(cursor)
    messages = format_messages(unformatted_messages)
    client_socket.sendall(messages.encode("utf-8"))
    web_servers = [client for client in web_servers if client != client_socket]
    client_socket.close()
        
  except Exception as e:
    web_servers = [client for client in web_servers if client != client_socket]
    client_socket.close()


def handle_web_server_post(cursor, connection, client_socket, msg):
  global web_servers 
  
  try:
    unfiltered_messages_list = msg.split("\n")

    for unfiltered_message in unfiltered_messages_list:
      if unfiltered_message:
        timestamp, sender, message = split_message(unfiltered_message)
      
        if timestamp and sender and message:
          add_new_message(cursor, connection, timestamp, sender, message)
          send_message(format_messages([(timestamp, sender, message)]), False, sender)

    client_socket.sendall("DONE".encode("UTF-8"))
    web_servers = [client for client in web_servers if client != client_socket]
    client_socket.close()
       
  except Exception as e:
    web_servers = [client for client in web_servers if client != client_socket]
    client_socket.close()


def receive_web_message(cursor, connection, client_socket):
  default_size = 1024
  full_message = b''

  try:  
    while True:
      message_chunk = client_socket.recv(default_size)
      full_message += message_chunk

      if len(message_chunk) <= default_size: 
        break

  except Exception as e:
    print("Error:", e)
    traceback_message()
  return full_message


def main():
  global connected_clients
  global web_servers

  connection, cursor = initialize_db()
  server_host = ""
  server_port = 8576
  web_port = 8578
 
  print(f"Listening on interface {socket.gethostname()} on port {server_port} for clients and {web_port} for webserver")
    
  # binging and listening to a host and port
  server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server_socket.setblocking(False) # non-blocking
  server_socket.bind((server_host, server_port))
  server_socket.listen()
  
  web_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  web_socket.setblocking(False) # non-blocking
  web_socket.bind((server_host, web_port))
  web_socket.listen()
 
  print("To close the server press 'Ctrl + C'\nWaiting for input...")

  while True:
    try:
      inputs = [server_socket] + [client.client_socket for client in connected_clients] + [web_socket] + web_servers 
      
      readable, writable, exceptional = select.select(inputs, [], inputs)
       
      for source in readable:
        if source is server_socket:
          # then we have a new client, accept new connection
          client_socket, client_address = server_socket.accept()
          print("Accepting connection from:", client_address)

          new_client = User(client_socket)
          connected_clients.append(new_client) 
        
        elif source is web_socket:
          client_socket, client_address = web_socket.accept()
          print("Accepting connection from:", client_address)
          web_servers.append(client_socket)
         
        else:
          if source in web_servers:
            full_message = receive_web_message(cursor, connection, source).decode("UTF-8")
            if full_message:
              msg = full_message.split(":", 1)
             
              if msg[0] == "webserver GET SOME" and msg[1]:
                handle_web_server_get(cursor, source, msg[1])
            
              elif msg[0] == "webserver GET ALL":
                handle_web_server_get_all(cursor, source)

              elif msg[0] == "webserver POST" and msg[1]:
                handle_web_server_post(cursor, connection, source, msg[1])
               
          else:
            receive_message(cursor, connection, source)
                 
    except KeyboardInterrupt:
      for client in web_servers:
        web_servers.remove(client)      
        client.close()

      shutdown(cursor, connection, server_socket)
      
    except Exception as e: 
      print("Error:", e)
      
      for client in web_servers:
        web_servers.remove(client)
        client.close()

      shutdown(cursor, connection, server_socket)
      traceback_message()
      
      
if __name__ == "__main__":
  main()

