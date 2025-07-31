import re
import html
from typing import Dict

class PDFProcessor:
    def extract_specs_from_pdf_content(self, content: str) -> Dict[str, str]:
        """Extract technical specifications from PDF text content"""
        specs = {}
        
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

    def format_pdf_content_simple(self, content: str) -> str:
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
