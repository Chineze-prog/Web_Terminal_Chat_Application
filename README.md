## Description:
Web clients can communicate with terminal clients. They send requests to the web server, which relays those requests to the chat server.

## How to run:
chatClient.py: python chatClient.py <CHAT_SERVER_HOST> <CHAT_SERVER_PORT> <USERNAME>

chatServer.py: python chatServer.py

webserver.py: python webserver.py <CHAT_SERVER_HOST> <CHAT_SERVER_PORT>

The web server's chat server port is different from the one the chat client accepts. You can find which one to use by using the information printed to the terminal when the chat server is run.

screen_scrapper.c: make then ./a2 <WEB_SERVER_HOST> <WEB_SERVER_PORT> <USERNAME> "<MESSAGE>"

The message should be in quotes if it is more than 1 word.
