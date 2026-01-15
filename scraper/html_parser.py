"""
HTML Parser for extracting founder information from YC company pages.
Uses BeautifulSoup for parsing and extracting LinkedIn URLs.
"""

import re
from typing import Optional
from bs4 import BeautifulSoup

from .utils import logger


# Regex patterns for LinkedIn URL matching
LINKEDIN_PATTERN = re.compile(
    r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?',
    re.IGNORECASE
)


def parse_founders_from_html(html: str, company_name: str = "") -> list[dict]:
    """
    Parse founder names and LinkedIn URLs from YC company page HTML.
    
    The YC company pages typically have a founders section with:
    - Founder names
    - Links to LinkedIn profiles (when available)
    
    Args:
        html: Raw HTML content of the company page
        company_name: Company name for fallback search URL construction
    
    Returns:
        List of founder dictionaries with keys:
        - name: Founder's full name
        - linkedin_url: LinkedIn profile URL or empty string
    """
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    founders = []
    
    # Strategy 1: Look for founder sections with specific patterns
    # YC pages often have founder info in specific div structures
    
    # Find elements that might contain founder info
    # Look for LinkedIn links first, as they often appear near founder names
    linkedin_links = soup.find_all('a', href=LINKEDIN_PATTERN)
    
    for link in linkedin_links:
        linkedin_url = link.get('href', '')
        
        # Try to find the founder name near this LinkedIn link
        founder_name = _extract_name_near_element(link)
        
        if founder_name:
            founders.append({
                'name': founder_name,
                'linkedin_url': linkedin_url
            })
    
    # Strategy 2: Look for founder section with names but no LinkedIn
    # Search for common founder section patterns
    founder_sections = _find_founder_sections(soup)
    
    for section in founder_sections:
        names = _extract_names_from_section(section)
        for name in names:
            # Check if we already have this founder
            if not any(f['name'].lower() == name.lower() for f in founders):
                founders.append({
                    'name': name,
                    'linkedin_url': ''  # No LinkedIn found
                })
    
    # Strategy 3: Look for text patterns indicating founders
    if not founders:
        founders = _extract_founders_from_text(soup, company_name)
    
    # Deduplicate by name
    seen_names = set()
    unique_founders = []
    for founder in founders:
        name_lower = founder['name'].lower().strip()
        if name_lower and name_lower not in seen_names:
            seen_names.add(name_lower)
            unique_founders.append(founder)
    
    return unique_founders


def _extract_name_near_element(element) -> str:
    """Extract what appears to be a name near a given element."""
    # Check parent elements for text that looks like a name
    parent = element.parent
    
    for _ in range(3):  # Go up to 3 levels
        if parent is None:
            break
        
        # Get text content
        text = parent.get_text(separator=' ', strip=True)
        
        # Look for name-like patterns (2-4 words, capitalized)
        words = text.split()
        for i in range(len(words)):
            # Try to find 2-3 consecutive capitalized words
            if words[i][0].isupper() if words[i] else False:
                candidate = []
                for j in range(i, min(i + 4, len(words))):
                    if words[j] and words[j][0].isupper() and len(words[j]) > 1:
                        # Skip common non-name words
                        if words[j].lower() not in {
                            'linkedin', 'twitter', 'founder', 'ceo', 'cto', 
                            'co-founder', 'cofounder', 'the', 'and', 'at'
                        }:
                            candidate.append(words[j])
                    else:
                        break
                
                if 2 <= len(candidate) <= 4:
                    return ' '.join(candidate)
        
        parent = parent.parent
    
    return ""


def _find_founder_sections(soup: BeautifulSoup) -> list:
    """Find HTML sections that likely contain founder information."""
    sections = []
    
    # Look for elements with founder-related class names or text
    founder_keywords = ['founder', 'team', 'leadership', 'about']
    
    for keyword in founder_keywords:
        # Search by class
        elements = soup.find_all(class_=re.compile(keyword, re.IGNORECASE))
        sections.extend(elements)
        
        # Search by id
        elements = soup.find_all(id=re.compile(keyword, re.IGNORECASE))
        sections.extend(elements)
    
    # Also look for headings containing "Founder"
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
        if 'founder' in heading.get_text().lower():
            # Get the next sibling or parent container
            parent = heading.parent
            if parent:
                sections.append(parent)
    
    return sections


def _extract_names_from_section(section) -> list[str]:
    """Extract potential founder names from a section."""
    names = []
    text = section.get_text(separator='\n', strip=True)
    
    # Split by newlines and look for name patterns
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        words = line.split()
        
        # A name is typically 2-4 words, all capitalized
        if 2 <= len(words) <= 4:
            if all(w[0].isupper() for w in words if w):
                # Additional validation
                if not any(skip in line.lower() for skip in [
                    'linkedin', 'twitter', 'founded', 'batch', 'active',
                    'employees', 'team size', 'location'
                ]):
                    names.append(line)
    
    return names


def _extract_founders_from_text(soup: BeautifulSoup, company_name: str) -> list[dict]:
    """
    Fallback: Extract founder names from page text using patterns.
    """
    founders = []
    text = soup.get_text()
    
    # Look for patterns like "Founded by X and Y"
    founded_pattern = re.compile(
        r'[Ff]ounded\s+(?:by|in\s+\d{4}\s+by)\s+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+and\s+[A-Z][a-z]+\s+[A-Z][a-z]+)*)',
        re.MULTILINE
    )
    
    matches = founded_pattern.findall(text)
    for match in matches:
        # Split by "and" to get individual names
        names = re.split(r'\s+and\s+', match)
        for name in names:
            name = name.strip()
            if name and len(name.split()) >= 2:
                founders.append({
                    'name': name,
                    'linkedin_url': ''
                })
    
    return founders


def find_linkedin_url(html: str, founder_name: str) -> Optional[str]:
    """
    Try to find a LinkedIn URL for a specific founder in the HTML.
    
    Args:
        html: Page HTML content
        founder_name: The founder's name to search for
    
    Returns:
        LinkedIn URL if found, None otherwise
    """
    if not html or not founder_name:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all LinkedIn links
    for link in soup.find_all('a', href=LINKEDIN_PATTERN):
        # Check if this link is near the founder's name
        parent = link.parent
        for _ in range(5):
            if parent is None:
                break
            if founder_name.lower() in parent.get_text().lower():
                return link.get('href')
            parent = parent.parent
    
    return None
