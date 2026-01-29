"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Sparkles, MessageSquare } from "lucide-react";

export function AskAssistantSheet() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleAsk() {
    if (!question.trim()) return;
    setLoading(true);
    setAnswer(null);
    setTimeout(() => {
      setAnswer("I see you're asking about returns. You can process a return for any item within 30 days of purchase through your Orders page.");
      setLoading(false);
    }, 800);
  }

  return (
    <Sheet>
      {/* This button will sit in your header */}
      <SheetTrigger asChild>
        <Button className="rounded-full bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 shadow-sm flex items-center gap-2">
           <Sparkles className="h-3 w-3" />
           Velora Assistant
        </Button>
      </SheetTrigger>

      <SheetContent side="right" className="flex w-full flex-col gap-0 sm:max-w-md p-0 border-l border-neutral-200">
        <SheetHeader className="px-6 py-5 border-b border-neutral-100 bg-neutral-50/50">
          <SheetTitle className="flex items-center gap-2 text-lg text-indigo-900">
             <div className="p-2 bg-indigo-100 rounded-lg">
                <Sparkles className="h-5 w-5 text-indigo-600" />
             </div>
             Velora Assistant
          </SheetTitle>
          <SheetDescription className="text-neutral-500">
            Ask about products, refunds, or track your orders instantly.
          </SheetDescription>
        </SheetHeader>

        <div className="flex-1 space-y-4 overflow-auto p-6 bg-white">
          {answer ? (
            <div className="rounded-2xl rounded-tl-none bg-indigo-50 p-4 text-sm text-indigo-900 leading-relaxed border border-indigo-100">
              <div className="flex items-center gap-2 mb-2">
                 <span className="text-xs font-bold text-indigo-700 uppercase tracking-wide">Velora AI</span>
              </div>
              <p>{answer}</p>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center p-8 opacity-40">
                <MessageSquare className="h-12 w-12 mb-4" />
                <p className="text-sm font-medium">No messages yet</p>
                <p className="text-xs">Ask a question to get started</p>
            </div>
          )}
        </div>

        <div className="p-6 bg-neutral-50 border-t border-neutral-100 space-y-3">
          <Textarea
            rows={3}
            placeholder="Ask: What is the status of my refund?..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="w-full rounded-xl border-neutral-200 bg-white focus:ring-indigo-500/20 resize-none text-sm"
          />
           <Button 
            onClick={handleAsk} 
            disabled={loading || !question.trim()}
            className="w-full rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm py-5"
           >
            {loading ? "Thinking..." : "Ask Agent"}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
