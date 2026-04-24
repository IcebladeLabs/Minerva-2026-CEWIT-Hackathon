import { useState, useEffect } from "react";
import { api } from "./api";
import Auth from "./components/Auth";
import Dashboard from "./components/Dashboard";

export default function App() {
  const [loggedIn, setLoggedIn] = useState(api.isLoggedIn());

  return loggedIn
    ? <Dashboard onLogout={() => { api.logout(); setLoggedIn(false); }} />
    : <Auth onAuth={() => setLoggedIn(true)} />;
}
