import "./Navbar.css";

function Navbar() {
  return (
    <header className="navbar">
      <a href="/" className="navbar-brand" aria-label="Hot Hotels home">
        <span className="navbar-logo">H</span>
        <span className="navbar-title">Hot Hotels</span>
      </a>

      <nav className="navbar-links" aria-label="Main navigation">
        <a href="#" className="navbar-link">
          List your property
        </a>
        <a href="#" className="navbar-link">
          Support
        </a>
        <a href="#" className="navbar-link">
          Trips
        </a>
        <a href="#" className="navbar-link">
          Sign in
        </a>
        <a href="#" className="navbar-button">
          Create account
        </a>
      </nav>
    </header>
  );
}

export default Navbar;