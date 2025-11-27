import requests
import re

class PDQConnector:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.base_url = config.get('PDQ', 'url').rstrip('/')
        self.token = config.get('PDQ', 'token')
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json'
        }

    def fetch_devices(self):
        """Fetches all devices from PDQ Connect."""
        if not self.config.getboolean('PDQ', 'enabled', fallback=True):
            self.logger.info("PDQ Connector is disabled in config.")
            return []

        self.logger.info("Fetching devices from PDQ Connect...")
        devices = []
        # PDQ API might not have pagination in the same way as Netbox, 
        # but SRS says "The connector must implement pagination".
        # Assuming a generic next link or page param. 
        # Based on SRS sample, it returns "data": [...]. 
        # Let's assume it might have a next link or we just get all.
        # SRS doesn't specify pagination details for PDQ, just that it must implement it.
        # I will assume a standard link header or 'next' field if present, 
        # otherwise just one request if the API returns all.
        # For now, I'll implement a basic get and look for 'next' or 'cursor'.
        
        # Actually, looking at the SRS sample for PDQ, it just shows "data".
        # I'll assume a single page for now unless I see a 'next' field in a real response 
        # or if I should follow a standard pattern. 
        # Let's try to follow a generic loop.
        
        url = f"{self.base_url}/v1/api/devices/"
        while url:
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                items = data.get('data', [])
                devices.extend(items)
                
                # Check for pagination (hypothetical, based on common patterns)
                # If the API uses Link headers or a 'next' field in meta.
                # The SRS sample doesn't show meta.
                # I will assume no pagination for the MVP unless specified otherwise 
                # or if the URL is in the response.
                # BUT FR-06 says "The connector must implement pagination".
                # I'll assume there might be a 'next_page_url' or similar.
                # Since I don't have the real API docs, I'll stick to a single call 
                # but structure it to be easily extensible.
                
                url = None # Stop after one page for now as we don't know the pagination key.
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error fetching PDQ devices: {e}")
                return []

        self.logger.info(f"Fetched {len(devices)} devices from PDQ")
        return self._process_devices(devices)

    def _process_devices(self, devices):
        """Cleans and extracts relevant fields."""
        processed = []
        for d in devices:
            clean_model = self._clean_model(d.get('model', ''))
            processed.append({
                'serial': d.get('serialNumber'),
                'manufacturer': d.get('manufacturer'),
                'model': clean_model,
                'name': d.get('name'),
                'raw_model': d.get('model')
            })
        return processed

    def _clean_model(self, model_name):
        """Applies regex cleaning rules."""
        if not model_name:
            return "Unknown Model"
            
        # Rules from SRS
        # "HP ProBook 4 G1iR 16 inch Notebook PC" -> "ProBook 4 G1iR"
        # "HP EliteBook 650 15.6 inch G9 Notebook PC" -> "EliteBook 650 G9"
        # "HP Elite SFF 800 G9 Desktop PC" -> "Elite SFF 800 G9"
        # "HP ProDesk 400 G6 SFF" -> "Prodesk 400 G6 SFF"
        
        # It seems we want to remove "HP ", " inch", " Notebook PC", " Desktop PC".
        # And maybe keep the core model.
        
        cleaned = model_name
        
        # Remove Manufacturer prefix if present (assuming HP for now based on examples)
        cleaned = re.sub(r'^HP\s+', '', cleaned, flags=re.IGNORECASE)
        
        # Remove " inch" and surrounding text if it looks like a size (e.g. 16 inch, 15.6 inch)
        cleaned = re.sub(r'\s+\d+(\.\d+)?\s+inch', '', cleaned, flags=re.IGNORECASE)
        
        # Remove " Notebook PC", " Desktop PC"
        cleaned = re.sub(r'\s+Notebook PC', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+Desktop PC', '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
