import requests
import re
import json
import time
from urllib.parse import urlparse

class APIKeyExtractor:
    def __init__(self):
        # Only essential API key patterns
        self.patterns = {
            'Google API': r'AIza[0-9A-Za-z\-_]{35}',
            'AWS Key': r'AKIA[0-9A-Z]{16}',
            'GitHub Token': r'github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}',
            'Stripe Key': r'sk_live_[0-9a-zA-Z]{24}|sk_test_[0-9a-zA-Z]{24}',
            'Facebook Token': r'EAACEdEose0cBA[0-9A-Za-z]+',
            'Slack Token': r'xox[baprs]-[0-9a-zA-Z]{10,48}',
            'Discord Token': r'[MN][A-Za-z\d]{23,25}\.[A-Za-z\d]{6}\.[A-Za-z\d]{27,38}',
            'Generic API Key': r'api[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,40})["\']?',
            'MongoDB URI': r'mongodb(?:\+srv)?://[^\s<>"\']+',
            'Password/Secret': r'password["\']?\s*[:=]\s*["\']?([^"\'\s]{8,})["\']?'
        }
        
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    def get_content(self, url):
        """Simple content fetcher"""
        try:
            print(f"[*] Fetching: {url}")
            r = requests.get(url, headers=self.headers, timeout=10)
            return r.text if r.status_code == 200 else None
        except:
            return None
    
    def find_keys(self, content, source="page"):
        """Extract API keys from content"""
        found = {}
        
        for name, pattern in self.patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Clean up matches
                clean_matches = []
                for m in matches:
                    if isinstance(m, tuple):
                        m = m[0]  # Get first group if tuple
                    if len(str(m)) > 6:  # Ignore short matches
                        clean_matches.append(m)
                
                if clean_matches:
                    found[name] = list(set(clean_matches))[:3]  # Max 3 per type
                    print(f"  [+] Found {len(clean_matches)} {name}")
        
        return found
    
    def scan_js_files(self, html, base_url):
        """Quick scan for JS files"""
        js_keys = {}
        js_urls = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', html)
        
        for js in js_urls[:3]:  # Max 3 JS files
            if not js.startswith('http'):
                if js.startswith('//'):
                    js = 'https:' + js
                elif js.startswith('/'):
                    parsed = urlparse(base_url)
                    js = f"{parsed.scheme}://{parsed.netloc}{js}"
                else:
                    js = base_url.rstrip('/') + '/' + js.lstrip('/')
            
            print(f"[*] Checking JS: {js}")
            js_content = self.get_content(js)
            if js_content:
                keys = self.find_keys(js_content, "JS")
                if keys:
                    js_keys[js] = keys
        
        return js_keys
    
    def scan(self, url):
        """Main scan function"""
        print(f"\n{'='*50}")
        print(f"API Key Scanner - {url}")
        print(f"{'='*50}\n")
        
        # Get page content
        html = self.get_content(url)
        if not html:
            print("[!] Failed to fetch URL")
            return None
        
        # Find keys in HTML
        print("[*] Scanning main page...")
        results = {
            'url': url,
            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'main_page': self.find_keys(html),
            'js_files': {}
        }
        
        # Scan JS files
        print("\n[*] Scanning JavaScript files...")
        results['js_files'] = self.scan_js_files(html, url)
        
        # Count total
        total = sum(len(v) for v in results['main_page'].values())
        for js in results['js_files'].values():
            total += sum(len(v) for v in js.values())
        results['total'] = total
        
        return results

def main():
    print("🔑 Simple API Key Extractor")
    print("For educational use only!\n")
    
    while True:
        url = input("Enter URL (or 'quit'): ").strip()
        
        if url.lower() == 'quit':
            break
        
        if not url.startswith('http'):
            url = 'https://' + url
        
        # Run scan
        scanner = APIKeyExtractor()
        results = scanner.scan(url)
        
        if results:
            print(f"\n{'='*50}")
            print(f"RESULTS - Found {results['total']} potential keys")
            print(f"{'='*50}")
            
            if results['main_page']:
                print("\n📄 MAIN PAGE:")
                for k, v in results['main_page'].items():
                    print(f"  {k}: {', '.join(v)}")
            
            if results['js_files']:
                print("\n📁 JS FILES:")
                for js, keys in results['js_files'].items():
                    print(f"  {js.split('/')[-1]}:")
                    for k, v in keys.items():
                        print(f"    {k}: {', '.join(v)}")
            
            # Auto-save
            filename = f"keys_{int(time.time())}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Saved to: {filename}")
        
        print("\n" + "-"*50 + "\n")

if __name__ == "__main__":
    main()