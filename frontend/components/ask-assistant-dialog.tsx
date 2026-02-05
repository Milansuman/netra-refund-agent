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
  // Status color mapping
  const statusColors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800",
    completed: "bg-green-100 text-green-800",
    shipped: "bg-blue-100 text-blue-800",
    cancelled: "bg-red-100 text-red-800",
    delivered: "bg-emerald-100 text-emerald-800",
  };

  const statusClass = statusColors[order.status.toLowerCase()] || "bg-gray-100 text-gray-800";

  return (
    <div className="bg-white rounded-xl border border-neutral-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow">
      {/* Card Header */}
      <div className="bg-gradient-to-r from-indigo-50 to-violet-50 px-4 py-3 border-b border-neutral-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Package className="h-4 w-4 text-indigo-600" />
            <span className="font-semibold text-neutral-900">Order #{order.id}</span>
          </div>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusClass}`}>
            {order.status}
          </span>
        </div>
      </div>

      {/* Card Body - Items List */}
      <div className="p-4 space-y-2">
        {order.items.map((item) => (
          <div key={item.id} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <ShoppingBag className="h-3.5 w-3.5 text-neutral-400" />
              <span className="text-neutral-700">{item.name}</span>
              <span className="text-neutral-400">×{item.quantity}</span>
            </div>
            <span className="text-neutral-600">${item.price.toFixed(2)}</span>
          </div>
        ))}
      </div>

      {/* Card Footer */}
      <div className="bg-neutral-50 px-4 py-3 border-t border-neutral-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-neutral-500">
            <CreditCard className="h-3.5 w-3.5" />
            <span>{order.payment_method}</span>
          </div>
          <span className="font-semibold text-indigo-600">${order.paid_amount.toFixed(2)}</span>
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
    pending: "bg-yellow-100 text-yellow-800",
    processing: "bg-blue-100 text-blue-800",
    shipped: "bg-indigo-100 text-indigo-800",
    delivered: "bg-green-100 text-green-800",
    cancelled: "bg-red-100 text-red-800",
  };

  const statusClass = statusColors[data.status.toLowerCase()] || "bg-gray-100 text-gray-800";

  return (
    <div className="bg-white rounded-xl border border-neutral-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 px-4 py-3 border-b border-neutral-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Package className="h-4 w-4 text-purple-600" />
            <span className="font-semibold text-neutral-900">Order #{data.order_id}</span>
          </div>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusClass}`}>
            {data.status}
          </span>
        </div>
      </div>

      {/* Products List */}
      <div className="p-4 space-y-4">
        {data.items.map((item) => (
          <div key={item.id} className="border-b border-neutral-100 pb-3 last:border-0 last:pb-0">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <ShoppingBag className="h-4 w-4 text-purple-500" />
                  <span className="font-medium text-neutral-800">{item.name}</span>
                  <span className="text-xs text-neutral-400">ID: {item.id}</span>
                </div>
                <p className="text-sm text-neutral-500 mt-1 ml-6">{item.description}</p>
                <div className="flex items-center gap-4 mt-2 ml-6 text-xs text-neutral-500">
                  <span>Qty: {item.quantity}</span>
                  <span>Tax: {item.tax_percent}%</span>
                  {item.discounts.length > 0 && (
                    <span className="text-green-600">🏷️ {item.discounts.join(", ")}</span>
                  )}
                </div>
              </div>
              <span className="font-semibold text-neutral-700">${item.unit_price.toFixed(2)}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="bg-neutral-50 px-4 py-3 border-t border-neutral-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-neutral-500">
            <CreditCard className="h-3.5 w-3.5" />
            <span>{data.payment_method}</span>
          </div>
          <span className="font-bold text-purple-600">${data.total_paid.toFixed(2)}</span>
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

              // Parse node updates from LangGraph
              for (const key of Object.keys(chunkData)) {
                const nodeData = chunkData[key];
                if (nodeData?.messages && Array.isArray(nodeData.messages)) {

                  // Check ALL messages for ORDER_DATA or PRODUCT_DATA (from tool responses)
                  for (const msg of nodeData.messages) {
                    const msgContent = msg.content || "";

                    // Check for ORDER_DATA (list of orders)
                    if (msgContent.includes("<!--ORDER_DATA:")) {
                      const { orders } = parseOrderData(msgContent);
                      if (orders) {
                        setMessages(prev => prev.map(m =>
                          m.id === assistantMessageId
                            ? { ...m, orders }
                            : m
                        ));
                      }
                    }

                    // Check for PRODUCT_DATA (single order details)
                    if (msgContent.includes("<!--PRODUCT_DATA:")) {
                      const { productData } = parseProductData(msgContent);
                      if (productData) {
                        setMessages(prev => prev.map(m =>
                          m.id === assistantMessageId
                            ? { ...m, productData }
                            : m
                        ));
                      }
                    }
                  }

                  // Get the AI message for the text content
                  const aiMessages = nodeData.messages.filter(
                    (m: { type?: string }) => m.type === "ai" || m.type === "AIMessage"
                  );
                  if (aiMessages.length > 0) {
                    const lastAiMsg = aiMessages[aiMessages.length - 1];
                    const content = lastAiMsg.content || "";

                    setMessages(prev => prev.map(msg =>
                      msg.id === assistantMessageId
                        ? { ...msg, content: content }
                        : msg
                    ));
                  }
                }
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
      name: "Refund Agent",
      description: "Process returns, refunds, and replacements for your orders.",
      icon: Sparkles,
      color: "from-violet-500 to-indigo-600",
      bgColor: "bg-indigo-50",
      borderColor: "border-indigo-200"
    },
    {
      id: "order_agent",
      name: "Order Agent",
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
      <DialogContent className="sm:max-w-[720px] p-0 gap-0 overflow-hidden border-0 shadow-2xl rounded-3xl bg-white/95 backdrop-blur-xl h-[600px] flex flex-col">

        {/* Header */}
        <DialogHeader className="relative overflow-hidden px-5 py-4 shrink-0">
          <div className="absolute inset-0 bg-gradient-to-br from-violet-600 via-indigo-600 to-purple-700"></div>
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PGNpcmNsZSBjeD0iMzAiIGN5PSIzMCIgcj0iNCIvPjwvZz48L2c+PC9zdmc+')] opacity-50"></div>

          <div className="relative flex items-center gap-3">
            {selectedAgent ? (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-white hover:bg-white/20 -ml-2"
                onClick={() => setSelectedAgent(null)}
              >
                <span className="sr-only">Back</span>
                <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-4 w-4"><path d="M8.84182 3.13514C9.04327 3.32401 9.05348 3.64042 8.86462 3.84188L5.43521 7.49991L8.86462 11.1579C9.05348 11.3594 9.04327 11.6758 8.84182 11.8647C8.64036 12.0535 8.32394 12.0433 8.13508 11.8419L4.38508 7.84188C4.20477 7.64955 4.20477 7.35027 4.38508 7.15794L8.13508 3.15794C8.32394 2.95648 8.64036 2.94628 8.84182 3.13514Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path></svg>
              </Button>
            ) : (
              <div className="h-11 w-11 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center ring-2 ring-white/20">
                <Bot className="h-6 w-6 text-white" />
              </div>
            )}

            <div>
              <DialogTitle className="text-base font-semibold text-white flex items-center gap-2">
                {selectedAgent ? agents.find(a => a.id === selectedAgent)?.name : "AI Assistant"}
                <Sparkles className="h-4 w-4 text-amber-300" />
              </DialogTitle>
              <DialogDescription className="text-xs text-white/70">
                {selectedAgent ? "Always online" : "Select an agent to help you"}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {/* CONTENT */}
        {!selectedAgent ? (
          /* AGENT SELECTION SCREEN */
          <div className="flex-1 overflow-y-auto p-6 bg-gradient-to-b from-neutral-50 to-white">
            <div className="space-y-6">
              <div className="text-center space-y-2 mb-8">
                <h3 className="text-xl font-bold text-neutral-900">How can we help you?</h3>
                <p className="text-neutral-500 text-sm">Choose a specialized agent for your needs</p>
              </div>

              <div className="grid gap-4">
                {agents.map((agent) => (
                  <button
                    key={agent.id}
                    onClick={() => setSelectedAgent(agent.id)}
                    className="flex items-start gap-4 p-4 rounded-2xl bg-white border border-neutral-200 shadow-sm hover:shadow-md hover:border-indigo-300 hover:scale-[1.02] transition-all text-left group"
                  >
                    <div className={`h-12 w-12 rounded-xl bg-gradient-to-br ${agent.color} flex items-center justify-center shadow-lg shrink-0 group-hover:scale-110 transition-transform`}>
                      <agent.icon className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-neutral-900 mb-1">{agent.name}</h4>
                      <p className="text-sm text-neutral-500 leading-relaxed">{agent.description}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* CHAT SCREEN */
          <div className="flex flex-col flex-1 overflow-hidden bg-gradient-to-b from-neutral-50 to-white relative">
            <ScrollArea className="flex-1 overflow-y-auto p-4 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-5">
                  <div className="relative">
                    <div className={`h-20 w-20 rounded-3xl bg-gradient-to-br ${agents.find(a => a.id === selectedAgent)?.color} flex items-center justify-center shadow-lg opacity-20`}></div>
                    <div className={`absolute inset-0 h-20 w-20 rounded-3xl bg-gradient-to-br ${agents.find(a => a.id === selectedAgent)?.color} flex items-center justify-center shadow-lg scale-90`}>
                      {(() => {
                        const Icon = agents.find(a => a.id === selectedAgent)?.icon || Bot;
                        return <Icon className="h-10 w-10 text-white" />;
                      })()}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <p className="font-semibold text-lg text-neutral-900">
                      Hello! I'm your {agents.find(a => a.id === selectedAgent)?.name}.
                    </p>
                    <p className="text-sm text-neutral-500 max-w-[260px] mx-auto leading-relaxed">
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
                            // We need to wait for state update in a real app, but here we can just call sendMessage with content
                            // actually sendMessage requires input state if content not passed, but we can pass content.
                            // But better to simulate typing:

                            // For simplicity let's just trigger it immediately
                            sendMessage(text);
                          }}
                          className="px-4 py-2 text-xs font-medium rounded-full bg-white border border-neutral-200 text-neutral-600 hover:border-indigo-300 hover:text-indigo-600 hover:bg-indigo-50 transition-all shadow-sm"
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
                        <div className={`h-8 w-8 rounded-xl bg-gradient-to-br ${agents.find(a => a.id === selectedAgent)?.color || "from-violet-500 to-indigo-600"} flex items-center justify-center mr-2 shrink-0 shadow-lg shadow-indigo-200`}>
                          <Bot className="h-4 w-4 text-white" />
                        </div>
                      )}
                      <div className={`max-w-[85%] ${message.role === "user" ? "" : "flex-1"}`}>
                        {/* Text content */}
                        <div
                          className={`rounded-2xl px-4 py-3 text-sm shadow-sm ${message.role === "user"
                            ? "bg-gradient-to-br from-indigo-600 to-violet-600 text-white rounded-br-md whitespace-pre-wrap"
                            : "bg-white border border-neutral-100 text-neutral-800 rounded-bl-md markdown-content"
                            }`}
                        >
                          {message.role === "assistant" ? (
                            message.content ? (
                              <ReactMarkdown>{message.content}</ReactMarkdown>
                            ) : (
                              "..."
                            )
                          ) : (
                            message.content
                          )}
                        </div>

                        {/* Order Cards - for order list */}
                        {message.orders && message.orders.length > 0 && (
                          <div className="mt-3 space-y-3">
                            {message.orders.map((order) => (
                              <OrderCard key={order.id} order={order} />
                            ))}
                          </div>
                        )}

                        {/* Product Card - for single order details */}
                        {message.productData && (
                          <div className="mt-3">
                            <ProductCard data={message.productData} />
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  {loading && messages[messages.length - 1]?.role !== "assistant" && (
                    <div className="flex justify-start animate-in slide-in-from-bottom-2">
                      <div className={`h-8 w-8 rounded-xl bg-gradient-to-br ${agents.find(a => a.id === selectedAgent)?.color || "from-violet-500 to-indigo-600"} flex items-center justify-center mr-2 shrink-0 shadow-lg shadow-indigo-200`}>
                        <Bot className="h-4 w-4 text-white" />
                      </div>
                      <div className="bg-white border border-neutral-100 rounded-2xl rounded-bl-md px-4 py-3 flex items-center gap-1.5 shadow-sm">
                        <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                        <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                        <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></span>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </ScrollArea>

            {/* Input area */}
            <div className="p-4 border-t border-neutral-100 bg-white/80 backdrop-blur-sm shrink-0">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  sendMessage();
                }}
                className="flex items-end gap-2"
              >
                <div className="flex-1 relative">
                  <Textarea
                    placeholder="Type your message..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    className="min-h-[48px] max-h-[120px] resize-none rounded-2xl border-neutral-200 bg-neutral-50 focus:bg-white focus-visible:ring-2 focus-visible:ring-indigo-500/20 focus-visible:border-indigo-300 py-3 px-4 pr-12 transition-all [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
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
                    className="h-12 w-12 rounded-2xl border-neutral-200 hover:bg-red-50 hover:border-red-200 hover:text-red-600 transition-all"
                    title="Clear chat"
                  >
                    <Trash2 className="h-5 w-5" />
                  </Button>
                )}
                <Button
                  type="submit"
                  size="icon"
                  disabled={loading || !input.trim()}
                  className="h-12 w-12 rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 shadow-lg shadow-indigo-200 hover:shadow-indigo-300 hover:scale-105 transition-all disabled:opacity-50 disabled:scale-100 disabled:shadow-none"
                >
                  <Send className="h-5 w-5" />
                </Button>
              </form>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
