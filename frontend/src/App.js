import React, { useState, useEffect, useRef } from "react";
import "./App.css";

function App() {
  const [clientId] = useState(Math.floor(new Date().getTime() / 1000));
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState("");
  const websocket = useRef(null);

  useEffect(() => {
    const url = `ws://localhost:8000/ws/${clientId}`;
    const ws = new WebSocket(url);
    websocket.current = ws;

    ws.onopen = () => {
      ws.send("Connect");
    };

    ws.onmessage = (e) => {
      const newMessage = JSON.parse(e.data);
      setMessages((prevMessages) => [...prevMessages, newMessage]);
    };

    return () => {
      ws.close();
    };
  }, [clientId]);

  const sendMessage = () => {
    if (websocket.current && message) {
      websocket.current.send(message);
      setMessage("");
    }
  };

  return (
    <div className="container">
      <h1>Chat</h1>
      <h2>Your client id: {clientId}</h2>
      <div className="chat-container">
        <div className="chat">
          {messages.map((value, index) => (
            <div key={index} className={value.clientId === clientId ? "my-message-container" : "another-message-container"}>
              <div className={value.clientId === clientId ? "my-message" : "another-message"}>
                <p className="client">client id: {value.clientId}</p>
                <p className="date">Date: {value.time}</p>
                <p className="message">{value.message}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="input-chat-container">
          <input
            className="input-chat"
            type="text"
            placeholder="Chat message ..."
            onChange={(e) => setMessage(e.target.value)}
            value={message}
          />
          <button className="submit-chat" onClick={sendMessage}>
            Send
          </button> 
        </div>
      </div>
    </div>
  );
}

export default App;
