"use client";

import { FormEvent, useState } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const msg = input.trim();
    if (!msg || disabled) return;
    onSend(msg);
    setInput("");
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 p-4 border-t dark:border-gray-700">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="输入你的问题..."
        disabled={disabled}
        className="flex-1 px-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600
                   bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                   focus:outline-none focus:ring-2 focus:ring-blue-500
                   disabled:opacity-50 disabled:cursor-not-allowed
                   placeholder:text-gray-400"
      />
      <button
        type="submit"
        disabled={disabled || !input.trim()}
        className="px-5 py-2.5 rounded-xl bg-blue-600 text-white font-medium
                   hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500
                   disabled:opacity-50 disabled:cursor-not-allowed
                   transition-colors"
      >
        发送
      </button>
    </form>
  );
}
