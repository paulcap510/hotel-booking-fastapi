import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import "./SearchResults.css";

function SearchResults() {
  const [searchParams] = useSearchParams();

  const city = searchParams.get("city") || "";
  const checkIn = searchParams.get("check_in") || "";
  const checkOut = searchParams.get("check_out") || "";
  const guests = searchParams.get("guests") || "1";

  const [hotels, setHotels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchSearchResults() {
      setLoading(true);
      setError("");

      try {
        const params = new URLSearchParams({
          city,
          check_in: checkIn,
          check_out: checkOut,
          guests,
        });

        const response = await fetch(
          `http://127.0.0.1:8000/api/search?${params.toString()}`
        );

        if (!response.ok) {
          throw new Error("Search request failed");
        }

        const data = await response.json();
        setHotels(data);
      } catch (err) {
        setError("Could not load search results.");
      } finally {
        setLoading(false);
      }
    }

    fetchSearchResults();
  }, [city, checkIn, checkOut, guests]);

  return (
    <main className="search-results-page">
      <section className="search-results-header">
        <div className="search-results-header-inner">
          <p className="eyebrow">Search results</p>
          <h1>Available stays in {city || "your destination"}</h1>

          <div className="search-summary">
            <span>{checkIn}</span>
            <span>to</span>
            <span>{checkOut}</span>
            <span>{guests} guest{Number(guests) === 1 ? "" : "s"}</span>
          </div>

          <Link to="/" className="new-search-link">
            Start a new search
          </Link>
        </div>
      </section>

      <section className="results-section">
        <div className="results-inner">
          {loading && <p className="status-message">Searching...</p>}

          {error && <p className="status-message error-message">{error}</p>}

          {!loading && !error && hotels.length === 0 && (
            <p className="status-message">No hotels found for this search.</p>
          )}

          {!loading && !error && hotels.length > 0 && (
            <div className="results-grid">
              {hotels.map((hotel) => (
                <article key={hotel.id} className="hotel-card">
                  <img
                    src={`http://127.0.0.1:8000/static/${hotel.image_path}`}
                    alt={hotel.name}
                    className="hotel-card-image"
                  />

                  <div className="hotel-card-content">
                    <div>
                      <p className="hotel-city">{hotel.city}</p>
                      <h2>{hotel.name}</h2>
                      <p className="hotel-description">{hotel.description}</p>
                    </div>

                    <div className="hotel-card-footer">
                      <div>
                        <p className="price-label">Starting from</p>
                        <p className="hotel-price">${hotel.starting_price}</p>
                      </div>

                      <div className="availability-pill">
                        {hotel.available_rooms_count} available
                      </div>
                    </div>

                    <Link
                      to={`/hotels/${hotel.id}?check_in=${checkIn}&check_out=${checkOut}&guests=${guests}`}
                      className="view-hotel-button"
                    >
                      View hotel
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

export default SearchResults;