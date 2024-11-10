
## How to run:
chatClient.py: python chatClient.py <CHAT_SERVER_HOST> <CHAT_SERVER_PORT> <USERNAME>

chatServer.py: python chatServer.py

webserver.py: python webserver.py <CHAT_SERVER_HOST> <CHAT_SERVER_PORT>

For the webserver, the chat server port it accepts is different from the one the chat client accepts, you can find which one to use printed to the terminat when the chat server is run.

screen_scrapper.c: make then ./a2 <WEB_SERVER_HOST> <WEB_SERVER_PORT> <USERNAME> "<MESSAGE>"

The message should be in quotes if its more than 1 word.
