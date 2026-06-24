import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [hotels, setHotels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  //** useEffect: run this code after React renders the component
  //** */ useEffect lets you run code after React renders, and the dependency array controls when/how often it runs. */
  useEffect(() => {
    async function fetchHotels() {
      try {
        const response = await fetch("http://127.0.0.1:8000/api/hotels");

        if (!response.ok) {
          throw new Error("Failed to fetch hotels");
        }

        const data = await response.json();
        setHotels(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchHotels();
  }, []);

  if (loading) {
    return (
      <main className="app">
        <p>Loading hotels...</p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="app">
        <p>Error: {error}</p>
      </main>
    );
  }

  return (
    <main className="app">
      <h1>Hot Hotels</h1>
      <p>React frontend connected to FastAPI.</p>

      <section>
        <h2>Hotels</h2>

        {hotels.length === 0 ? (
          <p>No hotels found.</p>
        ) : (
          <ul>
            {hotels.map((hotel) => (
              <li key={hotel.id}>
                <strong>{hotel.name}</strong> — {hotel.price}
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}

export default App;