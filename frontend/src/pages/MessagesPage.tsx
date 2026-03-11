import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Contact {
  id: number;
  email: string;
  role: string;
}

interface Message {
  id: number;
  sender_id: number;
  receiver_id: number;
  content: string;
  created_at: string;
  is_read: boolean;
}

const MessagesPage: React.FC = () => {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loadingMessages, setLoadingMessages] = useState(false);

  const token = sessionStorage.getItem('token');
  const currentUserId = Number(sessionStorage.getItem('user_id'));

  useEffect(() => {
    if (!token) return;
    axios
      .get(`${API_URL}/api/messages/contacts`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((res) => setContacts(res.data as Contact[]))
      .catch(() => {});
  }, [token]);

  const loadConversation = (contact: Contact) => {
    if (!token) return;
    setSelectedContact(contact);
    setLoadingMessages(true);
    axios
      .get(`${API_URL}/api/messages/with/${contact.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((res) => setMessages(res.data as Message[]))
      .catch(() => {})
      .finally(() => setLoadingMessages(false));
  };

  const handleSend = () => {
    if (!token || !selectedContact || !newMessage.trim()) return;
    const payload = {
      receiver_id: selectedContact.id,
      content: newMessage.trim(),
    };
    axios
      .post(`${API_URL}/api/messages/send`, payload, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((res) => {
        setMessages((prev) => [...prev, res.data as Message]);
        setNewMessage('');
      })
      .catch((err) => {
        alert(err.response?.data?.detail || 'Failed to send message');
      });
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6 flex gap-6">
      {/* Contacts list */}
      <div className="w-64 bg-gray-800 rounded-xl border border-gray-700 p-4 flex flex-col">
        <h2 className="text-lg font-bold mb-3">Messages</h2>
        <p className="text-xs text-gray-400 mb-3">
          {contacts.length === 0 ? 'No available contacts yet.' : 'Select a person to start chatting.'}
        </p>
        <div className="flex-1 overflow-y-auto space-y-2">
          {contacts.map((c) => (
            <button
              key={c.id}
              onClick={() => loadConversation(c)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm ${
                selectedContact?.id === c.id ? 'bg-blue-600 text-white' : 'bg-gray-700 hover:bg-gray-600'
              }`}
            >
              <div className="font-semibold truncate">{c.email}</div>
              <div className="text-xs text-gray-300 capitalize">{c.role}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Conversation */}
      <div className="flex-1 bg-gray-800 rounded-xl border border-gray-700 flex flex-col">
        <div className="border-b border-gray-700 px-4 py-3">
          <h2 className="text-lg font-bold">
            {selectedContact ? `Chat with ${selectedContact.email}` : 'Select a contact to view messages'}
          </h2>
        </div>
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          {loadingMessages && <div className="text-gray-400 text-sm">Loading messages...</div>}
          {!loadingMessages && selectedContact && messages.length === 0 && (
            <div className="text-gray-500 text-sm">No messages yet. Say hello!</div>
          )}
          {!loadingMessages &&
            selectedContact &&
            messages.map((m) => {
              const isMine = m.sender_id === currentUserId;
              return (
                <div
                  key={m.id}
                  className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                      isMine ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-100'
                    }`}
                  >
                    <div>{m.content}</div>
                    <div className="text-[10px] text-gray-300 mt-1 text-right">
                      {new Date(m.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>
              );
            })}
        </div>
        {selectedContact && (
          <div className="border-t border-gray-700 px-4 py-3 flex gap-3">
            <input
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Type a message..."
              className="flex-1 bg-gray-700 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleSend}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-semibold"
            >
              Send
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessagesPage;

