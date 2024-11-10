CC = clang
CFLAGS = -Wall
TARGET = a2
FILE = screen_scrapper.c

.PHONY: all clean run

all: $(TARGET)

$(TARGET): $(FILE)
	$(CC) $(CFLAGS) -o $(TARGET) $(FILE)

run: $(TARGET)
	@echo "Usage: make run ARGS = \"<server_host> <server_port> <username> <message>\""
	./$(TARGET) $(ARGS)

clean:
	rm $(TARGET)
