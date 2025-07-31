"""
Lambda.hu Építőanyag AI - Backend API

Ez a fájl tartalmazza a FastAPI alkalmazás fő belépési pontját.
Az alkalmazás RESTful API-t biztosít az építőanyag adatok kezeléséhez.

Főbb funkciók:
- Kategória menedzsment (hierarchikus struktúra)
- Gyártó adatok kezelése  
- Termék információk tárolása és lekérdezése
- CORS támogatás frontend integrációhoz

Technológiák:
- FastAPI: Modern, gyors Python web framework
- SQLAlchemy: ORM adatbázis műveletekhez
- PostgreSQL: Relációs adatbázis
- Redis: Cache layer (jövőbeli használatra)
"""

from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import html
import logging
import re
import chromadb

# Relative imports for app context
from .database import get_db
from . import models
from . import schemas
from .api import admin
from .api import ai_config_admin

# Create the database tables
# Base.metadata.create_all(bind=engine)  # Temporarily disabled due to UTF-8 issues


# FastAPI alkalmazás példány létrehozása
app = FastAPI(
    title="Lambda.hu API",
    description="API for the Lambda.hu building material intelligence system.",
    version="1.0.0",
    redoc_url=None,  # Disable redoc
)

# CORS middleware konfigurálása a frontend integrációhoz
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 Router
api_v1_router = APIRouter(prefix="/api/v1")


# ==================== PRODUCT PARAMETER CLASSES ====================

class ProductFilters:
    """Encapsulates product filtering parameters"""
    def __init__(
        self,
        category_id: Optional[int] = None,
        manufacturer_id: Optional[int] = None
    ):
        self.category_id = category_id
        self.manufacturer_id = manufacturer_id


class ProductCreationData:
    """Encapsulates product creation parameters"""
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        price: Optional[float] = None,
        category_id: Optional[int] = None,
        manufacturer_id: Optional[int] = None,
        technical_specs: Optional[dict] = None
    ):
        self.name = name
        self.description = description
        self.price = price
        self.category_id = category_id
        self.manufacturer_id = manufacturer_id
        self.technical_specs = technical_specs


# ==================== VALIDATION FUNCTIONS ====================

def validate_category_exists(category_id: int, db: Session) -> bool:
    """Validates if a category exists in the database"""
    if not category_id:
        return True
    return db.query(models.Category).filter(
        models.Category.id == category_id
    ).first() is not None


def validate_manufacturer_exists(manufacturer_id: int, db: Session) -> bool:
    """Validates if a manufacturer exists in the database"""
    if not manufacturer_id:
        return True
    return db.query(models.Manufacturer).filter(
        models.Manufacturer.id == manufacturer_id
    ).first() is not None


def validate_product_creation_data(
    data: ProductCreationData, db: Session
) -> None:
    """Validates product creation data and raises HTTPException if invalid"""
    if data.category_id and not validate_category_exists(data.category_id, db):
        raise HTTPException(
            status_code=404,
            detail="Kategória nem található"
        )
    
    if data.manufacturer_id and not validate_manufacturer_exists(
        data.manufacturer_id, db
    ):
        raise HTTPException(
            status_code=404,
            detail="Gyártó nem található"
        )


# ==================== PRODUCT ENDPOINTS ====================

@api_v1_router.get("/products", response_model=List[schemas.Product])
def read_products(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products


@api_v1_router.get("/categories", response_model=List[schemas.Category])
def read_categories(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    categories = db.query(models.Category).offset(skip).limit(limit).all()
    return categories


app.include_router(api_v1_router)
app.include_router(admin.router)
app.include_router(ai_config_admin.router)


# Root endpoint for basic health check and redirect to search
@app.get("/", response_class=RedirectResponse)
async def root():
    """Redirects root to the main search interface."""
    return "/search"


# ==================== KATEGÓRIA ENDPOINTS ====================

@app.get("/categories", include_in_schema=False)
async def get_categories(db: Session = Depends(get_db)):
    """Összes kategória lekérdezése hierarchikus struktúrával"""
    categories = db.query(models.Category).all()
    return [cat.to_dict() for cat in categories]


@app.post("/categories", include_in_schema=False)
async def create_category(
    name: str,
    description: Optional[str] = None,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Új kategória létrehozása"""
    # Szülő kategória validálása ha meg van adva
    if parent_id:
        parent = db.query(models.Category).filter(
            models.Category.id == parent_id
        ).first()
        if not parent:
            raise HTTPException(
                status_code=404,
                detail="Szülő kategória nem található"
            )
    
    # Új kategória létrehozása
    new_category = models.Category(
        name=name,
        description=description,
        parent_id=parent_id
    )
    
    # Adatbázisba mentés
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    return new_category.to_dict()


# ==================== GYÁRTÓ ENDPOINTS ====================

@app.get("/manufacturers", include_in_schema=False)
async def get_manufacturers(db: Session = Depends(get_db)):
    """Összes gyártó lekérdezése"""
    manufacturers = db.query(models.Manufacturer).all()
    return [mfr.to_dict() for mfr in manufacturers]


# ==================== CHROMA DB CONNECTION ====================

def get_chroma_client():
    """Get ChromaDB client with fallback connection logic"""
    try:
        chroma_client = chromadb.HttpClient(host="chroma", port=8000)
        chroma_client.heartbeat()
        return chroma_client
    except Exception:
        try:
            chroma_client = chromadb.HttpClient(host="localhost", port=8001)
            chroma_client.heartbeat()
            return chroma_client
        except Exception as e:
            logging.error(f"ChromaDB connection failed: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Kereső szolgáltatás nem elérhető: {e}"
            )


# ==================== HTML GENERATION FUNCTIONS ====================

def generate_search_interface_html() -> str:
    """Generate the HTML content for the search interface"""
    return """
    <!DOCTYPE html>
    <html lang="hu">
    <head>
        <title>Lambda.hu Intelligens Kereső</title>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🏗️</text></svg>">
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; background-color: #f9f9f9; color: #333; }
            h1 { color: #2c3e50; }
            .search-container { display: flex; gap: 10px; margin: 20px 0; }
            .search-box { flex-grow: 1; padding: 15px; font-size: 16px; border: 1px solid #ccc; border-radius: 5px; }
            .search-box:focus { border-color: #007bff; outline: none; }
            .search-btn { padding: 15px 30px; font-size: 16px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
            .search-btn:hover { background: #0056b3; }
            .limit-selector { padding: 15px; font-size: 16px; border: 1px solid #ccc; border-radius: 5px; background-color: white; }
            .result { border: 1px solid #ddd; margin: 15px 0; padding: 15px; border-radius: 5px; background-color: white; transition: box-shadow 0.2s; }
            .result a { text-decoration: none; color: inherit; }
            .result-product:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); cursor: pointer; }
            .result-title { font-weight: 600; color: #007bff; font-size: 1.1em; }
            .result-category { color: #555; font-style: italic; margin: 4px 0; }
            .result-score { color: #28a745; font-size: 12px; font-weight: bold; }
            .result-type { float: right; font-size: 12px; background-color: #e9ecef; padding: 3px 8px; border-radius: 10px; color: #495057; }
            .loading { display: none; text-align: center; color: #666; margin: 20px; }
            .stats { background: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <h1>🏗️ Lambda.hu Intelligens Kereső</h1>
        <p>Keressen a teljes adatbázisban (<strong>167 termék és dokumentum</strong>) természetes nyelven.</p>
        
        <div class="search-container">
            <input type="text" id="searchQuery" class="search-box" placeholder="Keresés... pl. 'homlokzati kőzetgyapot' vagy 'tűzállóság'" />
            <select id="limitSelector" class="limit-selector">
                <option value="10">10</option>
                <option value="25" selected>25</option>
                <option value="50">50</option>
            </select>
            <button onclick="performSearch()" class="search-btn">Keresés</button>
        </div>
        
        <div class="loading" id="loading">🔍 Keresés az adatbázisban...</div>
        <div id="searchStats" class="stats" style="display: none;"></div>
        <div id="searchResults"></div>
        
        <script>
            async function performSearch() {
                const query = document.getElementById('searchQuery').value;
                if (!query.trim()) return;

                const limit = parseInt(document.getElementById('limitSelector').value, 10);
                
                document.getElementById('loading').style.display = 'block';
                document.getElementById('searchResults').innerHTML = '';
                document.getElementById('searchStats').style.display = 'none';
                
                try {
                    const response = await fetch('/search/rag', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query: query, limit: limit })
                    });
                    
                    if (!response.ok) {
                        throw new Error(`A szerver hibát adott: ${response.statusText}`);
                    }

                    const data = await response.json();
                    
                    document.getElementById('loading').style.display = 'none';
                    
                    // Show stats
                    document.getElementById('searchStats').innerHTML = 
                        `📊 <strong>${data.total_results}</strong> találat a(z) <strong>${data.collection_size}</strong> adatbázis elem között a következőre: "<em>${data.query}</em>"`;
                    document.getElementById('searchStats').style.display = 'block';
                    
                    // Show results
                    const resultsDiv = document.getElementById('searchResults');
                    if (!data.results || data.results.length === 0) {
                        resultsDiv.innerHTML = '<div class="result">Nincs találat.</div>';
                    } else {
                        resultsDiv.innerHTML = data.results.map(result => {
                            const isProduct = result.metadata.doc_type === 'Termék';
                            const link = isProduct ? `/products/${result.metadata.product_id}/view` : '#';
                            const resultClass = isProduct ? 'result result-product' : 'result';
                            const title_attr = isProduct ? 'Kattintson a részletekért' : 'Ez egy dokumentum, nem kattintható';

                            return `
                            <div class="${resultClass}" ${isProduct ? `onclick="window.open('${link}', '_blank')"` : ''} title="${title_attr}">
                                <a href="${link}" target="_blank" onclick="event.stopPropagation()">
                                    <span class="result-type">${result.metadata.doc_type}</span>
                                    <div class="result-title">${result.rank}. ${result.name}</div>
                                    <div class="result-category">Kategória: ${result.category}</div>
                                    <div class="result-score">Hasonlóság: ${Math.max(0, result.similarity_score * 100).toFixed(1)}%</div>
                                    <div style="margin-top: 10px;">${result.description}</div>
                                </a>
                            </div>
                            `;
                        }).join('');
                    }
                } catch (error) {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('searchResults').innerHTML = 
                        '<div class="result" style="color: red;">Hiba történt a keresés során: ' + error.message + '</div>';
                }
            }
            
            // Allow Enter key to search
            document.getElementById('searchQuery').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') performSearch();
            });
        </script>
    </body>
    </html>
    """


def extract_specs_from_pdf_content(content: str) -> Dict[str, str]:
    """Extract technical specifications from PDF text content"""
    specs = {}
    
    # Process content for pattern matching
    
    # Patterns to look for technical specifications
    patterns = [
        # Hungarian technical patterns
        (r'([Hh]ővezetési tényező|[Tt]hermal conductivity|λ[DT]?)\s*[=:≤]\s*([0-9.,]+\s*W.*?m.*?K)', 'Hővezetési tényező'),
        (r'([Tt]űzvédelmi osztály|[Ff]ire classification)\s*[=:]\s*([A-Z][0-9]*)', 'Tűzvédelmi osztály'),
        (r'([Nn]yomószilárdság|[Cc]ompressive strength)\s*[=:≥]\s*([0-9.,]+\s*[kM]?Pa)', 'Nyomószilárdság'),
        (r'([Tt]estsűrűség|[Dd]ensity)\s*[=:]\s*([0-9.,]+\s*kg.*?m)', 'Testsűrűség'),
        (r'([Oo]lvadáspont|[Mm]elting point)\s*[=>]\s*([0-9.,]+\s*°?C)', 'Olvadáspont'),
        (r'([Vv]íztaszító|[Ww]ater repellent)', 'Víztaszító'),
        (r'([Pp]áraáteresztő|[Vv]apour permeable)', 'Páraáteresztő'),
        (r'([Vv]astagsági tűrés|[Tt]hickness tolerance)\s*[=:]\s*([+-]?[0-9.,]+\s*[%mm]*)', 'Vastagsági tűrés'),
    ]
    
    content_lower = content.lower()
    
    # Look for technical data in tables or specification sections
    for pattern, spec_name in patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            if len(match.groups()) >= 2:
                value = match.group(2).strip()
                if value and len(value) < 50:  # Avoid capturing too much text
                    specs[spec_name] = value
                    break  # Take first match for each spec
    
    # Look for specific ROCKWOOL specs
    if 'a1' in content_lower or 'nem éghető' in content_lower:
        specs['Tűzvédelmi osztály'] = 'A1 (nem éghető)'
    
    if '1000°c' in content_lower or '1000 °c' in content_lower:
        specs['Olvadáspont'] = '> 1000°C'
    
    # Look for W/mK values
    wm_matches = re.findall(r'([0-9.,]+)\s*W.*?m.*?K', content, re.IGNORECASE)
    if wm_matches and 'Hővezetési tényező' not in specs:
        specs['Hővezetési tényező'] = f"{wm_matches[0]} W/mK"
    
    # Look for kPa values
    kpa_matches = re.findall(r'([0-9.,]+)\s*kPa', content, re.IGNORECASE)
    if kpa_matches and 'Nyomószilárdság' not in specs:
        specs['Nyomószilárdság'] = f"{kpa_matches[0]} kPa"
    
    return specs


def format_pdf_content_simple(content: str) -> str:
    """Simple PDF content formatter that preserves structure and improves readability"""
    if not content or content.strip() == "":
        return "<p>Nincs elérhető tartalom.</p>"
    
    lines = content.split('\n')
    formatted_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # Skip empty lines and page markers
        if not line_stripped or line_stripped.startswith('--- Page'):
            continue
            
        # Preserve meaningful spacing and structure
        original_spaces = len(line) - len(line.lstrip())
        
        # Detect and format different types of content
        if len(line_stripped) < 50 and not any(char in line_stripped for char in '.,:;()'):
            # Likely a header - make it bold
            formatted_lines.append(f"<h3>{html.escape(line_stripped)}</h3>")
        elif ':' in line_stripped and len(line_stripped) < 100:
            # Likely a specification line - emphasize it
            formatted_lines.append(f"<div class='spec-line'><strong>{html.escape(line_stripped)}</strong></div>")
        elif original_spaces > 4 or '\t' in line:
            # Indented content - preserve as table-like
            formatted_lines.append(f"<div class='table-row'>{html.escape(line_stripped)}</div>")
        elif len(line_stripped) > 10:
            # Regular paragraph content
            formatted_lines.append(f"<p>{html.escape(line_stripped)}</p>")
    
    return '\n'.join(formatted_lines) if formatted_lines else "<p>Nincs feldolgozható tartalom.</p>"


def analyze_pdf_content_structure(content: str) -> Dict[str, any]:
    """Analyze PDF content structure and extract relevant information"""
    analysis = {
        'content_type': 'unknown',
        'has_technical_specs': False,
        'has_tables': False,
        'sections': [],
        'technical_data': {},
        'structured_content': None
    }
    
    if not content:
        return analysis
    
    # Detect content type based on keywords
    content_lower = content.lower()
    if any(keyword in content_lower for keyword in ['műszaki adatlap', 'technical datasheet', 'termékadatlap']):
        analysis['content_type'] = 'technical_datasheet'
    elif any(keyword in content_lower for keyword in ['árlista', 'price list', 'katalógus']):
        analysis['content_type'] = 'catalog'
    elif any(keyword in content_lower for keyword in ['alkalmazás', 'felhasználás', 'application']):
        analysis['content_type'] = 'application_guide'
    else:
        analysis['content_type'] = 'general_info'
    
    # Detect table-like structures and technical specifications
    lines = content.split('\n')
    table_indicators = ['│', '|', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼', '\t\t']
    
    table_lines = []
    spec_lines = []
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        # Check for table indicators
        if any(indicator in line for indicator in table_indicators):
            analysis['has_tables'] = True
            table_lines.append((i, line_stripped))
        
        # Look for key-value pairs (technical specs)
        if ':' in line or '=' in line:
            tech_terms = [
                'hővezetési', 'thermal', 'λ', 'tűzvédelmi', 'fire', 'szilárdság', 'strength',
                'sűrűség', 'density', 'olvadás', 'melting', 'vastagság', 'thickness',
                'méret', 'size', 'tömeg', 'weight', 'alkalmazás', 'application'
            ]
            
            if any(term in line_stripped.lower() for term in tech_terms):
                analysis['has_technical_specs'] = True
                spec_lines.append((i, line_stripped))
    
    # Extract technical data using existing function for compatibility
    analysis['technical_data'] = extract_specs_from_pdf_content(content)
    
    # Create structured content based on detected type
    if analysis['content_type'] == 'technical_datasheet':
        analysis['structured_content'] = format_technical_datasheet(content, table_lines, spec_lines)
    elif analysis['has_tables']:
        analysis['structured_content'] = format_tabular_content(content, table_lines)
    else:
        analysis['structured_content'] = format_text_content(content)
    
    return analysis


def format_technical_datasheet(content: str, table_lines: list, spec_lines: list) -> str:
    """Format technical datasheet content preserving structure"""
    lines = content.split('\n')
    formatted = []
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith('--- Page'):
            continue
            
        # Check if this line looks like a section header
        if (len(line_stripped) < 50 and 
            any(keyword in line_stripped.lower() for keyword in 
                ['alkalmazás', 'felhasználás', 'műszaki', 'technical', 'jellemzők', 'adatok', 'tulajdonságok'])):
            formatted.append(f"<h3>{html.escape(line_stripped)}</h3>")
        
        # Format table lines with special styling
        elif any(table_line[0] == i for table_line in table_lines):
            formatted.append(f"<div class='table-row'>{html.escape(line_stripped)}</div>")
        
        # Format spec lines with emphasis
        elif any(spec_line[0] == i for spec_line in spec_lines):
            formatted.append(f"<div class='spec-line'><strong>{html.escape(line_stripped)}</strong></div>")
        
        # Regular content - preserve meaningful lines
        elif len(line_stripped) > 8:
            formatted.append(f"<p>{html.escape(line_stripped)}</p>")
    
    return '\n'.join(formatted)


def format_tabular_content(content: str, table_lines: list) -> str:
    """Format content with tables, preserving table structure"""
    lines = content.split('\n')
    formatted = []
    in_table = False
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith('--- Page'):
            continue
            
        is_table_line = any(table_line[0] == i for table_line in table_lines)
        
        if is_table_line and not in_table:
            formatted.append("<div class='table-section'>")
            in_table = True
        elif not is_table_line and in_table:
            formatted.append("</div>")
            in_table = False
        
        if is_table_line:
            formatted.append(f"<div class='table-row'>{html.escape(line_stripped)}</div>")
        elif len(line_stripped) > 5:
            formatted.append(f"<p>{html.escape(line_stripped)}</p>")
    
    if in_table:
        formatted.append("</div>")
    
    return '\n'.join(formatted)


def format_text_content(content: str) -> str:
    """Format general text content intelligently"""
    lines = content.split('\n')
    formatted = []
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith('--- Page') or len(line_stripped) < 5:
            continue
            
        # Detect headers (short lines, no punctuation, or specific keywords)
        if (len(line_stripped) < 50 and 
            (not any(char in line_stripped for char in '.,:;()') or
             any(keyword in line_stripped.lower() for keyword in ['termék', 'product', 'alkalmazás', 'használat', 'jellemzők']))):
            formatted.append(f"<h3>{html.escape(line_stripped)}</h3>")
        else:
            formatted.append(f"<p>{html.escape(line_stripped)}</p>")
    
    return '\n'.join(formatted)


def generate_product_html(product) -> str:
    """Generate HTML content for a single product view"""
    
    # Extract technical specs from full text content if available
    specs_html = "<h3>Nincsenek megadva</h3>"
    
    # Simple PDF content extraction - try to get specs first
    if product.full_text_content:
        extracted_specs = extract_specs_from_pdf_content(product.full_text_content)
        if extracted_specs:
            specs_html = "<ul>"
            for key, value in extracted_specs.items():
                specs_html += f"<li><strong>{key}:</strong> {value}</li>"
            specs_html += "</ul>"
    
    # Fall back to structured technical_specs if no content extraction
    if specs_html == "<h3>Nincsenek megadva</h3>" and product.technical_specs and isinstance(product.technical_specs, dict):
        specs_html = "<ul>"
        for key, value in product.technical_specs.items():
            if isinstance(value, dict) and 'value' in value:
                unit = value.get('unit', '')
                val = value.get('value', '')
                if val is not None:
                    specs_html += f"<li><strong>{key}:</strong> {val} {unit}</li>"
            else:
                specs_html += f"<li><strong>{key}:</strong> {value}</li>"
        specs_html += "</ul>"

    # Simple PDF content formatting with preserved structure
    formatted_full_text = format_pdf_content_simple(product.full_text_content or "Nincs elérhető tartalom.")
    
    # Detect content type based on keywords
    content_type_text = "PDF Tartalom"
    if product.full_text_content:
        content_lower = product.full_text_content.lower()
        if any(keyword in content_lower for keyword in ['műszaki adatlap', 'technical datasheet', 'termékadatlap']):
            content_type_text = "Műszaki Adatlap"
        elif any(keyword in content_lower for keyword in ['alkalmazás', 'felhasználás', 'application']):
         