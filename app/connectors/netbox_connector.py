import requests
import time

class NetboxConnector:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.base_url = config.get('Netbox', 'url').rstrip('/')
        self.token = config.get('Netbox', 'token')
        self.headers = {
            'Authorization': f'Token {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.manufacturers = {}
        self.item_types = {}
        self.assets = {}

    def check_connection(self):
        """Checks connection to Netbox and fetches baseline data."""
        try:
            self.logger.info("Connecting to Netbox...")
            # Fetch Manufacturers
            self.manufacturers = self._fetch_all('dcim/manufacturers/')
            self.logger.info(f"Fetched {len(self.manufacturers)} Manufacturers")

            # Fetch Inventory Item Types
            self.item_types = self._fetch_all('plugins/inventory/inventory-item-types/')
            self.logger.info(f"Fetched {len(self.item_types)} Inventory Item Types")

            # Fetch Assets
            self.assets = self._fetch_all('plugins/inventory/assets/')
            self.logger.info(f"Fetched {len(self.assets)} Assets")
            
            return True
        except Exception as e:
            self.logger.critical(f"Failed to connect to Netbox: {e}")
            return False

    def _fetch_all(self, endpoint):
        """Helper to fetch all records handling pagination."""
        results = []
        url = f"{self.base_url}/api/{endpoint}"
        
        while url:
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                results.extend(data.get('results', []))
                url = data.get('next')
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error fetching {endpoint}: {e}")
                raise e
        
        # Index by ID or other unique field if needed, but for now returning list
        # Actually, for easier lookup, let's index them.
        # But for now, let's just return the list and process it in the sync engine or here.
        # The SRS says "Cache data in Python Dictionary". 
        # Let's index by a useful key.
        
        return results

    def get_manufacturer_by_name(self, name):
        for m in self.manufacturers:
            if m['name'].lower() == name.lower():
                return m
        return None

    def create_manufacturer(self, name, slug):
        payload = {'name': name, 'slug': slug}
        return self._post('dcim/manufacturers/', payload)

    def create_item_type(self, payload):
        return self._post('plugins/inventory/inventory-item-types/', payload)

    def create_asset(self, payload):
        return self._post('plugins/inventory/assets/', payload)

    def update_asset(self, asset_id, payload):
        return self._patch(f'plugins/inventory/assets/{asset_id}/', payload)

    def _post(self, endpoint, payload):
        url = f"{self.base_url}/api/{endpoint}"
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error creating record at {endpoint}: {e}")
            if response is not None:
                 self.logger.error(f"Response content: {response.text}")
            return None

    def _patch(self, endpoint, payload):
        url = f"{self.base_url}/api/{endpoint}"
        try:
            response = requests.patch(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error updating record at {endpoint}: {e}")
            if response is not None:
                 self.logger.error(f"Response content: {response.text}")
            return None
