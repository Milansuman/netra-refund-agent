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

export function AskAssistantSheet() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleAsk() {
    if (!question.trim()) return;
    setLoading(true);
    setAnswer(null);
    setTimeout(() => {
      setAnswer("This is a sample AI answer. Connect your backend here.");
      setLoading(false);
    }, 800);
  }

  return (
    <Sheet>
      {/* This button will sit in your header */}
      <SheetTrigger asChild>
        <Button className="rounded-md bg-yellow-400 px-4 py-1 text-xs font-semibold text-slate-900 hover:bg-yellow-300">
          Ask assistant
        </Button>
      </SheetTrigger>

      <SheetContent side="right" className="flex w-full flex-col gap-4 sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Shopping assistant</SheetTitle>
          <SheetDescription>
            Ask about products, categories, or orders.
          </SheetDescription>
        </SheetHeader>

        <div className="flex-1 space-y-3 overflow-auto pr-2">
          {answer && (
            <div className="rounded-md bg-slate-100 p-3 text-sm">
              <p className="mb-1 font-semibold">Assistant</p>
              <p>{answer}</p>
            </div>
          )}
        </div>

        <div className="space-y-2">
          <Textarea
            rows={3}
            placeholder="Ask: Recommend a laptop under ₹60,000..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          
        </div>
      </SheetContent>
    </Sheet>
  );
}
