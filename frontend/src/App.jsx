import { useState } from "react";
import Header from "./components/Header";

export default function App() {
  const [currentTab, setCurrentTab] = useState("agenda");

  return (
    <div className="app-container">
      <Header
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        onRefresh={() => console.log("Refrescando...")}
      />

      <main className="main-content">
        {currentTab === "agenda" && (
          <div className="tab-placeholder">
            <p>Vista de Agenda de Hoy (siguiente paso)</p>
          </div>
        )}
        {currentTab === "new" && (
          <div className="tab-placeholder">
            <p>Formulario de Nueva Cita (siguiente paso)</p>
          </div>
        )}
        {currentTab === "upcoming" && (
          <div className="tab-placeholder">
            <p>Vista de Todas las Citas Futuras (siguiente paso)</p>
          </div>
        )}
      </main>
    </div>
  );
}
