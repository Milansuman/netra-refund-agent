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
import { Send, Sparkles, MessageSquare, Trash2 } from "lucide-react";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

const SUGGESTED_QUESTIONS = [
  "Check my refund status",
  "Return policy for electronics",
  "I received a damaged item",
];

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

  async function sendMessage(text: string = input) {
    if (!text.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    // TODO: Connect to backend
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          "I can help you with that refund request. Could you please provide your Order ID? It usually starts with 'VEL-'.",
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setLoading(false);
    }, 1500);
  }

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button className="rounded-full bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 shadow-sm flex items-center gap-2">
          <Sparkles className="h-3 w-3" />
          Velora Support
        </Button>
      </DialogTrigger>

      <DialogContent className="sm:max-w-[500px] p-0 gap-0 overflow-hidden border-neutral-200">
        <div className="bg-neutral-50 px-6 py-4 border-b border-neutral-100 flex items-center gap-4">
            <div className="relative">
                <Avatar className="h-10 w-10 border-2 border-white shadow-sm">
                <AvatarImage src="https://images.unsplash.com/photo-1535378433864-ed9c2cb781cc?auto=format&fit=crop&w=64&q=80" />
                <AvatarFallback className="bg-indigo-100 text-indigo-700">AI</AvatarFallback>
                </Avatar>
                <span className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full bg-emerald-500 ring-2 ring-white"></span>
            </div>
          <div>
            <DialogTitle className="text-base font-semibold text-neutral-900">Velora Support Agent</DialogTitle>
            <DialogDescription className="text-xs text-neutral-500">Always online • Ask about refunds & returns</DialogDescription>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="ml-auto text-neutral-400 hover:text-red-500 hover:bg-red-50"
            onClick={() => setMessages([])}
            title="Clear Chat"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>

        <ScrollArea className="h-[400px] w-full bg-white p-6">
          <div ref={scrollRef} className="space-y-6">
             {messages.length === 0 && (
                <div className="text-center py-8">
                    <div className="mx-auto h-12 w-12 bg-indigo-50 rounded-xl flex items-center justify-center mb-3">
                        <MessageSquare className="h-6 w-6 text-indigo-600" />
                    </div>
                    <h3 className="text-sm font-medium text-neutral-900">How can we help?</h3>
                    <p className="text-xs text-neutral-500 mt-1 max-w-[200px] mx-auto">Track refunds, initiate returns, or get product support instantly.</p>
                </div>
             )}
            
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    message.role === "user"
                      ? "bg-indigo-600 text-white rounded-br-none"
                      : "bg-neutral-100 text-neutral-800 rounded-bl-none"
                  }`}
                >
                  <p>{message.content}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="rounded-2xl rounded-bl-none bg-neutral-100 px-4 py-3">
                    <div className="flex gap-1">
                        <span className="h-1.5 w-1.5 rounded-full bg-neutral-400 animate-bounce [animation-delay:-0.3s]"></span>
                        <span className="h-1.5 w-1.5 rounded-full bg-neutral-400 animate-bounce [animation-delay:-0.15s]"></span>
                        <span className="h-1.5 w-1.5 rounded-full bg-neutral-400 animate-bounce"></span>
                    </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Suggested Questions */}
        {messages.length === 0 && (
            <div className="px-6 pb-2">
                <p className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wider mb-2">Suggested</p>
                <div className="flex flex-wrap gap-2">
                    {SUGGESTED_QUESTIONS.map((q) => (
                        <button 
                            key={q} 
                            onClick={() => sendMessage(q)}
                            className="text-xs bg-neutral-50 border border-neutral-200 hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700 text-neutral-600 px-3 py-1.5 rounded-full transition-colors"
                        >
                            {q}
                        </button>
                    ))}
                </div>
            </div>
        )}

        <div className="p-4 bg-white border-t border-neutral-100">
          <div className="relative">
            <Textarea
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message..."
                className="min-h-[48px] pr-12 resize-none rounded-xl border-neutral-200 bg-neutral-50 focus:bg-white focus:ring-indigo-500/20 transition-all py-3"
                onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
                }}
            />
            <Button 
                onClick={() => sendMessage()} 
                disabled={loading || !input.trim()}
                className="absolute right-2 top-1.5 h-9 w-9 p-0 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white disabled:bg-neutral-200 disabled:text-neutral-400 shadow-sm"
            >
                <Send className="h-4 w-4" />
                <span className="sr-only">Send</span>
            </Button>
          </div>
          <div className="mt-2 text-center">
            <p className="text-[10px] text-neutral-400">Powered by Velora Intelligence</p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
