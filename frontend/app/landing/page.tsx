// app/page.tsx
import Image from "next/image";
import { AskAssistantSheet } from "@/components/ask-assistant-sheet";
import { AskAssistantDialog } from "@/components/ask-assistant-dialog";
import { Button } from "@/components/ui/button";


const featuredProducts = [
  {
    id: 1,
    name: "Echo Smart Speaker",
    price: "₹4,999",
    image:
      "https://images.unsplash.com/photo-1589561253898-768105ca91a8?auto=format&fit=crop&w=800&q=80",
    badge: "Best Seller",
  },
  {
    id: 2,
    name: "Wireless Headphones",
    price: "₹2,999",
    image:
      "https://images.unsplash.com/photo-1519677100203-a0e668c92439?auto=format&fit=crop&w=800&q=80",
    badge: "Deal of the day",
  },
  {
    id: 3,
    name: "4K Smart TV",
    price: "₹29,999",
    image:
      "https://images.unsplash.com/photo-1517048676732-d65bc937f952?auto=format&fit=crop&w=800&q=80",
    badge: "Top rated",
  },
  {
    id: 4,
    name: "Gaming Laptop",
    price: "₹79,999",
    image:
      "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=800&q=80",
    badge: "Trending",
  },
];

const categories = [
  {
    id: 1,
    name: "Mobiles",
    image:
      "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=800&q=80",
  },
  {
    id: 2,
    name: "Electronics",
    image:
      "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80",
  },
  {
    id: 3,
    name: "Fashion",
    image:
      "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=800&q=80",
  },
  {
    id: 4,
    name: "Home & Kitchen",
    image:
      "https://images.unsplash.com/photo-1505691723518-36a5ac3be353?auto=format&fit=crop&w=800&q=80",
  },
];

export default function Page() {
  return (
    <main className="min-h-screen bg-slate-100">
      {/* Top nav */}
      <header className="bg-slate-900 text-white">
        <div className="mx-auto flex items-center gap-6 px-4 py-3">
          <div className="text-xl font-bold tracking-tight">
            my<span className="text-yellow-400">Shop</span>
          </div>

          <div className="hidden flex-1 items-center gap-2 rounded-md bg-white px-3 py-2 text-sm text-slate-900 md:flex">
            <input
              type="text"
              placeholder="Search for products, brands and more"
              className="w-full bg-transparent outline-none"
            />
            
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 rounded-md bg-yellow-400 p-0 hover:bg-yellow-300 border-none"
              aria-label="Search"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
            </Button>

            <AskAssistantDialog />
          </div>

          <nav className="ml-auto flex items-center gap-4 text-sm">
            <button className="hover:underline">Hello, sign in</button>
            <button className="hover:underline">Orders</button>
            <button className="relative">
              Cart
              <span className="absolute -right-3 -top-2 rounded-full bg-yellow-400 px-1 text-[10px] font-bold text-slate-900">
                0
              </span>
            </button>
          </nav>
        </div>
      </header>


      {/* Secondary nav */}
      <div className="bg-slate-800 text-xs text-slate-100">
        <div className="mx-auto flex items-center gap-4 px-4 py-2 overflow-x-auto">
          <button className="whitespace-nowrap hover:underline">All</button>
          <button className="whitespace-nowrap hover:underline">Best Sellers</button>
          <button className="whitespace-nowrap hover:underline">Mobiles</button>
          <button className="whitespace-nowrap hover:underline">Fashion</button>
          <button className="whitespace-nowrap hover:underline">Electronics</button>
          <button className="whitespace-nowrap hover:underline">Home</button>
          <button className="whitespace-nowrap hover:underline">
            Customer Service
          </button>
        </div>
      </div>

      {/* Hero banner */}
      <section className="bg-gradient-to-r from-slate-900 to-slate-700">
        <div className="mx-auto flex  flex-col gap-6 px-4 py-10 md:flex-row">
          <div className="flex-1 text-white">
            <p className="text-xs uppercase tracking-wide text-slate-300">
              Deals inspired by Amazon
            </p>
            <h1 className="mt-2 text-3xl font-bold md:text-4xl">
              Great deals on everything you need.
            </h1>
            <p className="mt-3 text-sm text-slate-200">
              Shop top picks across electronics, fashion, home and more with fast
              delivery and easy returns.
            </p>
            <div className="mt-5 flex gap-3">
              <button className="rounded-md bg-yellow-400 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-yellow-300">
                Shop now
              </button>
              <button className="rounded-md border border-slate-400 px-4 py-2 text-sm text-slate-100 hover:bg-slate-800">
                View deals
              </button>
            </div>
          </div>

          <div className="relative h-48 flex-1 md:h-60">
            <div className="absolute inset-0 rounded-lg bg-slate-600/40" />
            <Image
              src="https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=1200&q=80"
              alt="Hero banner"
              fill
              className="rounded-lg object-cover"
            />
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="-mt-10 bg-slate-100 pb-10">
        <div className="mx-auto grid  gap-4 px-4 md:grid-cols-4">
          {categories.map((category) => (
            <div
              key={category.id}
              className="rounded-md bg-white p-3 shadow-sm hover:shadow-md transition-shadow"
            >
              <h2 className="mb-2 text-sm font-semibold">{category.name}</h2>
              <div className="relative h-32 w-full">
                <Image
                  src={category.image}
                  alt={category.name}
                  fill
                  className="rounded-md object-cover"
                />
              </div>
              <button className="mt-3 text-xs font-semibold text-sky-700 hover:underline">
                Shop now
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Featured products */}
      <section className="bg-slate-100 pb-12">
        <div className="mx-auto  px-4">
          <h2 className="mb-4 text-lg font-semibold">Featured products</h2>

          <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
            {featuredProducts.map((product) => (
              <article
                key={product.id}
                className="flex flex-col rounded-md bg-white p-3 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="relative mb-3 h-40 w-full">
                  <Image
                    src={product.image}
                    alt={product.name}
                    fill
                    className="object-contain"
                  />
                </div>

                <p className="text-xs text-emerald-700 font-semibold">
                  {product.badge}
                </p>
                <h3 className="mt-1 line-clamp-2 text-sm font-medium">
                  {product.name}
                </h3>
                <p className="mt-1 text-sm font-semibold">{product.price}</p>

                <button className="mt-3 rounded-md bg-yellow-400 px-3 py-1.5 text-xs font-semibold text-slate-900 hover:bg-yellow-300">
                  Add to cart
                </button>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-slate-900 py-6 text-xs text-slate-300">
        <div className="mx-auto flex  flex-wrap items-center justify-between gap-3 px-4">
          <p>© {new Date().getFullYear()} myShop. Inspired by Amazon.</p>
          <div className="flex gap-4">
            <button className="hover:underline">Privacy</button>
            <button className="hover:underline">Terms</button>
            <button className="hover:underline">Help</button>
          </div>
        </div>
      </footer>
    </main>
  );
}
