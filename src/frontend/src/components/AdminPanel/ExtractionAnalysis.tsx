'use client';

import React, { useState, useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { materialDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface ExtractionResult {
  product_name?: string;
  confidence_score?: number;
  [key: string]: any;
}

interface ComparisonData {
  pdf_filename: string;
  structured_extraction: ExtractionResult | { error: string };
  raw_haiku_extraction: ExtractionResult | { error: string };
}

const API_BASE = 'http://localhost:8000/admin';

const ExtractionAnalysis: React.FC = () => {
  const [report, setReport] = useState<ComparisonData[]>([]);
  const [selectedPdf, setSelectedPdf] = useState<ComparisonData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/analysis/extraction-comparison`);
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to fetch analysis report');
      }
      const data = await response.json();
      setReport(data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, []);

  const renderJson = (data: object | null | undefined) => {
    if (!data) return <div className="text-gray-500">No data available.</div>;
    return (
      <SyntaxHighlighter language="json" style={materialDark} customStyle={{ margin: 0, padding: '1rem', height: '100%' }}>
        {JSON.stringify(data, null, 2)}
      </SyntaxHighlighter>
    );
  };
  
  const getConfidenceColor = (score: number | undefined) => {
    if (score === undefined) return 'bg-gray-400';
    if (score >= 0.9) return 'bg-green-500';
    if (score >= 0.75) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">🔬 Adatkinyerési Stratégiák Elemzése</h2>
        <button
          onClick={fetchReport}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          disabled={loading}
        >
          {loading ? 'Frissítés...' : '🔄 Frissítés'}
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          ❌ Hiba a riport betöltése közben: {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* PDF List */}
        <div className="md:col-span-1 bg-white p-4 rounded-lg shadow h-screen-70 overflow-y-auto">
          <h3 className="text-lg font-semibold mb-3 border-b pb-2">Feldolgozott PDF-ek ({report.length})</h3>
          <ul className="space-y-2">
            {report.map((item) => (
              <li key={item.pdf_filename}>
                <button
                  onClick={() => setSelectedPdf(item)}
                  className={`w-full text-left p-2 rounded text-sm ${selectedPdf?.pdf_filename === item.pdf_filename ? 'bg-blue-100 font-bold' : 'hover:bg-gray-100'}`}
                >
                  {item.pdf_filename}
                </button>
              </li>
            ))}
          </ul>
        </div>

        {/* Comparison View */}
        <div className="md:col-span-2 space-y-4">
          {!selectedPdf ? (
            <div className="flex items-center justify-center h-full bg-white rounded-lg shadow">
                <p className="text-gray-500">Válassz egy PDF-et a bal oldali listából az elemzés megtekintéséhez.</p>
            </div>
          ) : (
            <div className="bg-white p-4 rounded-lg shadow">
                <h3 className="text-xl font-bold mb-4">{selectedPdf.pdf_filename}</h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-screen-60">
                    {/* Structured Extraction */}
                    <div className="flex flex-col">
                        <h4 className="font-semibold text-lg mb-2">1. Strukturált Kinyerés (Jelenlegi)</h4>
                        <div className="flex items-center gap-2 mb-2">
                            <span className={`w-4 h-4 rounded-full ${getConfidenceColor(
                                'structured_extraction' in selectedPdf && 
                                selectedPdf.structured_extraction && 
                                'confidence_score' in selectedPdf.structured_extraction 
                                    ? selectedPdf.structured_extraction.confidence_score 
                                    : undefined
                            )}`}></span>
                            <span>Konfidencia: {(
                                'structured_extraction' in selectedPdf && 
                                selectedPdf.structured_extraction && 
                                'confidence_score' in selectedPdf.structured_extraction 
                                    ? selectedPdf.structured_extraction.confidence_score?.toFixed(2) 
                                    : 'N/A'
                            )}</span>
                        </div>
                        <div className="flex-grow bg-gray-800 rounded-lg overflow-hidden">
                            {renderJson(selectedPdf.structured_extraction)}
                        </div>
                    </div>
                    {/* Raw Haiku Extraction */}
                    <div className="flex flex-col">
                        <h4 className="font-semibold text-lg mb-2">2. "Nyers" Haiku Kinyerés</h4>
                         <div className="flex items-center gap-2 mb-2">
                            <span>(Nincs konfidencia metrika)</span>
                        </div>
                        <div className="flex-grow bg-gray-800 rounded-lg overflow-hidden">
                            {renderJson(selectedPdf.raw_haiku_extraction)}
                        </div>
                    </div>
                </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ExtractionAnalysis; 