import React, { useState } from "react";
import "./App.css"; // Importamos el archivo CSS externo

function App() {
  const [results, setResults] = useState([]);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (event) => {
    setFiles(Array.from(event.target.files));
  };

  const handleSubmit = async () => {
    if (files.length === 0) return;

    setLoading(true);
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }

    try {
      const response = await fetch("http://localhost:5000/analyze", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error("Error al procesar los archivos:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="scroll-container">
        <h1>Analizador Léxico de HTML</h1>
        <div className="upload-section">
          <input type="file" multiple onChange={handleFileChange} />
          <button onClick={handleSubmit} disabled={files.length === 0 || loading}>
            {loading ? "Procesando..." : "Enviar Archivos"}
          </button>
        </div>
        <div className="results">
          {results.map((result, index) => (
            <div key={index} className="result-box">
              <h2>Resultados del archivo: {result.file_path}</h2>
              {result.errors.length > 0 ? (
                <div className="errors">
                  <h3>Errores encontrados:</h3>
                  <ul>
                    {result.errors.map((error, i) => (
                      <li key={i}>{error}</li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className="valid">El archivo es válido.</p>
              )}
              <h3>Tokens reconocidos:</h3>
              <ul className="tokens-list">
                {result.tokens.map((token, i) => (
                  <li key={i}>
                    <strong>{token[0]}</strong>: {token[1]}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;