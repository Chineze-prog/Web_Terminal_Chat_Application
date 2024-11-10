class User:
  def __init__(self, client_socket):
    self.client_socket = client_socket
    self.username = "Unknown"

  def changeUsername(self, newUsername):
    self.username = newUsername
