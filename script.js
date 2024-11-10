const loginSection = document.getElementById("login");
const chatSection = document.getElementById("chat");
const usernameInput = document.getElementById("username");
const messageInput = document.getElementById("newMessage");
const messagesSection = document.getElementById("messages");
const table = document.getElementById("theTable").querySelector("tbody");

let username = '';
let messagesList = [];
let users = [];

function addUser(username, last_seen_timestamp){
  users.push({
    username: username,
    last_seen: last_seen_timestamp
  });
}

function updateLastSeen(username, new_last_seen_timestamp){
  for (let user of users){
    if (user.username == username){
      user.last_seen = new_last_seen_timestamp;
      break;
    }
  }
}
  
function findUser(username){
  for (let user of users){
    if (user.username == username){
      return true;
    }
  }
  return false;
}

function get_last_seen(username){
  for(let user of users){
    if(user.username == username){
      return user.last_seen;
    }
  }
  return 0;
}

function postMessage(){
  var newMsg = messageInput.value.trim();

  if(!newMsg) {
    return
  }

  var oReq = new XMLHttpRequest();
  oReq.open("POST", "/api/messages", true);
  oReq.setRequestHeader("Content-Type", "application/json");
  oReq.withCredentials = true;
  oReq.addEventListener("load", loadedEventCallBack);
  oReq.send(JSON.stringify({newMsg}));
  
  function loadedEventCallBack(){
    if(oReq.status === 200){
      messageInput.value = '';
    }
    else if(oReq.status === 401){ //unauthoried 
        alert("You have to be logged in to send a message.\nPlease login in.");
        logout();
    }
    else{
        alert("Could not send message.\nServer is down, please try again later.");
    }
  };
}

function fetchMessages(){
  const latestTimestamp = get_last_seen(username);

  var oReq = new XMLHttpRequest();
  oReq.open("GET", `/api/messages?last=${latestTimestamp}`, true);
  oReq.setRequestHeader("Content-Type", "application/json");
  oReq.withCredentials = true;
  oReq.addEventListener("load", loadedEventCallBack);
  oReq.send({latestTimestamp});

  function loadedEventCallBack(){
    if(oReq.status === 200){
      var messages = JSON.parse(oReq.responseText);
      
      table.innerHTML = "";
      messagesList = messages;
      
      messages.forEach(msg => {

        if(msg.trim()){
          displayMessage(msg);
        }
      });  
    }
  };
}

function displayMessage(msg){
  const row = document.createElement("tr");
  const timestamp = document.createElement("td");
  const username = document.createElement("td");
  const message = document.createElement("td");
  const deleteCell = document.createElement("td");

  const timestampMatch = msg.match(/\[(.*?)]/);
  const usernameMatch = msg.match(/] (\w+):/);
  const messageMatch = msg.match(/: (.+)$/);

  const timestampText = timestampMatch ? timestampMatch[1] : "";
  const usernameText = usernameMatch ? usernameMatch[1] : "";
  const messageText = messageMatch ? messageMatch[1].trim() : "";

  timestamp.textContent = timestampText; 
  row.appendChild(timestamp);

  username.textContent = usernameText; 
  row.appendChild(username);

  message.textContent = messageText; 
  row.appendChild(message);

  console.log("1: " + usernameInput.value.trim());
  console.log("2: " + usernameText);
  if(usernameText === usernameInput.value.trim()){
    console.log(usernameText === usernameInput.value.trim());
    const deleteButton = document.createElement("button");
    deleteButton.textContent = "Delete";
    deleteButton.onclick = () => deleteMessage(timestampText, usernameText);
    deleteCell.appendChild(deleteButton);
  }

  row.appendChild(deleteCell);

  table.appendChild(row);
}

function deleteMessage(timestamp, username){
  var oReq = new XMLHttpRequest();
  oReq.open("DELETE", `api/messages/${timestamp}&${username}`, true);
  oReq.setRequestHeader("Content-Type", "application/json");
  oReq.withCredentials = true;
  oReq.addEventListener("load", loadedEventCallBack);
  oReq.send();

  function loadedEventCallBack(){
    if(oReq.status === 200){
      fetchMessages();
    }
    else if(oReq.status === 403){
      alert("You can only delete yor own messages.");
    }
    else{
      alert("Failed to delete message.\nPlease try again.")
    }
  }
}

function login(){
  username = usernameInput.value.trim();
  const loginButton = document.getElementById("loginButton");

  if(!username){
    return alert("Please enter a username!");
  }

  if (!findUser(username)){
    addUser(username, 0);
  }

  var oReq = new XMLHttpRequest();
  oReq.open("POST", "/api/login", true);
  oReq.setRequestHeader("Content-Type", "application/json");
  oReq.withCredentials = true;
  oReq.addEventListener("load", loadedEventCallBack);
  oReq.send(JSON.stringify({username}));

  function loadedEventCallBack(){
    loginButton.disabled = true;

    if(oReq.status === 200){
      loginSection.style.display = 'none';
      chatSection.style.display = 'block';

      fetchMessages();
      setInterval(fetchMessages, 1000); //every 1 second
    }
    else{
        alert("Login failed. Please try again later.");
        loginButton.disabled = false;
    }
  };
}

function logout(){
  var oReq = new XMLHttpRequest();
  oReq.open("DELETE", "/api/login", true);
  oReq.setRequestHeader("Content-Type", "application/json");
  oReq.withCredentials = true;
  oReq.addEventListener("load", loadedEventCallBack);
  oReq.send();

  function loadedEventCallBack(){
    loginButton.disabled = false;
    
    if(oReq.status === 200){
      loginSection.style.display = 'block';
      chatSection.style.display = 'none';
      usernameInput.value = '';
      messageInput.innerHTML = '';
      table.innerHTML = '';

      if (messagesList.length > 0){
        const latestTimestamp = messagesList[messagesList.length - 1].match(/\[(.*?)]/);
        updateLastSeen(username, latestTimestamp ? latestTimestamp[1] : 0);
      }
      
      messagesList = [];
      username = '';
    }
    else{
        alert("Logout failed. Please try again later.");
    }
  };
}
