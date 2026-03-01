var inner = document.getElementById("inner");
var chatContainer = document.getElementById("chat-container");
var userInput = document.getElementById("user-input");
var sendBtn = document.getElementById("send-btn");
var welcomeGone = false;

// Boutons de suggestion
document.querySelectorAll(".chip").forEach(function(btn) {
  btn.addEventListener("click", function() {
    userInput.value = btn.getAttribute("data-q");
    sendMessage();
  });
});

// Bouton envoyer
sendBtn.addEventListener("click", sendMessage);

// Touche Entree
userInput.addEventListener("keydown", function(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// Auto-resize
userInput.addEventListener("input", function() {
  userInput.style.height = "auto";
  userInput.style.height = Math.min(userInput.scrollHeight, 110) + "px";
});

function removeWelcome() {
  if (!welcomeGone) {
    var w = document.getElementById("welcome");
    if (w) { w.remove(); }
    welcomeGone = true;
  }
}

function makeBotAvatar() {
  var av = document.createElement("div");
  av.className = "av";
  av.innerHTML = '<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/></svg>';
  return av;
}

function makeUserAvatar() {
  var av = document.createElement("div");
  av.className = "av";
  av.innerHTML = '<svg viewBox="0 0 24 24"><path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/></svg>';
  return av;
}

function addMessage(text, isUser) {
  removeWelcome();

  var row = document.createElement("div");
  row.className = "msg " + (isUser ? "user" : "bot");

  var bubble = document.createElement("div");
  bubble.className = "bbl";

  if (isUser) {
    bubble.textContent = text;
    row.appendChild(makeUserAvatar());
    row.appendChild(bubble);
  } else {
    bubble.innerHTML = text.replace(/\n/g, "<br>");
    row.appendChild(makeBotAvatar());
    row.appendChild(bubble);
  }

  inner.appendChild(row);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function showTyping() {
  removeWelcome();
  var row = document.createElement("div");
  row.className = "msg bot";
  row.id = "typing";

  var bubble = document.createElement("div");
  bubble.className = "bbl";
  bubble.innerHTML = '<div class="dots"><span></span><span></span><span></span></div>';

  row.appendChild(makeBotAvatar());
  row.appendChild(bubble);
  inner.appendChild(row);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function hideTyping() {
  var el = document.getElementById("typing");
  if (el) { el.remove(); }
}

function sendMessage() {
  var text = userInput.value.trim();
  if (!text) { return; }

  addMessage(text, true);
  userInput.value = "";
  userInput.style.height = "auto";
  sendBtn.disabled = true;
  showTyping();

  fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text })
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    hideTyping();
    addMessage(data.response || "Erreur.", false);
  })
  .catch(function() {
    hideTyping();
    addMessage("Erreur de connexion au serveur.", false);
  })
  .finally(function() {
    sendBtn.disabled = false;
    userInput.focus();
  });
}
