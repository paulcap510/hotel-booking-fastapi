import { useEffect, useState } from "react";
import Navbar from "./components/Navbar/Navbar";
import HeroSearch from "./components/HeroSearch/HeroSearch";
import SearchResults from "./components/SearchResults/SearchResults";
import HotelInfo from "./components/HotelInfo/HotelInfo";

import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";

function Home() {
  return (
    <>
      <HeroSearch />

      <main className="app">
      </main>
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Navbar />

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/search-results" element={<SearchResults />} />
        <Route path="/hotels/:hotelId" element={<HotelInfo />} />
      </Routes>
    </BrowserRouter>
  );
}
export default App;

