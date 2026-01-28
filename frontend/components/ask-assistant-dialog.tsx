"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

export function AskAssistantDialog() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  async function sendMessage() {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    // TODO: Replace with your real /api/assistant
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          "This is a sample AI response. I can help you find products, compare prices, or answer shopping questions. Connect your backend API here!",
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setLoading(false);
    }, 3000);
  }

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button className="rounded-md bg-yellow-400 px-4 py-1 text-xs font-semibold text-slate-900 hover:bg-yellow-300">
          Ask assistant
        </Button>
      </DialogTrigger>

      <DialogContent className="sm:max-w-[600px] bg-white/95 backdrop-blur-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <Avatar className="h-8 w-8">
              <AvatarImage src="https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=64&q=80" />
              <AvatarFallback>AI</AvatarFallback>
            </Avatar>
            <span>Jenga AI</span>
          </DialogTitle>
          <DialogDescription>Chat about products, prices, or recommendations.</DialogDescription>
        </DialogHeader>

        <ScrollArea className="h-[400px] w-full rounded-md border p-4">
          <div ref={scrollRef} className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[70%] rounded-lg p-3 ${
                    message.role === "user"
                      ? "bg-yellow-400 text-slate-900"
                      : "bg-slate-100 text-slate-900"
                  }`}
                >
                  <p className="text-sm">{message.content}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="max-w-[70%] rounded-lg bg-slate-100 p-3">
                  <p className="text-sm">Assistant is typing...</p>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="mt-4 flex gap-2">
          <Textarea
            rows={2}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about products, recommendations, or orders..."
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
          />
          <Button onClick={sendMessage} disabled={loading || !input.trim()}>
            Send
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setMessages([]);
              setInput("");
            }}
          >
            Clear
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
