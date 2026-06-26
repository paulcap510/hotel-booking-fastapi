import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import "./HotelInfo.css"

function HotelInfo() {
  const { hotelId } = useParams();
  const [searchParams] = useSearchParams();

  const checkIn = searchParams.get("check_in") || "";
  const checkOut = searchParams.get("check_out") || "";
  const guests = searchParams.get("guests") || "1";

  const [hotel, setHotel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchHotelInfo() {
      try {
        const params = new URLSearchParams({
          check_in: checkIn,
          check_out: checkOut,
          guests: guests,
        });

        const response = await fetch(
          `http://127.0.0.1:8000/api/hotels/${hotelId}/details?${params.toString()}`
        );

        if (!response.ok) {
          throw new Error("Failed to fetch hotel info");
        }

        const data = await response.json();
        setHotel(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchHotelInfo();
  }, [hotelId, checkIn, checkOut, guests]);

  if (loading) {
    return <p>Loading hotel...</p>;
  }

  if (error) {
    return <p>Error: {error}</p>;
  }

  if (!hotel) {
    return <p>Hotel not found.</p>;
  }

return (
  <main className="hotel-info-page">
    <section className="hotel-info-hero">
      <div className="hotel-info-hero-inner">
        <div>
          <p className="hotel-info-eyebrow">Hotel details</p>
          <h1>{hotel.name}</h1>
          <p className="hotel-info-city">{hotel.city}</p>
          <p className="hotel-info-description">{hotel.description}</p>
        </div>

        <div className="hotel-info-image-wrap">
          <img
            src={`http://127.0.0.1:8000/static/${hotel.image_path}`}
            alt={hotel.name}
            className="hotel-info-image"
          />
        </div>
      </div>
    </section>

    <section className="hotel-info-body">
      <div className="hotel-info-inner">
        <div className="hotel-info-summary">
          <span>{checkIn}</span>
          <span>to</span>
          <span>{checkOut}</span>
          <span>
            {guests} guest{Number(guests) === 1 ? "" : "s"}
          </span>
        </div>

        <h2 className="rooms-heading">Available rooms</h2>

        {hotel.rooms.length === 0 ? (
          <p className="hotel-info-status">
            No rooms available for this search.
          </p>
        ) : (
          <div className="rooms-grid">
            {hotel.rooms.map((room) => (
              <article key={room.id} className="room-card">
                <div>
                  <h3>{room.room_type}</h3>

                  <div className="room-meta">
                    <span>Max {room.max_guests} guests</span>
                    <span>{room.available_inventory} available</span>
                  </div>
                </div>

                <div className="room-price-panel">
                  <p className="room-price-label">Per night</p>
                  <p className="room-price">${room.price_per_night}</p>

                  {room.available ? (
                    <button className="book-room-button">
                      Book this room
                    </button>
                  ) : (
                    <button className="book-room-button" disabled>
                      Unavailable
                    </button>
                  )}
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

export default HotelInfo;