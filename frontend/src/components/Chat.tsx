"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useWebSocket, WSMessage } from "@/hooks/useWebSocket";
import { endpoints, fetchProviders } from "@/lib/api";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { AgentStatus } from "./AgentStatus";
import { ProviderSelector } from "./ProviderSelector";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [statuses, setStatuses] = useState<string[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [providers, setProviders] = useState<string[]>([]);
  const [currentProvider, setCurrentProvider] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent, statuses]);

  // Fetch providers on mount
  useEffect(() => {
    fetchProviders().then((data) => {
      setProviders(data.providers);
      setCurrentProvider(data.default);
    });
  }, []);

  const handleWSMessage = useCallback(
    (msg: WSMessage) => {
      switch (msg.type) {
        case "status":
          if (msg.message) {
            setStatuses((prev) => [...prev, msg.message!]);
          }
          break;
        case "token":
          if (msg.content) {
            setStreamingContent((prev) => prev + msg.content);
          }
          break;
        case "done":
          if (streamingContent || msg.content) {
            setMessages((prev) => [
              ...prev,
              { role: "assistant", content: streamingContent || msg.content || "" },
            ]);
          }
          setStreamingContent("");
          setStatuses([]);
          setIsStreaming(false);
          break;
        case "error":
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: `Error: ${msg.message}` },
          ]);
          setStreamingContent("");
          setStatuses([]);
          setIsStreaming(false);
          break;
      }
    },
    [streamingContent]
  );

  const { isConnected, send } = useWebSocket({
    url: endpoints.wsChat,
    onMessage: handleWSMessage,
  });

  const handleSend = useCallback(
    (message: string) => {
      // Add user message
      setMessages((prev) => [...prev, { role: "user", content: message }]);
      setIsStreaming(true);
      setStreamingContent("");
      setStatuses([]);

      // Send via WebSocket
      send({
        type: "chat",
        message,
        session_id: "default",
      });
    },
    [send]
  );

  const handleReset = useCallback(() => {
    setMessages([]);
    setStreamingContent("");
    setStatuses([]);
    setIsStreaming(false);
    send({ type: "reset", session_id: "default" });
  }, [send]);

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b dark:border-gray-700">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
            Agentic RAG Assistant
          </h1>
          <span
            className={`inline-block w-2 h-2 rounded-full ${
              isConnected ? "bg-green-500" : "bg-red-500"
            }`}
          />
        </div>
        <div className="flex items-center gap-3">
          {providers.length > 0 && (
            <ProviderSelector
              providers={providers}
              current={currentProvider}
              onChange={setCurrentProvider}
            />
          )}
          <button
            onClick={handleReset}
            className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                       text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800
                       transition-colors"
          >
            Reset
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 && !isStreaming && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-400">
              <div className="text-4xl mb-3">AI</div>
              <p className="text-sm">
                Ask me anything. I can search documents, calculate, and search
                the web.
              </p>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatMessage key={i} role={msg.role} content={msg.content} />
        ))}

        {isStreaming && (
          <>
            <AgentStatus statuses={statuses} />
            <ChatMessage
              role="assistant"
              content={streamingContent}
              isStreaming={true}
            />
          </>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={isStreaming || !isConnected} />
    </div>
  );
}
