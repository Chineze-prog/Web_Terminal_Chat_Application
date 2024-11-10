#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <assert.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netdb.h>

#define BUFFER_SIZE 1024

void handle_error(const char *msg);
void receive_response(int client_socket, char *response);
void send_request(int client_socket, const char *request);
void get_request_without_cookie(int client_socket, const char *server_host);
void post_request_without_cookie(int client_socket, const char *server_host, const char *message);
void fetch_messages(int client_socket, const char *server_host, const char *username, const char *expected_message, bool check_for_msg);
void post_messages(int client_socket, const char *server_host, const char *username, const char *message);
int create_and_connect_socket(struct sockaddr_in *server_addr, const char *server_host, const char *server_port);
void resolve_host(const char *server_host, struct sockaddr_in *server_addr, const char *port);


int main(int args, char *argv[]){
  if(args < 5){
    fprintf(stderr, "Usage: %s <server_host> <server_port> <username> <message>\n", argv[0]);
    exit(EXIT_FAILURE);
  }

  const char *server_host = argv[1];
  const char *server_port = argv[2];
  const char *username = argv[3];
  const char *message = argv[4];

  int client_socket;
  struct sockaddr_in server_addr;
 
  resolve_host(server_host, &server_addr, server_port);
 
  client_socket = create_and_connect_socket(&server_addr, server_host, server_port);

  fetch_messages(client_socket, server_host, username, message, false);
  printf("The Message was not found.\n");
  close(client_socket);

  client_socket = create_and_connect_socket(&server_addr, server_host, server_port);

  post_messages(client_socket, server_host, username, message);
  printf("The Message was posted.\n");
  close(client_socket);

  client_socket = create_and_connect_socket(&server_addr, server_host, server_port);

  fetch_messages(client_socket, server_host, username, message, true);
  printf("The Message was found.\n");
  close(client_socket);
 
  client_socket = create_and_connect_socket(&server_addr, server_host, server_port);

  get_request_without_cookie(client_socket, server_host);
  printf("The Request was not accepted.\n");
  close(client_socket);

  client_socket = create_and_connect_socket(&server_addr, server_host, server_port);

  post_request_without_cookie(client_socket, server_host, message);
  printf("The Request was not accepted.\n");
  close(client_socket);

  printf("All tests passed sucessfully!!.\n");
 
  return 0;
}


int create_and_connect_socket(struct sockaddr_in *server_addr, const char *server_host, const char *server_port){
  int client_socket = socket(AF_INET, SOCK_STREAM, 0);

  if (client_socket < 0){
    handle_error("Unable to create socket\n");
  }

  printf("Socket created successfully\n");

  //send connection:
  if(connect(client_socket, (struct sockaddr *)server_addr, sizeof(*server_addr)) < 0){
    handle_error("Unable to connect to server\n");
  }

  printf("Connected with server on host %s on port %s  successfully\n", server_host, server_port);

  return client_socket;
}


void resolve_host(const char *server_host, struct sockaddr_in *server_addr, const char *port){
  struct addrinfo hints, *server_info;

  memset(&hints, 0, sizeof(hints));
  hints.ai_family = AF_INET;
  hints.ai_socktype = SOCK_STREAM;

  int status = getaddrinfo(server_host, port, &hints, &server_info);

  if (status != 0) {
    handle_error("getaddrinfo failed.\n");
  }

  *server_addr = *(struct sockaddr_in *)server_info->ai_addr;
  freeaddrinfo(server_info);
}
    

void get_request_without_cookie(int client_socket, const char *server_host){
  char request[BUFFER_SIZE], response[BUFFER_SIZE];

  snprintf(request, sizeof(request),
        "GET /api/messages HTTP/1.1\r\n"
        "Host: %s\r\n\r\n",
        server_host);

  send_request(client_socket, request);
  receive_response(client_socket, response);

  assert(strstr(response, "401 Unauthorized") != NULL);
}


void post_request_without_cookie(int client_socket, const char *server_host, const char *message){
  char request[BUFFER_SIZE], response[BUFFER_SIZE], body[BUFFER_SIZE];

  snprintf(body, sizeof(body), "{\"newMsg\": \"%s\"}", message);

  snprintf(request, sizeof(request),
        "POST /api/messages HTTP/1.1\r\n"
        "Host: %s\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: %lu\r\n\r\n%s",
        server_host, strlen(body), body);

  send_request(client_socket, request);
  receive_response(client_socket, response);

  assert(strstr(response, "401 Unauthorized") != NULL);
}


void fetch_messages(int client_socket, const char *server_host, const char *username, const char *expected_message, bool check_for_msg){
  char request[BUFFER_SIZE], response[BUFFER_SIZE];

  snprintf(request, sizeof(request),
        "GET /api/messages HTTP/1.1\r\n"
        "Host: %s\r\n"
        "Cookie: session_id=%s\r\n\r\n",
        server_host, username);

  send_request(client_socket, request);
  receive_response(client_socket, response);
  
  if(check_for_msg){
    assert(strstr(response, expected_message) != NULL);
  }
  else{
    assert(strstr(response, expected_message) == NULL); 
  }
}


void post_messages(int client_socket, const char *server_host, const char *username, const char *message){
  char request[BUFFER_SIZE], response[BUFFER_SIZE], body[BUFFER_SIZE];
 
  memset(response, 0, BUFFER_SIZE);

  snprintf(body, sizeof(body), "{\"newMsg\": \"%s\"}", message);

  snprintf(request, sizeof(request),
        "POST /api/messages HTTP/1.1\r\n"
        "Host: %s\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: %lu\r\n"
        "Cookie: session_id=%s\r\n\r\n%s",
        server_host, strlen(body), username, body);

  send_request(client_socket, request);
  receive_response(client_socket, response);
  
  assert(strstr(response, "Message Sent!") != NULL);
}


void send_request(int client_socket, const char *request){
  if(send(client_socket, request, strlen(request), 0) < 0){
    handle_error("Unable to send request");
  }
}


void receive_response(int client_socket, char *response){
  memset(response, 0, BUFFER_SIZE);

  int bytes_received = recv(client_socket, response, BUFFER_SIZE - 1, 0);

  if(bytes_received < 0){
    handle_error("Unable to receive message");
  }

  response[bytes_received] = '\0';
}


void handle_error(const char *msg){
  perror(msg);
  exit(EXIT_FAILURE);
}

