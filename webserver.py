import json
import socket
import threading
import traceback
import sys
from datetime import datetime
from file_handling import getFileContent
 

def traceback_message():
    print("-"*60)
    traceback.print_exc(file = sys.stdout)
    print("-"*60)
    
    
def main():
  global chat_server_host
  global chat_server_port
  global web_socket
  
  try:
    try:
      if len(sys.argv) != 3:
        raise Exception
            
      chat_server_host = sys.argv[1]
      chat_server_port = int(sys.argv[2]) 
    except Exception as e:
      print("Usage: python webserver.py <CHAT_SERVER_HOST> <CHAT_SERVER_PORT>")
      sys.exit(1)
      
    webserver_host = ""
    webserver_port = 8577
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as web_socket:  
      web_socket.bind((webserver_host, webserver_port))
      web_socket.listen()

      print(f"Listening on interface {socket.gethostname()} on port {webserver_port}")
      print("To close the server press 'Ctrl + C'\nWaiting for input...")

      while True:
        client_socket, client_address = web_socket.accept()
        myThread = threading.Thread(target = handle_client, args = (client_socket,))
        myThread.start() #run()
      
  except Exception as e:
    traceback_message() 

  
def handle_client(client_socket):    
  try: 
    request = client_socket.recv(1024).decode("UTF-8") 

    #split the request into 2 parts - header and body 
    header_section, body_section = request.split('\r\n\r\n')
      
    headers =  header_section.split('\r\n')
    components = headers[0].split()
    http_method = components[0]
    relative_path = components[1]
  
    if "Cookie:" in header_section:
      username = get_cookie(header_section)
      response = handle_requests(http_method, relative_path, username, body_section)
    else:
      if relative_path != '/' and not relative_path.endswith('.js') and not relative_path.startswith('/api'):
        response = get_other_files(relative_path)
      else:
        response = homepage(relative_path, body_section)
      
    client_socket.sendall(response.encode("UTF-8"))
  
  except KeyboardInterrupt:
    print("server is shutting down...")
  
  except Exception as e:
    traceback_message()
    print("An error coourred:", e)
  
  finally:
    client_socket.close()
  
 
def handle_requests(http_method, relative_path, username, body_section):
  response = ""
  
  if http_method == 'GET':
    response = handle_get_request(relative_path, username, body_section)
  elif http_method == 'POST':
    response = handle_post_request(relative_path, username, body_section)
  elif http_method == 'DELETE':
    response = handle_delete_request(relative_path, username)
  return response

    
def recieve_message(client_socket):
  default_size = 1024
  full_message = b''
  
  while True:
    message_chunk = client_socket.recv(default_size)
    
    if not message_chunk:
      break

    full_message += message_chunk
   
  return full_message.decode("UTF-8")


def set_protocol(username, message):
  timestamp = datetime.now()   
  formatted_message = f"[{timestamp}] {username}: {message}\n"
  
  return formatted_message
  

def get_cookie(header_section):
  headers =  header_section.split('\r\n')
  username = None
    
  for header in headers:
    if header.startswith("Cookie:"): 
      cookies = header.split(": ", 1)[1]

      for cookie in cookies.split(";"):
        if cookie.strip().startswith("session_id="): 
          username = cookie.split("=", 1)[1]
          break
      break
      
  return username
  

def homepage(relative_path, body_section):
  response = ""

  if relative_path == '/':
    response = get_html()
    
  elif relative_path.endswith('.js'):
    response = get_javascript(relative_path)  
    
  elif relative_path == '/api/login':    
    response = post_login(body_section)
 
  else:
    response = "HTTP/1.1 401 Unauthorized\nContent-Type: text/html\n\n<h1>Unauthorized Access<h1>" 
 
  return response
  
  
def get_html():
  content = getFileContent("index.html")
  
  if content:
    response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: {len(content)}\r\n\r\n{content}"
  else:
    response = "HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n<h1>File Not Found<h1>"
  return response


def get_javascript(relative_path):
  filename = relative_path.strip('/')
  content = getFileContent(filename)
      
  if content:
    response = f"HTTP/1.1 200 OK\r\nContent-Type: application/javascript\r\nContent-Length: {len(content)}\r\n\r\n{content}"
  else:
    response = "HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n<h1>File Not Found<h1>"
  return response
  
  
def get_messages(username, sent_timestamp):
  response = ''
  content = ''
  timestamp = sent_timestamp.replace('%20', ' ')

  if username:
    try:
      with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as web_socket:
        web_socket.connect((chat_server_host, chat_server_port))
        web_socket.sendall(f"webserver GET SOME:{timestamp}".encode("UTF-8"))
        recieved = recieve_message(web_socket) 

      messages = recieved.split("\n")      
      content = json.dumps(messages)
      response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(content)}\r\n\r\n{content}"
    except Exception as e:
      print("Chat Server is down, so can't get messages.")  
      
  else:
    content = json.dumps({"error": "Not Logged in."})
    response = f"HTTP/1.1 401 Unauthorized\r\nContent-Type: application/json\r\nContent-Length: {len(content)}\r\n\r\n{content}"
                                                                                                                                               
  return response


def get_all_messages(username): 
  response = ''
  content = ''
  
  if username:
    try:
      with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as web_socket:
        web_socket.connect((chat_server_host, chat_server_port))
        web_socket.sendall(f"webserver GET ALL:".encode("UTF-8"))
        recieved = recieve_message(web_socket)
            
      messages = recieved.split("\n")
      content = json.dumps(messages)
      response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(content)}\r\n\r\n{content}"      
    except Exception as e:
      print("Chat Server is down, so can't get messages.")  
      
  else:
    content = json.dumps({"error": "Not Logged in."})
    response = f"HTTP/1.1 401 Unauthorized\r\nContent-Type: application/json\r\nContent-Length: {len(content)}\r\n\r\n{content}"
                                                                                                                                                           
  return response


def get_other_files(relative_path):
  content = ''
  response = ''
  filename = relative_path.strip('/')
  content_type = "text/plain"
  
  try:
    suffix = filename.split(".")[-1].lower()

    if suffix in ["jpeg", "png", "jpg"]:
      content_type = f"image/{'jpeg' if suffix == 'jpg' else suffix}"
      
    elif suffix == "html":
      content_type = f"text/{suffix}"
      
    elif suffix == "js":
      content_type = f"application/javascript"
    
    content = getFileContent(filename)

    if content:
      response = f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n{content}"
    else:
      raise Exception
    
  except Exception as e:
      response = "HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n<h1>File Not Found<h1>"
  
  return response

    
def post_login(body_section):
  response = ''
  content = ''

  try:
    username = json.loads(body_section).get("username")
    if username:        
      content = json.dumps({"message": "Login successful!"})
      response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nSet-Cookie: session_id={username}; Path=/; HttpOnly\r\nContent-Length: {len(content)}\r\n\r\n{content}"
    else:
      raise ValueError()
    
  except (json.JSONDecodeError, ValueError) as e:
    content = json.dumps({"error": "Login unsuccessful."})
    response = f"HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\nContent-Length: {len(content)}\r\n\r\n{content}"
    
  return response
    
    
def post_message(username, body_section):
  try:
    newMessage = json.loads(body_section).get("newMsg") 
    
    if username:  
      try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as web_socket:
          web_socket.connect((chat_server_host, chat_server_port))
          newMessage = f"webserver POST:{set_protocol(username, newMessage)}"
          web_socket.sendall(newMessage.encode("UTF-8"))
          message = recieve_message(web_socket)
        
        if message == "DONE":
          content = json.dumps({"message": "Message Sent!"})
          response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(content)}\r\n\r\n{content}" 
      
      except Exception as e:
        print("Chat Server is down, so messages can't be sent.")
        content = json.dumps({"error": "Message Not Sent."})
        response = f"HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\nContent-Length: {len(content)}\r\n\r\n{content}"
    
    else:
      raise ValueError() 
    
  except (json.JSONDecodeError, Exception, ValueError) as e:
    content = json.dumps({"error": "Not logged in."})
    response = f"HTTP/1.1 401 Unauthorized\r\nContent-Type: application/json\r\nContent-Length: {len(content)}\r\n\r\n{content}"
    
  return response


def delete_login(username):
  response = ''
  content = ''
  
  try :
    if username:    
      content = json.dumps({"message": "logout successful!"})
      response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nSet-Cookie: session_id={username}; Path=/; HttpOnly; Expires=Mon, 25 Nov 2002 00:00:00 GMT\r\nContent-Length: {len(content)}\r\n\r\n{content}"
      
    else:
      raise ValueError()
    
  except (Exception, ValueError) as e:
    content = json.dumps({"error": "Not Logged in."})
    response = f"HTTP/1.1 401 Unauthorized\r\nContent-Type: application/json\r\nContent-Length: {len(content)}\r\n\r\n{content}"
    
  return response


def delete_message(relative_path, username):
  relative_path_components = relative_path.split("/")
  components = relative_path_components[3].split("&")
  sent_timestamp = components[0]
  timestamp = sent_timestamp.replace('%20', ' ')
  name = components[1]
  response = ''

  if username and username == name:  
    try:
      with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as web_socket:
        web_socket.connect((chat_server_host, chat_server_port))
        newMessage = f"webserver DELETE:{timestamp}&{name}"
        web_socket.sendall(newMessage.encode("UTF-8"))
        message = recieve_message(web_socket)
        
      if message == "DONE":
        content = json.dumps({"message": "Message Sent!"})
        response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(content)}\r\n\r\n{content}" 
    except:
      print("Chat Server is down, so messages can't be sent.")
      content = json.dumps({"error": "Message could not be deleted."})
      response = f"HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\nContent-Length: {len(content)}\r\n\r\n{content}"
  else:
    content = json.dumps({"error": "Cannot delete message that is not yours."})
    response = f"HTTP/1.1 403 Forbidden\r\nContent-Type: application/json\r\nContent-Length: {len(content)}\r\n\r\n{content}"
  
  return response


def handle_get_request(relative_path, username, body_section):      
  response = ""  
   
  if relative_path == '/':
    response = get_html()
    
  elif relative_path.endswith('.js'):
    response = get_javascript(relative_path)  
  
  elif relative_path.startswith('/api/messages?last='):
    timestamp = relative_path.split("=")[1]
    response = get_messages(username, timestamp)
  
  elif relative_path == '/api/messages':
    response = get_all_messages(username)
    
  else:
    response = get_other_files(relative_path)
    
  return response
    
    
def handle_post_request(relative_path, username, body_section):
  response = ""

  if relative_path == '/api/messages':
    response = post_message(username, body_section)
  
  elif relative_path == '/api/login':   
    response = post_login(body_section)
   
  return response
    
    
def handle_delete_request(relative_path, username):
  response = ""

  if relative_path == '/api/login':    
    response = delete_login(username)
    
  elif relative_path.startswith('/api/messages'):
    response = delete_message(relative_path, username)
    
  return response
   
  
if __name__ == "__main__":
  main()
  
