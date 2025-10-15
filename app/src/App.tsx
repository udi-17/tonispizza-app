import { useState } from "react";
import "./App.css";

type MenuItem = {
  id: number;
  name: string;
  price: number;
  image: string;
};

type Menu = Record<string, MenuItem[]>;

export default function App() {
  const [cart, setCart] = useState<MenuItem[]>([]);
  const [category, setCategory] = useState<string>("burgers");

  const menu: Menu = {
    burgers: [
      { id: 1, name: "Golden Classic", price: 45, image: "/img/classic.jpg" },
      { id: 2, name: "Double Deluxe", price: 55, image: "/img/double.jpg" },
      { id: 3, name: "Vegan King", price: 48, image: "/img/vegan.jpg" },
    ],
    sides: [
      { id: 4, name: "צ’יפס קלאסי", price: 15, image: "/img/fries.jpg" },
      { id: 5, name: "טבעות בצל", price: 18, image: "/img/onion.jpg" },
    ],
    drinks: [
      { id: 6, name: "קולה", price: 10, image: "/img/cola.jpg" },
      { id: 7, name: "מים", price: 8, image: "/img/water.jpg" },
    ],
  };

  const addToCart = (item: MenuItem) => {
    setCart((prev) => [...prev, item]);
  };

  return (
    <div className="kiosk bg-black text-white min-h-screen flex">
      <div className="menu w-3/4 p-4">
        <h1 className="text-4xl text-yellow-400 font-bold mb-4">Golden-Bis</h1>

        <div className="categories flex gap-4 mb-4">
          {Object.keys(menu).map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={`px-4 py-2 rounded ${
                category === cat ? "bg-yellow-500" : "bg-gray-700"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {menu[category].map((item) => (
            <div
              key={item.id}
              className="bg-gray-800 rounded-lg p-3 text-center hover:scale-105 transition"
            >
              <img
                src={item.image}
                alt={item.name}
                className="w-full h-40 object-cover rounded"
              />
              <h2 className="text-xl mt-2">{item.name}</h2>
              <p className="text-yellow-400 text-lg">{item.price} ₪</p>
              <button
                onClick={() => addToCart(item)}
                className="bg-yellow-500 text-black font-bold mt-2 px-4 py-2 rounded"
              >
                הוסף להזמנה
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="cart w-1/4 bg-gray-900 p-4">
        <h2 className="text-2xl font-bold mb-3 text-yellow-400">ההזמנה שלי</h2>
        {cart.length === 0 ? (
          <p>אין פריטים עדיין</p>
        ) : (
          <>
            {cart.map((item, index) => (
              <div key={index} className="flex justify-between mb-2">
                <span>{item.name}</span>
                <span>{item.price} ₪</span>
              </div>
            ))}
            <hr className="my-2" />
            <div className="flex justify-between text-lg">
              <span>סה״כ:</span>
              <span>
                {cart.reduce((sum, item) => sum + item.price, 0)} ₪
              </span>
            </div>
            <button className="bg-yellow-500 text-black font-bold mt-4 w-full py-2 rounded">
              לתשלום
            </button>
          </>
        )}
      </div>
    </div>
  );
}
