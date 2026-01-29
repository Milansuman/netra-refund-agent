"use client";

import Image from "next/image";
import { LoginPopover } from "@/components/login-popover";
import { RegisterPopover } from "@/components/register-popover";
import { AskAssistantDialog } from "@/components/ask-assistant-dialog";
import { Button } from "@/components/ui/button";
import { ShoppingBag, Search, Menu, ArrowRight, Star, Package, LogOut, Sparkles, Zap, Shield, Truck } from "lucide-react";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

const featuredProducts = [
  {
    id: 1,
    name: "Velora Smart Speaker",
    price: "₹4,999",
    originalPrice: "₹6,999",
    image: "https://images.unsplash.com/photo-1589561253898-768105ca91a8?auto=format&fit=crop&w=1600&q=90",
    badge: "Best Seller",
    rating: 4.8,
    reviews: 2847,
  },
  {
    id: 2,
    name: "Noise Cancelling Pro",
    price: "₹12,999",
    originalPrice: "₹16,999",
    image: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=1600&q=90",
    badge: "New Arrival",
    rating: 4.9,
    reviews: 1523,
  },
  {
    id: 3,
    name: "Ultra HD Smart TV",
    price: "₹29,999",
    originalPrice: "₹39,999",
    image: "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?auto=format&fit=crop&w=1600&q=90",
    badge: "Top Rated",
    rating: 4.7,
    reviews: 892,
  },
  {
    id: 4,
    name: "Pro Gaming Laptop",
    price: "₹79,999",
    originalPrice: "₹99,999",
    image: "https://images.unsplash.com/photo-1603302576837-37561b2e2302?auto=format&fit=crop&w=1600&q=90",
    badge: "Trending",
    rating: 4.6,
    reviews: 456,
  },
];

const categories = [
  { id: 1, name: "Mobiles", count: "234 Products", image: "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=1600&q=90", gradient: "from-rose-500 to-orange-500" },
  { id: 2, name: "Audio", count: "189 Products", image: "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=1600&q=90", gradient: "from-violet-500 to-purple-500" },
  { id: 3, name: "Fashion", count: "456 Products", image: "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=1600&q=90", gradient: "from-cyan-500 to-blue-500" },
  { id: 4, name: "Lifestyle", count: "312 Products", image: "https://images.unsplash.com/photo-1532453288672-3a27e9be9efd?auto=format&fit=crop&w=1600&q=90", gradient: "from-emerald-500 to-teal-500" },
];

const features = [
  { icon: Truck, title: "Free Delivery", desc: "On orders above ₹999" },
  { icon: Shield, title: "Secure Payment", desc: "100% protected" },
  { icon: Zap, title: "Fast Shipping", desc: "2-3 business days" },
  { icon: Sparkles, title: "Premium Quality", desc: "Guaranteed products" },
];

export default function Page() {
  const router = useRouter();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState("");
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await fetch("http://localhost:8000/me", {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setIsLoggedIn(true);
        setUsername(data.username);
      }
    } catch (err) {
      setIsLoggedIn(false);
    }
  };

  const handleOrdersClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (isLoggedIn) {
      router.push("/orders");
    } else {
      setShowLogin(true);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch("http://localhost:8000/logout", {
        method: "POST",
        credentials: "include",
      });
      setIsLoggedIn(false);
      setUsername("");
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  return (
    <main className="min-h-screen bg-white font-sans text-neutral-900 selection:bg-indigo-100 selection:text-indigo-900">
      {/* Decorative Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-[500px] h-[500px] bg-gradient-to-br from-indigo-200/40 to-violet-200/40 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 -left-40 w-[400px] h-[400px] bg-gradient-to-br from-cyan-200/30 to-blue-200/30 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-1/4 w-[300px] h-[300px] bg-gradient-to-br from-rose-200/30 to-orange-200/30 rounded-full blur-3xl"></div>
      </div>

      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b border-neutral-200/60 bg-white/70 backdrop-blur-2xl">
        <div className="mx-auto flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8 max-w-7xl">
          <div className="flex items-center gap-8">
            <a href="#" className="text-2xl font-bold tracking-tight bg-gradient-to-r from-indigo-600 via-violet-600 to-purple-600 bg-clip-text text-transparent">
              Velora.
            </a>
            <div className="hidden md:flex gap-1">
              {["New Arrivals", "Electronics", "Fashion", "Lifestyle"].map((item) => (
                <a
                  key={item}
                  href="#"
                  className="px-4 py-2 text-sm font-medium text-neutral-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-full transition-all"
                >
                  {item}
                </a>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative hidden sm:block">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
              <input
                type="text"
                placeholder="Search products..."
                className="h-10 w-64 rounded-full bg-neutral-100/80 pl-10 pr-4 text-sm outline-none focus:ring-2 focus:ring-indigo-500/20 focus:bg-white border border-transparent focus:border-indigo-200 transition-all"
              />
            </div>

            <button
              onClick={handleOrdersClick}
              className="relative p-2.5 text-neutral-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-full transition-all"
              title="Orders"
            >
              <Package className="h-5 w-5" />
            </button>

            {isLoggedIn ? (
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 pl-3 pr-4 py-1.5 rounded-full bg-gradient-to-r from-indigo-50 to-violet-50 border border-indigo-100">
                  <div className="h-7 w-7 rounded-full bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center text-white text-xs font-bold shadow-lg shadow-indigo-200">
                    {username.charAt(0).toUpperCase()}
                  </div>
                  <span className="text-sm font-medium text-indigo-900 hidden sm:block">
                    {username}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  className="p-2 text-neutral-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-all"
                  title="Logout"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <Button
                onClick={() => setShowLogin(true)}
                className="bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 shadow-lg shadow-indigo-200/50 rounded-full px-5"
              >
                Sign In
              </Button>
            )}

            <button className="md:hidden p-2 hover:bg-neutral-100 rounded-full">
              <Menu className="h-5 w-5" />
            </button>
          </div>
        </div>
      </nav>

      {/* Login/Register Popovers */}
      <LoginPopover
        open={showLogin}
        onOpenChange={(open: boolean) => {
          setShowLogin(open);
          if (!open && !showRegister) checkAuthStatus();
        }}
        onSwitchToRegister={() => {
          setShowLogin(false);
          setShowRegister(true);
        }}
      />
      <RegisterPopover
        open={showRegister}
        onOpenChange={(open: boolean) => {
          setShowRegister(open);
          if (!open && !showLogin) setShowLogin(true);
        }}
        onSwitchToLogin={() => {
          setShowRegister(false);
          setShowLogin(true);
        }}
      />

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-950 via-violet-950 to-purple-950"></div>
        <div className="absolute inset-0 opacity-30">
          <Image
            src="https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=1920&q=80"
            alt="Background"
            fill
            className="object-cover"
          />
        </div>
        <div className="absolute inset-0 bg-gradient-to-t from-indigo-950 via-transparent to-indigo-950/50" />
        
        {/* Animated gradient orbs */}
        <div className="absolute top-20 left-20 w-72 h-72 bg-indigo-500/30 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-violet-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: "1s" }}></div>

        <div className="relative mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-32">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 backdrop-blur-md px-4 py-2 text-sm text-white/90 border border-white/10 mb-6">
              <Sparkles className="h-4 w-4 text-amber-400" />
              <span>Spring Collection 2026 is here</span>
            </div>
            <h1 className="text-5xl sm:text-7xl font-bold tracking-tight text-white mb-6">
              Discover
              <span className="block bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-400 bg-clip-text text-transparent">
                Premium Lifestyle
              </span>
            </h1>
            <p className="text-lg text-white/70 mb-8 max-w-lg leading-relaxed">
              Curated collection of premium electronics, fashion, and lifestyle products designed for modern minimalists.
            </p>
            <div className="flex flex-wrap gap-4">
              <Button size="lg" className="bg-white text-indigo-900 hover:bg-white/90 shadow-2xl shadow-indigo-500/30 rounded-full px-8 h-12 text-base font-semibold">
                Shop Now
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
              <Button size="lg" variant="outline" className="border-white/30 text-white hover:bg-white/10 rounded-full px-8 h-12 text-base font-semibold backdrop-blur-sm">
                View Lookbook
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Bar */}
      <section className="relative -mt-8 z-10 mx-auto max-w-6xl px-4">
        <div className="bg-white rounded-3xl shadow-xl shadow-neutral-200/50 border border-neutral-100 p-6 grid grid-cols-2 md:grid-cols-4 gap-6">
          {features.map((feature, i) => (
            <div key={i} className="flex items-center gap-4 group">
              <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-indigo-50 to-violet-50 flex items-center justify-center group-hover:scale-110 transition-transform">
                <feature.icon className="h-5 w-5 text-indigo-600" />
              </div>
              <div>
                <p className="font-semibold text-neutral-900 text-sm">{feature.title}</p>
                <p className="text-xs text-neutral-500">{feature.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Categories */}
      <section className="py-20 relative">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-end justify-between mb-10">
            <div>
              <p className="text-sm font-semibold text-indigo-600 mb-2">EXPLORE</p>
              <h2 className="text-3xl font-bold tracking-tight text-neutral-900">Shop by Category</h2>
            </div>
            <a href="#" className="hidden sm:flex items-center gap-2 text-sm font-semibold text-indigo-600 hover:text-indigo-500 group">
              View all
              <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
            </a>
          </div>

          <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:gap-6">
            {categories.map((category, i) => (
              <div
                key={category.id}
                className="group relative aspect-[4/5] overflow-hidden rounded-3xl bg-neutral-100 cursor-pointer"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <Image
                  src={category.image}
                  alt={category.name}
                  fill
                  className="object-cover transition-all duration-700 group-hover:scale-110"
                />
                <div className={`absolute inset-0 bg-gradient-to-t ${category.gradient} opacity-60 group-hover:opacity-70 transition-opacity`} />
                <div className="absolute inset-0 flex flex-col justify-end p-6">
                  <h3 className="text-xl font-bold text-white mb-1">{category.name}</h3>
                  <p className="text-sm text-white/80">{category.count}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Products */}
      <section className="py-20 bg-gradient-to-b from-neutral-50/50 to-white relative">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-end justify-between mb-10">
            <div>
              <p className="text-sm font-semibold text-indigo-600 mb-2">TRENDING</p>
              <h2 className="text-3xl font-bold tracking-tight text-neutral-900">Best Sellers</h2>
            </div>
            <div className="hidden sm:flex gap-2">
              {["All", "Electronics", "Fashion", "Audio"].map((filter) => (
                <button
                  key={filter}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    filter === "All"
                      ? "bg-neutral-900 text-white"
                      : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200"
                  }`}
                >
                  {filter}
                </button>
              ))}
            </div>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {featuredProducts.map((product, i) => (
              <div
                key={product.id}
                className="group relative bg-white rounded-3xl border border-neutral-200/60 overflow-hidden hover:shadow-2xl hover:shadow-indigo-100/50 transition-all duration-500 hover:-translate-y-1"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <div className="aspect-square overflow-hidden bg-gradient-to-br from-neutral-100 to-neutral-50 relative">
                  <Image
                    src={product.image}
                    alt={product.name}
                    fill
                    className="object-cover transition-transform duration-700 group-hover:scale-110"
                  />
                  <div className="absolute top-3 left-3">
                    <span className="inline-flex items-center rounded-full bg-white/95 backdrop-blur-sm px-3 py-1 text-xs font-semibold text-neutral-700 shadow-lg">
                      {product.badge}
                    </span>
                  </div>
                  <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
                <div className="p-5">
                  <h3 className="font-semibold text-neutral-900 group-hover:text-indigo-600 transition-colors">
                    {product.name}
                  </h3>
                  <div className="flex items-center gap-2 mt-2">
                    <div className="flex items-center gap-1 text-amber-500">
                      <Star className="h-3.5 w-3.5 fill-current" />
                      <span className="text-sm font-medium text-neutral-700">{product.rating}</span>
                    </div>
                    <span className="text-xs text-neutral-400">({product.reviews} reviews)</span>
                  </div>
                  <div className="flex items-center justify-between mt-4">
                    <div className="flex items-baseline gap-2">
                      <span className="text-lg font-bold text-indigo-600">{product.price}</span>
                      <span className="text-sm text-neutral-400 line-through">{product.originalPrice}</span>
                    </div>
                  </div>
                  <Button className="w-full mt-4 bg-neutral-900 hover:bg-neutral-800 rounded-xl h-11 opacity-0 group-hover:opacity-100 translate-y-2 group-hover:translate-y-0 transition-all">
                    <ShoppingBag className="mr-2 h-4 w-4" />
                    Add to Cart
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Newsletter */}
      <section className="py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-600 via-violet-600 to-purple-700 p-8 sm:p-16">
            <div className="absolute top-0 right-0 w-96 h-96 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
            <div className="absolute bottom-0 left-0 w-64 h-64 bg-white/5 rounded-full blur-2xl translate-y-1/2 -translate-x-1/2"></div>
            
            <div className="relative max-w-xl mx-auto text-center">
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
                Get 20% Off Your First Order
              </h2>
              <p className="text-white/70 mb-8">
                Subscribe to our newsletter and never miss out on exclusive deals and new arrivals.
              </p>
              <form className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
                <input
                  type="email"
                  placeholder="Enter your email"
                  className="flex-1 h-12 rounded-full px-6 bg-white/10 border border-white/20 text-white placeholder:text-white/50 outline-none focus:bg-white/20 focus:border-white/40 transition-all"
                />
                <Button className="h-12 px-8 bg-white text-indigo-600 hover:bg-white/90 rounded-full font-semibold shadow-xl">
                  Subscribe
                </Button>
              </form>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-neutral-200/60 bg-neutral-50/50 pt-16 pb-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4 lg:gap-12">
            <div className="col-span-2 md:col-span-1">
              <span className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">
                Velora.
              </span>
              <p className="mt-4 text-sm text-neutral-500 leading-relaxed">
                Premium products for a premium lifestyle. Quality you can trust, designs you will love.
              </p>
            </div>
            {[
              { title: "Shop", links: ["New Arrivals", "Electronics", "Fashion", "Lifestyle"] },
              { title: "Support", links: ["Help Center", "Order Status", "Returns", "Contact Us"] },
              { title: "Company", links: ["About", "Press", "Careers", "Blog"] },
            ].map((section) => (
              <div key={section.title}>
                <h3 className="text-sm font-semibold text-neutral-900">{section.title}</h3>
                <ul className="mt-4 space-y-3">
                  {section.links.map((link) => (
                    <li key={link}>
                      <a href="#" className="text-sm text-neutral-500 hover:text-indigo-600 transition-colors">
                        {link}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          <div className="mt-12 pt-8 border-t border-neutral-200/60 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-xs text-neutral-400">
              © {new Date().getFullYear()} Velora Inc. All rights reserved.
            </p>
            <div className="flex gap-6 text-xs text-neutral-400">
              <a href="#" className="hover:text-neutral-600 transition-colors">Privacy Policy</a>
              <a href="#" className="hover:text-neutral-600 transition-colors">Terms of Service</a>
              <a href="#" className="hover:text-neutral-600 transition-colors">Cookies</a>
            </div>
          </div>
        </div>
      </footer>

      {/* Chat Assistant */}
      <AskAssistantDialog />
    </main>
  );
}
