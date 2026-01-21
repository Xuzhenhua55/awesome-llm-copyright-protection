/**
 * Citation System for HTML Documents
 * Provides LaTeX-like citation functionality using BibTeX files
 */

class CitationSystem {
    constructor() {
        this.references = {};
        this.citationCounter = 1;
        this.citedKeys = new Set();
    }

    /**
     * Parse BibTeX content and extract references
     */
    parseBibTeX(bibtexContent) {
        // Split entries by @ and filter empty ones
        const entries = bibtexContent.split(/@(?=\w)/);
        
        entries.forEach(entry => {
            entry = entry.trim();
            if (!entry) return;
            
            // Extract entry type and key from first line
            const firstLineMatch = entry.match(/^(\w+)\s*\{\s*([^,\s}]+)/);
            if (!firstLineMatch) return;
            
            const entryType = firstLineMatch[1].toLowerCase();
            const key = firstLineMatch[2].trim();
            
            // Extract fields using improved regex
            const fields = {};
            
            // More robust field extraction that handles nested braces
            const fieldRegex = /(\w+)\s*=\s*([{"](?:[^{}"]|{[^{}]*})*[}"])/g;
            let match;
            
            while ((match = fieldRegex.exec(entry)) !== null) {
                const fieldName = match[1].toLowerCase();
                let fieldValue = match[2].trim();
                
                // Remove surrounding quotes or braces
                if (fieldValue.startsWith('"') && fieldValue.endsWith('"')) {
                    fieldValue = fieldValue.slice(1, -1);
                } else if (fieldValue.startsWith('{') && fieldValue.endsWith('}')) {
                    fieldValue = fieldValue.slice(1, -1);
                }
                
                // Clean up the value
                fieldValue = fieldValue.replace(/\s+/g, ' ').trim();
                fields[fieldName] = fieldValue;
            }
            
            console.log(`Parsed entry ${key}:`, fields);
            
            this.references[key] = {
                type: entryType,
                key: key,
                ...fields
            };
        });
    }

    /**
     * Load BibTeX file
     */
    async loadBibTeX(filePath) {
        try {
            const response = await fetch(filePath);
            const content = await response.text();
            this.parseBibTeX(content);
            console.log(`Loaded ${Object.keys(this.references).length} references from ${filePath}`);
        } catch (error) {
            console.error('Error loading BibTeX file:', error);
        }
    }

    /**
     * Format author names (simplified)
     */
    formatAuthors(authorString) {
        if (!authorString) return 'Unknown Author';
        
        const authors = authorString.split(' and ').map(author => {
            author = author.trim();
            // Handle "Last, First" format
            if (author.includes(',')) {
                const [last, first] = author.split(',').map(s => s.trim());
                return `${first} ${last}`;
            }
            return author;
        });
        
        if (authors.length === 1) return authors[0];
        if (authors.length === 2) return `${authors[0]} and ${authors[1]}`;
        if (authors.length > 2) return `${authors[0]} et al.`;
        
        return authorString;
    }

    /**
     * Format a single reference for bibliography (author, title, year)
     */
    formatReference(ref) {
        // Clean and extract author, title, and year
        const author = this.formatAuthors(ref.author || 'Unknown Author');
        const title = (ref.title || 'Untitled').replace(/[{}]/g, '').trim();
        const year = ref.year || 'n.d.';
        
        const result = `${author} (${year}). <em>${title}</em>`;
        return result;
    }

    /**
     * Create citation link
     */
    createCitation(keys) {
        const keyArray = keys.split(',').map(k => k.trim());
        const validKeys = keyArray.filter(key => this.references[key]);
        
        if (validKeys.length === 0) {
            console.warn(`Citation key(s) not found: ${keys}`);
            return `<span class="citation-error">[${keys}]</span>`;
        }
        
        // Mark as cited
        validKeys.forEach(key => this.citedKeys.add(key));
        
        // Create citation numbers
        const citationNumbers = validKeys.map(key => {
            if (!this.references[key].citationNumber) {
                this.references[key].citationNumber = this.citationCounter++;
            }
            return this.references[key].citationNumber;
        });
        
        const citationText = `[${citationNumbers.join(', ')}]`;
        const citationIds = validKeys.join(',');
        
        return `<a href="#ref-${validKeys[0]}" class="citation" data-keys="${citationIds}" title="${validKeys.map(k => this.references[k].title || k).join('; ')}">${citationText}</a>`;
    }

    /**
     * Generate bibliography HTML
     */
    generateBibliography() {
        const citedRefs = Array.from(this.citedKeys)
            .map(key => this.references[key])
            .filter(ref => ref)
            .sort((a, b) => a.citationNumber - b.citationNumber);
        
        if (citedRefs.length === 0) return '';
        
        let html = '<div class="bibliography"><h2>References</h2><ol class="reference-list">';
        
        citedRefs.forEach(ref => {
            html += `<li id="ref-${ref.key}" class="reference-item">`;
            html += this.formatReference(ref);
            html += '</li>';
        });
        
        html += '</ol></div>';
        return html;
    }

    /**
     * Process all citations in the document
     * Uses TreeWalker to avoid destroying dynamically loaded content
     */
    processCitations() {
        // Find all citation placeholders in format [cite:key1,key2]
        const citationRegex = /\[cite:([^\]]+)\]/g;
        
        // Use TreeWalker to find text nodes containing citations
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: (node) => {
                    // Skip script and style elements
                    if (node.parentElement && 
                        (node.parentElement.tagName === 'SCRIPT' || 
                         node.parentElement.tagName === 'STYLE')) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    // Only accept nodes that contain citation patterns
                    if (citationRegex.test(node.textContent)) {
                        citationRegex.lastIndex = 0; // Reset regex state
                        return NodeFilter.FILTER_ACCEPT;
                    }
                    return NodeFilter.FILTER_SKIP;
                }
            }
        );
        
        // Collect all text nodes with citations first (to avoid modifying during traversal)
        const textNodes = [];
        let node;
        while (node = walker.nextNode()) {
            textNodes.push(node);
        }
        
        // Process each text node
        textNodes.forEach(textNode => {
            const text = textNode.textContent;
            const parts = [];
            let lastIndex = 0;
            let match;
            
            citationRegex.lastIndex = 0; // Reset regex state
            while ((match = citationRegex.exec(text)) !== null) {
                // Add text before the citation
                if (match.index > lastIndex) {
                    parts.push(document.createTextNode(text.substring(lastIndex, match.index)));
                }
                // Create citation element
                const citationHTML = this.createCitation(match[1]);
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = citationHTML;
                parts.push(tempDiv.firstChild);
                
                lastIndex = match.index + match[0].length;
            }
            
            // Add remaining text after last citation
            if (lastIndex < text.length) {
                parts.push(document.createTextNode(text.substring(lastIndex)));
            }
            
            // Replace the text node with the new nodes
            if (parts.length > 0) {
                const parent = textNode.parentNode;
                parts.forEach(part => {
                    parent.insertBefore(part, textNode);
                });
                parent.removeChild(textNode);
            }
        });
    }

    /**
     * Initialize citation system
     */
    async init(bibtexPath) {
        await this.loadBibTeX(bibtexPath);
        
        // Process citations when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.processCitations();
                this.addBibliography();
            });
        } else {
            this.processCitations();
            this.addBibliography();
        }
    }

    /**
     * Add bibliography to the document
     */
    addBibliography() {
        const bibliographyContainer = document.getElementById('bibliography-container');
        if (bibliographyContainer && this.citedKeys.size > 0) {
            bibliographyContainer.innerHTML = this.generateBibliography();
        }
    }
}

// Global citation system instance
window.citationSystem = new CitationSystem();

// Convenience function for manual citations
window.cite = function(keys) {
    return window.citationSystem.createCitation(keys);
};
