"use client";

import Image from "next/image";
import { LoginPopover } from "@/components/login-popover";
import { RegisterPopover } from "@/components/register-popover";
import { AskAssistantDialog } from "@/components/ask-assistant-dialog";
import { Button } from "@/components/ui/button";
import { ShoppingBag, Search, Menu, ArrowRight, Star, Package, LogOut } from "lucide-react";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";


// Modernized Product Data
const featuredProducts = [
  {
    id: 1,
    name: "Velora Smart Speaker",
    price: "₹4,999",
    image: "https://images.unsplash.com/photo-1589561253898-768105ca91a8?auto=format&fit=crop&w=1600&q=90",
    badge: "Best Seller",
    rating: 4.8,
  },
  {
    id: 2,
    name: "Noise Cancelling Pro",
    price: "₹12,999",
    image: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=1600&q=90",
    badge: "New Arrival",
    rating: 4.9,
  },
  {
    id: 3,
    name: "Ultra HD Smart TV",
    price: "₹29,999",
    image: "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?auto=format&fit=crop&w=1600&q=90",
    badge: "Top Rated",
    rating: 4.7,
  },
  {
    id: 4,
    name: "Pro Gaming Laptop",
    price: "₹79,999",
    image: "https://images.unsplash.com/photo-1603302576837-37561b2e2302?auto=format&fit=crop&w=1600&q=90",
    badge: "Trending",
    rating: 4.6,
  },
];

const categories = [
  {
    id: 1,
    name: "Mobiles",
    image: "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=1600&q=90",
  },
  {
    id: 2,
    name: "Audio",
    image: "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=1600&q=90", // Better headphone image
  },
  {
    id: 3,
    name: "Fashion",
    image: "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=1600&q=90",
  },
  {
    id: 4,
    name: "Lifestyle",
    image: "https://images.unsplash.com/photo-1532453288672-3a27e9be9efd?auto=format&fit=crop&w=1600&q=90",
  },
];

export default function Page() {
  const router = useRouter();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState("");
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);

  // Check if user is already logged in on mount
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
      // User not logged in
      setIsLoggedIn(false);
    }
  };

  // Updated handler for Shopping Bag
  const handleCartClick = (e: React.MouseEvent) => {
    if (e) e.preventDefault();
    if (isLoggedIn) {
      router.push("/cart");
    } else {
      setShowLogin(true);
    }
  };

  const handleOrdersClick = (e: React.MouseEvent) => {
    if (e) e.preventDefault();
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
        credentials: "include" 
      });
      
      setIsLoggedIn(false);
      setUsername("");
      router.push("/landing");
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  return (
    <main className="min-h-screen bg-neutral-50 font-sans text-neutral-900 selection:bg-indigo-100 selection:text-indigo-900">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b border-neutral-200 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-8">
            <a href="#" className="text-2xl font-bold tracking-tighter text-indigo-600">
              Velora.
            </a>
            <div className="hidden md:flex gap-6 text-sm font-medium text-neutral-600">
              <a href="#" className="hover:text-indigo-600 transition-colors">New Arrivals</a>
              <a href="#" className="hover:text-indigo-600 transition-colors">Electronics</a>
              <a href="#" className="hover:text-indigo-600 transition-colors">Fashion</a>
            </div>
            
            <LoginPopover 
                open={showLogin} 
                onOpenChange={(open: boolean) => {
                    setShowLogin(open);
                    if (!open && !showRegister) {
                         // Fetch user info after login
                         checkAuthStatus();
                    }
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
                     if (!open && !showLogin) {
                         // After registration, user needs to login
                         setShowLogin(true);
                    }
                }}
                onSwitchToLogin={() => {
                    setShowRegister(false);
                    setShowLogin(true);
                }}
            />
          </div>

          <div className="flex items-center gap-4">
            <div className="relative hidden sm:block">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-neutral-400" />
              <input
                type="text"
                placeholder="Search premium products..."
                className="h-9 w-64 rounded-full bg-neutral-100 pl-9 pr-4 text-sm outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all"
              />
            </div>

            <button 
                onClick={handleOrdersClick}
                className="p-2 text-neutral-600 hover:text-indigo-600 transition-colors flex flex-col items-center gap-0.5"
                title="Orders"
            >
              <Package className="h-5 w-5" />
            </button>
            
            

            {isLoggedIn ? (
              <div className="hidden sm:flex items-center gap-3">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-50 border border-indigo-100">
                  <div className="h-6 w-6 rounded-full bg-indigo-600 flex items-center justify-center text-white text-xs font-semibold">
                    {username.charAt(0).toUpperCase()}
                  </div>
                  <span className="text-sm font-medium text-indigo-900">
                    Welcome, {username}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  className="p-2 text-neutral-600 hover:text-red-600 transition-colors"
                  title="Logout"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <Button
                onClick={() => setShowLogin(true)}
                size="sm"
                className="hidden sm:flex bg-indigo-600 hover:bg-indigo-500 h-9"
              >
                Sign In
              </Button>
            )}
            
            <button className="sm:hidden p-2">
              <Menu className="h-5 w-5" />
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden bg-neutral-900 text-white">
        <div className="absolute inset-0 opacity-20">
            <Image
                src="https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=1920&q=80"
                alt="Background"
                fill
                className="object-cover"
            />
        </div>
        <div className="absolute inset-0 bg-gradient-to-t from-neutral-900 via-neutral-900/40 to-transparent" />
        
        <div className="relative mx-auto flex flex-col items-start justify-center gap-6 px-4 py-24 sm:px-6 lg:px-8 lg:py-40">
          <span className="inline-block rounded-full bg-indigo-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-indigo-400 backdrop-blur-sm border border-indigo-500/20">
            Spring Collection 2026
          </span>
          <h1 className="max-w-2xl text-5xl font-bold tracking-tight sm:text-7xl">
            Redefine Your <span className="text-indigo-400">Style.</span>
          </h1>
          <p className="max-w-xl text-lg text-neutral-300">
            Discover a curated collection of premium electronics, fashion, and lifestyle products designed for the modern minimalists.
          </p>
          <div className="mt-4 flex gap-4">
            <Button size="lg" className="bg-white text-neutral-900 hover:bg-neutral-200">
              Shop Now
            </Button>
             <Button size="lg" variant="outline" className="border-neutral-700 text-black hover:bg-neutral-800 hover:text-white">
              View Lookbook
            </Button>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="py-16 sm:py-24">
        <div className="mx-auto px-4 sm:px-6 lg:px-8">
           <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold tracking-tight text-neutral-900">Shop by Category</h2>
             <a href="#" className="flex items-center text-sm font-semibold text-indigo-600 hover:text-indigo-500">
              Browse all categories <ArrowRight className="ml-1 h-4 w-4" />
            </a>
          </div>
          
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:gap-8 xl:gap-10">
            {categories.map((category) => (
              <div
                key={category.id}
                className="group relative aspect-[4/5] overflow-hidden rounded-xl bg-neutral-100"
              >
                <Image
                  src={category.image}
                  alt={category.name}
                  fill
                  className="object-cover transition-transform duration-500 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                <div className="absolute bottom-4 left-4">
                  <h3 className="text-lg font-semibold text-white">{category.name}</h3>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Products */}
      <section className="bg-white py-16 sm:py-24">
        <div className="mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
             <h2 className="text-2xl font-bold tracking-tight text-neutral-900">Trending Now</h2>
              <div className="flex gap-2">
                 {/* Filter buttons could go here */}
              </div>
          </div>

          <div className="grid gap-y-10 gap-x-6 sm:grid-cols-2 lg:grid-cols-4 xl:gap-x-10">
            {featuredProducts.map((product) => (
              <div key={product.id} className="group relative">
                <div className="aspect-square w-full overflow-hidden rounded-xl bg-neutral-100 relative">
                  <Image
                    src={product.image}
                    alt={product.name}
                    fill
                    className="object-cover object-center transition-transform duration-300 group-hover:scale-105"
                  />
                  <div className="absolute top-2 left-2">
                     <span className="inline-flex items-center rounded-md bg-white/90 px-2 py-1 text-xs font-medium text-neutral-700 backdrop-blur-sm shadow-sm">
                      {product.badge}
                    </span>
                  </div>
                </div>
                <div className="mt-4 flex justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-neutral-900">
                      <a href="#">
                        <span aria-hidden="true" className="absolute inset-0" />
                        {product.name}
                      </a>
                    </h3>
                    <p className="mt-1 text-sm text-neutral-500 flex items-center gap-1">
                        <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" /> {product.rating}
                    </p>
                  </div>
                  <p className="text-sm font-bold text-indigo-600">{product.price}</p>
                </div>
                <button className="mt-4 w-full rounded-lg bg-neutral-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-neutral-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-neutral-900 opacity-0 group-hover:opacity-100 transition-opacity absolute bottom-4 left-4 right-4 translate-y-2 group-hover:translate-y-0">
                    Add to Cart
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-neutral-200 bg-white pt-16 pb-8">
        <div className="mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
             <div className="col-span-2 md:col-span-1">
                <span className="text-xl font-bold text-indigo-600">Velora.</span>
                <p className="mt-4 text-sm text-neutral-500">
                    Premium products for a premium lifestyle. Quality you can trust, designs you will love.
                </p>
             </div>
             <div>
                <h3 className="text-sm font-semibold text-neutral-900">Shop</h3>
                <ul className="mt-4 space-y-2 text-sm text-neutral-600">
                    <li><a href="#" className="hover:text-indigo-600">New Arrivals</a></li>
                    <li><a href="#" className="hover:text-indigo-600">Electronics</a></li>
                    <li><a href="#" className="hover:text-indigo-600">Fashion</a></li>
                </ul>
             </div>
             <div>
                <h3 className="text-sm font-semibold text-neutral-900">Support</h3>
                <ul className="mt-4 space-y-2 text-sm text-neutral-600">
                    <li><a href="#" className="hover:text-indigo-600">Help Center</a></li>
                    <li><a href="#" className="hover:text-indigo-600">Order Status</a></li>
                    <li><a href="#" className="hover:text-indigo-600">Returns</a></li>
                </ul>
             </div>
             <div>
                <h3 className="text-sm font-semibold text-neutral-900">Company</h3>
                <ul className="mt-4 space-y-2 text-sm text-neutral-600">
                    <li><a href="#" className="hover:text-indigo-600">About</a></li>
                    <li><a href="#" className="hover:text-indigo-600">Press</a></li>
                    <li><a href="#" className="hover:text-indigo-600">Careers</a></li>
                </ul>
             </div>
          </div>
          <div className="mt-12 border-t border-neutral-100 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-xs text-neutral-400">© {new Date().getFullYear()} Velora Inc. All rights reserved.</p>
            <div className="flex gap-6 text-xs text-neutral-400">
               <a href="#" className="hover:text-neutral-600">Privacy Policy</a>
               <a href="#" className="hover:text-neutral-600">Terms of Service</a>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}
