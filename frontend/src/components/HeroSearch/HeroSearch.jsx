import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./HeroSearch.css";

function HeroSearch() {
  const navigate = useNavigate();

  const [city, setCity] = useState("");
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [guests, setGuests] = useState(1);

  function handleSearchSubmit(e) {
    e.preventDefault();

    const params = new URLSearchParams({
      city: city,
      check_in: checkIn,
      check_out: checkOut,
      guests: guests,
    });

    navigate(`/search-results?${params.toString()}`);
  }

  return (
    <section className="hero-search">
      <div className="hero-search-inner">
        <h1>Your next stay starts here</h1>

        <form className="search-card" onSubmit={handleSearchSubmit}>
          <div className="search-fields">
            <label className="search-field">
              <span>Where</span>
              <input
                type="text"
                placeholder="Where to?"
                value={city}
                onChange={(e) => setCity(e.target.value)}
              />
            </label>

            <label className="search-field">
              <span>Check-in</span>
              <input
                type="date"
                value={checkIn}
                onChange={(e) => setCheckIn(e.target.value)}
              />
            </label>

            <label className="search-field">
              <span>Check-out</span>
              <input
                type="date"
                value={checkOut}
                onChange={(e) => setCheckOut(e.target.value)}
              />
            </label>

            <label className="search-field">
              <span>Guests</span>
              <input
                type="number"
                min="1"
                value={guests}
                onChange={(e) => setGuests(Number(e.target.value))}
              />
            </label>

            <button type="submit" className="search-button">
              Search
            </button>
          </div>

          <label className="business-check">
            <input type="checkbox" />
            <span>I'm traveling for business</span>
          </label>
        </form>
      </div>
    </section>
  );
}

export default HeroSearch;