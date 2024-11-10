import sqlite3

LOG_LIMIT = 30

def initialize_db():
  connection = sqlite3.connect("ChatServerdb.db")
  cursor = connection.cursor()

  cursor.execute("""
                 CREATE TABLE IF NOT EXISTS Messages (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   timestamp DATETIME NOT NULL,
                   sender TEXT NOT NULL,
                   message TEXT NOT NULL
                 )""")

  cursor.execute("""
                 CREATE TABLE IF NOT EXISTS Clients (
                   username TEXT PRIMARY KEY,
                   sentMessagesNum INTEGER,  
                   lastMessageSeenId INTEGER,
                   connectionStatus TEXT NOT NULL,
                   FOREIGN KEY (lastMessageSeenId) REFERENCES Messages(id)
                 )""")

  return connection, cursor


# add a new client to the database and flag them as active, 
# if the username already exists, flag the user as active
def add_client(cursor, connection, username):
  cursor.execute("""INSERT INTO Clients (username, sentMessagesNum, connectionStatus) 
                 VALUES (?, ?, ?) ON CONFLICT (username) DO UPDATE 
                 SET connectionStatus = 'active'""", (username, 0, 'active'))

  connection.commit()


def delete_client(cursor, connection, username):
  cursor.execute("""DELETE FROM Clients WHERE username = ?""", (username,))

  connection.commit()


# check if the client already exists in the database
def find_client(cursor, username):
  return cursor.execute("""SELECT * FROM Clients WHERE username = ?
                         """, (username,)).fetchone()


# change the clients staus depending on if they are connected or not
def update_connection_status(cursor, connection, username, new_status):
  cursor.execute("""UPDATE Clients SET connectionStatus = ? WHERE username = ?
                  """, (new_status, username))

  connection.commit()


# updates the client's last seen message to the currently sent message
def update_client_last_seen_message(cursor, connection, message_id):
  cursor.execute("""UPDATE Clients SET lastMessageSeenId = ?  
                  WHERE connectionStatus = 'active'""", (message_id,))

  connection.commit()


# updates the number of messages the client has sent
def update_messages_sent_number(cursor, connection, username):
  number_of_messages_sent = cursor.execute("""
                            UPDATE Clients SET sentMessagesNum = sentMessagesNum + 1
                            WHERE username = ?""", (username,))

  connection.commit()


def add_new_message(cursor, connection, timestamp, sender, message):
  cursor.execute("""INSERT INTO Messages (timestamp, sender, message)
                 VALUES (?, ?, ?)""", (timestamp, sender, message))

  connection.commit()


def get_last_seen_msg_id(cursor, username):
  return cursor.execute("""SELECT lastMessageSeenId FROM Clients WHERE username = ?
                          """, (username,)).fetchone()


def get_last_30_msg_before_cutoff(cursor, last_seen_message_id):
    return cursor.execute("""SELECT timestamp, sender, message 
                        FROM Messages WHERE id <= ? ORDER BY id DESC LIMIT ?
                        """, (last_seen_message_id, LOG_LIMIT)).fetchall()


def get_msg_after_cutoff(cursor, last_seen_message_id):
  return cursor.execute("""SELECT timestamp, sender, message FROM Messages 
                    WHERE id > ?""", (last_seen_message_id,)).fetchall()


def get_last_few_msg(cursor, cutoff_value):
  return cursor.execute("""SELECT timestamp, sender, message FROM Messages
                        WHERE timestamp <= ? ORDER BY id DESC LIMIT ?
                        """, (cutoff_value, LOG_LIMIT)).fetchall()


def get_msg_for_web_client(cursor, timestamp):
  return cursor.execute("""SELECT timestamp, sender, message FROM Messages
                      WHERE timestamp >= ? ORDER BY id DESC 
                      """, (timestamp,)).fetchall()


def get_last_30_msg(cursor):
  return cursor.execute("""SELECT timestamp, sender, message FROM Messages
                      ORDER BY id DESC LIMIT ?""", (LOG_LIMIT,)).fetchall()


def latest_msg_id(cursor):
  return cursor.execute("SELECT MAX(id) FROM Messages").fetchone()


def get_all_msg(cursor):
   return cursor.execute("SELECT timestamp, sender, message  FROM Messages").fetchall()

def delete_msg(cursor, connection, timestamp, username):
  cursor.execute("DELETE FROM Messages WHERE timestamp = ? AND sender = ?", (timestamp,username))
  connection.commit() 
