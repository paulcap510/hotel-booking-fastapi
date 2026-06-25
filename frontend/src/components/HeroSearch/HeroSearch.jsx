import { useState } from "react";
import "./HeroSearch.css";


function HeroSearch() {
  const [city, setCity] = useState("");
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [guests, setGuests] = useState(1);

  //! In a normal HTML form, clicking submit makes the browser do its default behavior
  //! In React, we usually do not want the page to reload. We want React to handle the form submission itself
  function handleSearchSubmit(e) {
    e.preventDefault();

    console.log({
      city,
      checkIn,
      checkOut,
      guests,
    });
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