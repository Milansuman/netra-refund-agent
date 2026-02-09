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
import { Send, MessageSquare, Trash2, Sparkles, Bot, Package, CreditCard, ShoppingBag } from "lucide-react";
import ReactMarkdown from "react-markdown";
import "@/styles/markdown.css";

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================
// 
// These TypeScript types define the shape of our data.
// Think of them as "contracts" - if data doesn't match, TypeScript warns us.
// =============================================================================

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  orders?: Order[];  // For displaying order list cards
  productData?: ProductData;  // For displaying single order product details
};

// Order data structure (matches what the backend sends)
type OrderItem = {
  id: number;
  name: string;
  quantity: number;
  price: number;
};

type Order = {
  id: number;
  status: string;
  paid_amount: number;
  payment_method: string;
  items: OrderItem[];
};

// =============================================================================
// HELPER FUNCTION: Parse Order Data from Message
// =============================================================================
// 
// The backend sends order data in a special format:
// <!--ORDER_DATA:[{...}, {...}]-->
// 
// This function extracts that JSON and returns:
// 1. The order data (for rendering cards)
// 2. The clean message (without the marker)
// =============================================================================

function parseOrderData(content: string): { orders: Order[] | null; cleanContent: string } {
  // Using [\s\S]*? instead of .*? with /s flag for older JS compatibility
  // [\s\S] matches any character including newlines
  const orderDataRegex = /<!--ORDER_DATA:([\s\S]*?)-->/;
  const match = content.match(orderDataRegex);

  if (match) {
    try {
      const orders = JSON.parse(match[1]) as Order[];
      // Remove the ORDER_DATA marker from the content
      const cleanContent = content.replace(orderDataRegex, "").trim();
      return { orders, cleanContent };
    } catch {
      return { orders: null, cleanContent: content };
    }
  }

  return { orders: null, cleanContent: content };
}

// =============================================================================
// PRODUCT DATA TYPES AND PARSER
// =============================================================================
// 
// Similar to ORDER_DATA, but for detailed product information from a single order.
// Marker format: <!--PRODUCT_DATA:{...}-->
// =============================================================================

type ProductItem = {
  id: number;
  name: string;
  description: string;
  quantity: number;
  unit_price: number;
  tax_percent: number;
  discounts: string[];
};

type ProductData = {
  order_id: number;
  status: string;
  payment_method: string;
  total_paid: number;
  items: ProductItem[];
};

function parseProductData(content: string): { productData: ProductData | null; cleanContent: string } {
  const productDataRegex = /<!--PRODUCT_DATA:([\s\S]*?)-->/;
  const match = content.match(productDataRegex);

  if (match) {
    try {
      const productData = JSON.parse(match[1]) as ProductData;
      const cleanContent = content.replace(productDataRegex, "").trim();
      return { productData, cleanContent };
    } catch {
      return { productData: null, cleanContent: content };
    }
  }

  return { productData: null, cleanContent: content };
}

// =============================================================================
// ORDER CARD COMPONENT
// =============================================================================
// 
// This component renders a single order as a beautiful card.
// It receives an Order object and displays it with nice styling.
// =============================================================================

function OrderCard({ order }: { order: Order }) {
  // Status color mapping for dark theme
  const statusColors: Record<string, string> = {
    pending: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
    completed: "bg-green-500/10 text-green-400 border-green-500/20",
    shipped: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    cancelled: "bg-red-500/10 text-red-400 border-red-500/20",
    delivered: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  };

  const status = order?.status ?? "Unknown";
  const statusClass = statusColors[status.toLowerCase()] || "bg-neutral-800 text-neutral-400 border-neutral-700";

  return (
    <div className="bg-neutral-900/50 backdrop-blur-sm rounded-xl border border-white/5 shadow-inner overflow-hidden hover:border-indigo-500/30 transition-all group">
      {/* Card Header */}
      <div className="bg-white/5 px-4 py-3 border-b border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Package className="h-4 w-4 text-indigo-400" />
            <span className="font-medium text-neutral-200">Order #{order?.id ?? "N/A"}</span>
          </div>
          <span className={`px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wider font-semibold border ${statusClass}`}>
            {status}
          </span>
        </div>
      </div>

      {/* Card Body - Items List */}
      <div className="p-4 space-y-3">
        {(order?.items ?? []).map((item, idx) => (
          <div key={item?.id ?? idx} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-lg bg-neutral-800 flex items-center justify-center shrink-0">
                <ShoppingBag className="h-4 w-4 text-neutral-500" />
              </div>
              <div>
                <span className="block text-neutral-300 font-medium">{item?.name ?? "Unknown Item"}</span>
                <span className="text-xs text-neutral-500">Qty: {item?.quantity ?? 0}</span>
              </div>
            </div>
            <span className="text-neutral-400 font-mono">₹{(item?.price ?? 0).toFixed(2)}</span>
          </div>
        ))}
      </div>

      {/* Card Footer */}
      <div className="bg-white/5 px-4 py-3 border-t border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-neutral-500">
            <CreditCard className="h-3.5 w-3.5" />
            <span>{order?.payment_method ?? "Unknown"}</span>
          </div>
          <div className="text-right">
            <span className="text-xs text-neutral-500 mr-2">Total</span>
            <span className="font-semibold text-indigo-400">₹{(order?.paid_amount ?? 0).toFixed(2)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// PRODUCT CARD COMPONENT
// =============================================================================
// 
// Displays detailed product information for a single order.
// Shows description, discounts, tax, etc.
// =============================================================================

function ProductCard({ data }: { data: ProductData }) {
  const statusColors: Record<string, string> = {
    pending: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
    processing: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    shipped: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
    delivered: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    cancelled: "bg-red-500/10 text-red-400 border-red-500/20",
  };

  const status = data?.status ?? "Unknown";
  const statusClass = statusColors[status.toLowerCase()] || "bg-neutral-800 text-neutral-400 border-neutral-700";

  return (
    <div className="bg-neutral-900/50 backdrop-blur-sm rounded-xl border border-white/10 shadow-lg overflow-hidden ring-1 ring-white/5">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 px-4 py-3 border-b border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Package className="h-4 w-4 text-purple-400" />
            <span className="font-medium text-neutral-200">Order #{data?.order_id ?? "N/A"}</span>
          </div>
          <span className={`px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wider font-semibold border ${statusClass}`}>
            {status}
          </span>
        </div>
      </div>

      {/* Products List */}
      <div className="p-4 space-y-4">
        {(data?.items ?? []).map((item, idx) => (
          <div key={item?.id ?? idx} className="border-b border-white/5 pb-4 last:border-0 last:pb-0">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <div className="h-6 w-6 rounded bg-neutral-800 flex items-center justify-center">
                    <ShoppingBag className="h-3 w-3 text-purple-400" />
                  </div>
                  <span className="font-medium text-white">{item?.name ?? "Unknown Item"}</span>
                </div>
                <p className="text-xs text-neutral-500 ml-8 mb-2 leading-relaxed">{item?.description ?? "No description"}</p>

                <div className="flex flex-wrap items-center gap-3 ml-8 text-xs text-neutral-500">
                  <div className="flex items-center gap-1 bg-neutral-800/50 px-2 py-1 rounded">
                    <span>Qty:</span>
                    <span className="text-neutral-300">{item?.quantity ?? 0}</span>
                  </div>
                  <div className="flex items-center gap-1 bg-neutral-800/50 px-2 py-1 rounded">
                    <span>Tax:</span>
                    <span className="text-neutral-300">{item?.tax_percent ?? 0}%</span>
                  </div>
                  {(item?.discounts ?? []).length > 0 && (
                    <span className="text-green-400 bg-green-500/10 px-2 py-1 rounded border border-green-500/10">
                      🏷️ {(item?.discounts ?? []).join(", ")}
                    </span>
                  )}
                </div>
              </div>
              <div className="text-right">
                <span className="block font-semibold text-white">₹{(item?.unit_price ?? 0).toFixed(2)}</span>
                <span className="text-[10px] text-neutral-600">per unit</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="bg-white/5 px-4 py-3 border-t border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-neutral-500">
            <CreditCard className="h-3.5 w-3.5" />
            <span>{data?.payment_method ?? "Unknown"}</span>
          </div>
          <div className="text-right">
            <span className="text-xs text-neutral-500 mr-2">Total Paid</span>
            <span className="font-bold text-purple-400 text-lg">₹{(data?.total_paid ?? 0).toFixed(2)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export function AskAssistantDialog() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Preserve chat history when dialog closes
  const handleOpenChange = (isOpen: boolean) => {
    setOpen(isOpen);
  };

  async function sendMessage(content?: string) {
    const messageContent = content || input;
    if (!messageContent.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: messageContent,
    };

    setMessages((prev) => [...prev, userMessage]);

    // Clear input if it was typed
    if (!content) {
      setInput("");
    }

    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          prompt: messageContent,
          thread_id: threadId,
          order_item_ids: []
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to send message");
      }

      if (!response.body) return;

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      const assistantMessageId = (Date.now() + 1).toString();
      setMessages((prev) => [
        ...prev,
        {
          id: assistantMessageId,
          role: "assistant",
          content: "",
        },
      ]);

      let done = false;

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;

        if (value) {
          const chunkValue = decoder.decode(value);
          const lines = chunkValue.split("\n").filter(line => line.trim() !== "");

          for (const line of lines) {
            try {
              const chunkData = JSON.parse(line);

              if (chunkData.thread_id) {
                setThreadId(chunkData.thread_id);
                continue;
              }

              // Handle the new streaming format: {"type": "message", "content": "..."}
              if (chunkData.type === "message" && chunkData.content) {
                const content = chunkData.content;
                
                setMessages((prev) => {
                  const updated = [...prev];
                  const lastMsg = updated[updated.length - 1];
                  
                  if (lastMsg && lastMsg.role === "assistant" && lastMsg.id === assistantMessageId) {
                    // Check for ORDERS tag
                    const ordersMatch = content.match(/<ORDERS>([\s\S]*?)<\/ORDERS>/);
                    if (ordersMatch) {
                      try {
                        const parsed = JSON.parse(ordersMatch[1]);
                        // Backend returns {"orders": [...]} so extract the array
                        lastMsg.orders = parsed.orders || parsed;
                        lastMsg.content = content.replace(/<ORDERS>[\s\S]*?<\/ORDERS>/, "").trim();
                      } catch (e) {
                        lastMsg.content = content;
                      }
                    }
                    // Check for ORDER tag
                    else if (content.match(/<ORDER>([\s\S]*?)<\/ORDER>/)) {
                      const orderMatch = content.match(/<ORDER>([\s\S]*?)<\/ORDER>/);
                      try {
                        const parsed = JSON.parse(orderMatch![1]);
                        // Backend returns {"order": {...}} so extract the object
                        lastMsg.productData = parsed.order || parsed;
                        lastMsg.content = content.replace(/<ORDER>[\s\S]*?<\/ORDER>/, "").trim();
                      } catch (e) {
                        lastMsg.content = content;
                      }
                    }
                    // No structured data, just replace content
                    else {
                      lastMsg.content = content;
                    }
                  }
                  
                  return updated;
                });
              } else if (chunkData.type === "error") {
                console.error("Error from backend:", chunkData.content);
                setMessages((prev) => [
                  ...prev,
                  {
                    id: (Date.now() + 2).toString(),
                    role: "assistant",
                    content: "An error occurred: " + chunkData.content,
                  },
                ]);
              }
            } catch (e) {
              console.error("Error parsing JSON chunk", e);
            }
          }
        }
      }

    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, I couldn't connect to the server. Please try again.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  }

  const agents = [
    {
      id: "refund_agent",
      name: "Refunds",
      description: "Process returns, refunds, and replacements for your orders.",
      icon: Sparkles,
      color: "from-violet-500 to-indigo-600",
      bgColor: "bg-indigo-50",
      borderColor: "border-indigo-200"
    },
    {
      id: "order_agent",
      name: "Orders",
      description: "Track shipments, view order history, and manage deliveries.",
      icon: Package,
      color: "from-emerald-400 to-teal-500",
      bgColor: "bg-emerald-50",
      borderColor: "border-emerald-200"
    },
    {
      id: "support_agent",
      name: "General Support",
      description: "Help with account settings, payments, and general inquiries.",
      icon: Bot,
      color: "from-amber-400 to-orange-500",
      bgColor: "bg-amber-50",
      borderColor: "border-amber-200"
    }
  ];

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button
          size="lg"
          className="fixed bottom-6 right-6 h-16 w-16 rounded-full bg-gradient-to-br from-violet-600 via-indigo-600 to-purple-700 shadow-2xl shadow-indigo-500/30 hover:shadow-indigo-500/50 hover:scale-110 transition-all duration-300 z-40 group"
        >
          <div className="relative">
            <MessageSquare className="h-6 w-6 text-white group-hover:scale-110 transition-transform" />
            <span className="absolute -top-1 -right-1 h-3 w-3 bg-emerald-400 rounded-full animate-pulse ring-2 ring-white"></span>
          </div>
          <span className="sr-only">Open assistant</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[720px] h-[85vh] p-0 gap-0 overflow-hidden border-0 shadow-2xl rounded-3xl bg-neutral-900 text-neutral-100 flex flex-col ring-1 ring-white/10">

        {/* Header */}
        <DialogHeader className="relative overflow-hidden px-5 py-4 shrink-0 border-b border-white/5">
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/50 via-violet-900/50 to-purple-900/50"></div>
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PGNpcmNsZSBjeD0iMzAiIGN5PSIzMCIgcj0iNCIvPjwvZz48L2c+PC9zdmc+')] opacity-20"></div>

          <div className="relative flex items-center gap-3">
            {selectedAgent ? (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-neutral-400 hover:text-white hover:bg-white/10 -ml-2 rounded-full transition-colors"
                onClick={() => setSelectedAgent(null)}
              >
                <span className="sr-only">Back</span>
                <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-4 w-4"><path d="M8.84182 3.13514C9.04327 3.32401 9.05348 3.64042 8.86462 3.84188L5.43521 7.49991L8.86462 11.1579C9.05348 11.3594 9.04327 11.6758 8.84182 11.8647C8.64036 12.0535 8.32394 12.0433 8.13508 11.8419L4.38508 7.84188C4.20477 7.64955 4.20477 7.35027 4.38508 7.15794L8.13508 3.15794C8.32394 2.95648 8.64036 2.94628 8.84182 3.13514Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path></svg>
              </Button>
            ) : (
              <div className="h-10 w-10 rounded-xl bg-white/10 backdrop-blur-sm flex items-center justify-center ring-1 ring-white/10 shadow-lg">
                <Bot className="h-5 w-5 text-indigo-300" />
              </div>
            )}

            <div>
              <DialogTitle className="text-base font-medium text-white flex items-center gap-2">
                {selectedAgent ? agents.find(a => a.id === selectedAgent)?.name : "AI Assistant"}
                <Sparkles className="h-3.5 w-3.5 text-amber-300 animate-pulse" />
              </DialogTitle>
              <DialogDescription className="text-xs text-indigo-200/70">
                {selectedAgent ? "Always online" : "Select an agent to help you"}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {/* CONTENT */}
        {!selectedAgent ? (
          /* AGENT SELECTION SCREEN */
          <div className="flex-1 overflow-y-auto p-6 bg-neutral-900 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-neutral-800 via-neutral-900 to-neutral-900">
            <div className="space-y-6">
              <div className="text-center space-y-2 mb-8">
                <h3 className="text-xl font-medium text-white">How can we help you?</h3>
                <p className="text-neutral-400 text-sm">Choose a specialized agent for your needs</p>
              </div>

              <div className="grid gap-4">
                {agents.map((agent) => (
                  <button
                    key={agent.id}
                    onClick={() => {
                      if(agent.id === "refund_agent") setSelectedAgent(agent.id)
                    }}
                    className="flex items-start gap-4 p-4 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 hover:border-indigo-500/30 transition-all text-left group hover:shadow-lg hover:shadow-indigo-500/10"
                  >
                    <div className={`h-12 w-12 rounded-xl bg-gradient-to-br ${agent.color} flex items-center justify-center shadow-lg shrink-0 group-hover:scale-110 transition-transform opacity-90 group-hover:opacity-100`}>
                      <agent.icon className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <h4 className="font-medium text-neutral-200 mb-1 group-hover:text-white transition-colors">{agent.name}</h4>
                      <p className="text-sm text-neutral-400 leading-relaxed group-hover:text-neutral-300 transition-colors">{agent.description}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* CHAT SCREEN */
          <div className="flex flex-col flex-1 overflow-hidden bg-neutral-900 relative">
            <ScrollArea className="flex-1 overflow-y-auto p-4 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none] h-full">
              {messages.length === 0 ? (
                <div className="h-[70vh] flex flex-col items-center justify-center text-center p-6 space-y-5">
                  <div className="relative">
                    <div className={`h-24 w-24 rounded-3xl bg-gradient-to-br ${agents.find(a => a.id === selectedAgent)?.color} flex items-center justify-center shadow-2xl opacity-10 blur-xl`}></div>
                    <div className={`absolute inset-0 h-24 w-24 rounded-3xl bg-gradient-to-br ${agents.find(a => a.id === selectedAgent)?.color} flex items-center justify-center shadow-inner ring-1 ring-white/10 opacity-90`}>
                      {(() => {
                        const Icon = agents.find(a => a.id === selectedAgent)?.icon || Bot;
                        return <Icon className="h-10 w-10 text-white" />;
                      })()}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <p className="font-medium text-lg text-white">
                      Hello! I&apos;m your {agents.find(a => a.id === selectedAgent)?.name}.
                    </p>
                    <p className="text-sm text-neutral-400 max-w-[260px] mx-auto leading-relaxed">
                      {selectedAgent === "refund_agent"
                        ? "I can help you process returns, check eligibility, and track your refunds."
                        : "I'm here to assist you with your inquiries."}
                    </p>
                  </div>

                  {selectedAgent === "refund_agent" && (
                    <div className="flex flex-wrap gap-2 justify-center max-w-[300px]">
                      {["List my orders", "Return policy", "Request refund"].map((text) => (
                        <button
                          key={text}
                          onClick={() => {
                            setInput(text);
                            sendMessage(text);
                          }}
                          className="px-4 py-2 text-xs font-medium rounded-full bg-white/5 border border-white/10 text-neutral-300 hover:border-indigo-500/50 hover:text-indigo-300 hover:bg-white/10 transition-all shadow-sm"
                        >
                          {text}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((message, index) => (
                    <div
                      key={message.id}
                      className={`flex ${message.role === "user" ? "justify-end" : "justify-start"
                        } animate-in slide-in-from-bottom-2 duration-300`}
                      style={{ animationDelay: `${index * 50}ms` }}
                    >
                      {message.role === "assistant" && (
                        <div className={`h-8 w-8 rounded-lg bg-gradient-to-br ${agents.find(a => a.id === selectedAgent)?.color || "from-violet-500 to-indigo-600"} flex items-center justify-center mr-3 shrink-0 shadow-lg`}>
                          <Bot className="h-4 w-4 text-white" />
                        </div>
                      )}
                      <div className={`max-w-[85%] ${message.role === "user" ? "" : "flex-1"}`}>
                        {/* Text content */}
                        <div
                          className={`rounded-2xl px-5 py-3.5 text-sm shadow-md ${message.role === "user"
                            ? "bg-gradient-to-br from-indigo-600 to-violet-600 text-white rounded-br-sm"
                            : "bg-neutral-800 border border-white/5 text-neutral-200 rounded-bl-sm markdown-content ring-1 ring-white/5"
                            }`}
                        >
                          {message.role === "assistant" ? (
                            message.content ? (
                              <ReactMarkdown>{message.content}</ReactMarkdown>
                            ) : (
                              <span className="animate-pulse">...</span>
                            )
                          ) : (
                            message.content
                          )}
                        </div>

                        {/* Order Cards - for order list */}
                        {message.orders && message.orders.length > 0 && (
                          <div className="mt-4 space-y-4">
                            {message.orders.map((order, i) => (
                              <OrderCard key={i} order={order} />
                            ))}
                          </div>
                        )}

                        {/* Product Card - for single order details */}
                        {message.productData && (
                          <div className="mt-4">
                            <ProductCard data={message.productData} />
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  {loading && messages[messages.length - 1]?.role !== "assistant" && (
                    <div className="flex justify-start animate-in slide-in-from-bottom-2">
                      <div className={`h-8 w-8 rounded-lg bg-gradient-to-br ${agents.find(a => a.id === selectedAgent)?.color || "from-violet-500 to-indigo-600"} flex items-center justify-center mr-3 shrink-0 shadow-lg`}>
                        <Bot className="h-4 w-4 text-white" />
                      </div>
                      <div className="bg-neutral-800 border border-white/5 rounded-2xl rounded-bl-sm px-4 py-4 flex items-center gap-1.5 shadow-sm ring-1 ring-white/5">
                        <span className="w-1.5 h-1.5 bg-neutral-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                        <span className="w-1.5 h-1.5 bg-neutral-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                        <span className="w-1.5 h-1.5 bg-neutral-400 rounded-full animate-bounce"></span>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </ScrollArea>

            {/* Input area */}
            <div className="p-4 border-t border-white/5 bg-neutral-900/90 backdrop-blur-md shrink-0">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  sendMessage();
                }}
                className="flex items-end gap-3"
              >
                <div className="flex-1 relative group">
                  <Textarea
                    placeholder="Type your message..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    className="min-h-[52px] max-h-[120px] resize-none rounded-2xl border-white/10 bg-neutral-800/50 focus:bg-neutral-800 text-neutral-100 placeholder:text-neutral-500 focus-visible:ring-1 focus-visible:ring-indigo-500/50 focus-visible:border-indigo-500/50 py-3.5 px-4 pr-12 transition-all [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none] shadow-inner"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                      }
                    }}
                  />
                </div>
                {messages.length > 0 && (
                  <Button
                    type="button"
                    size="icon"
                    variant="outline"
                    onClick={async () => {
                      if (threadId) {
                        try {
                          await fetch(`http://localhost:8000/chat/${threadId}`, {
                            method: "DELETE",
                            credentials: "include",
                          });
                        } catch (error) {
                          console.error("Failed to clear chat on server:", error);
                        }
                      }
                      setMessages([]);
                      setThreadId(null);
                    }}
                    className="h-12 w-12 rounded-2xl border-white/10 bg-neutral-800 text-neutral-400 hover:bg-red-500/10 hover:border-red-500/20 hover:text-red-400 transition-all"
                    title="Clear chat"
                  >
                    <Trash2 className="h-5 w-5" />
                  </Button>
                )}
                <Button
                  type="submit"
                  size="icon"
                  disabled={loading || !input.trim()}
                  className="h-12 w-12 rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/40 hover:scale-105 transition-all disabled:opacity-50 disabled:scale-100 disabled:shadow-none"
                >
                  <Send className="h-5 w-5 text-white" />
                </Button>
              </form>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
