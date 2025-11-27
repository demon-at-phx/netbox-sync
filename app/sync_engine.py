from app.connectors.netbox_connector import NetboxConnector
from app.connectors.pdq_connector import PDQConnector
from app.utils import slugify

class SyncEngine:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.netbox = NetboxConnector(config, logger)
        self.pdq = PDQConnector(config, logger)

    def run_sync(self):
        # 1. Connect to Netbox and fetch baseline
        if not self.netbox.check_connection():
            self.logger.critical("Aborting sync due to Netbox connection failure.")
            return

        # 2. Fetch Source Data
        pdq_devices = self.pdq.fetch_devices()
        if not pdq_devices:
            self.logger.warning("No devices fetched from PDQ. Skipping sync.")
            return

        # 3. Compare and Sync
        self._sync_devices(pdq_devices)

    def _sync_devices(self, source_devices):
        # Index Netbox assets by serial for O(1) lookup
        netbox_assets_by_serial = {
            a['serial']: a for a in self.netbox.assets 
            if a.get('serial') # Only index assets with serials
        }

        # Index Netbox manufacturers by name
        netbox_manufacturers = {
            m['name'].lower(): m for m in self.netbox.manufacturers
        }

        # Index Netbox item types by model
        netbox_item_types = {
            t['model'].lower(): t for t in self.netbox.item_types
        }

        # Track processed serials to find retirements
        processed_serials = set()

        for device in source_devices:
            serial = device['serial']
            if not serial:
                self.logger.warning(f"Device {device['name']} has no serial. Skipping.")
                continue

            processed_serials.add(serial)
            
            # Ensure Manufacturer exists
            manufacturer_name = device['manufacturer'] or "Unknown"
            manufacturer = netbox_manufacturers.get(manufacturer_name.lower())
            
            if not manufacturer:
                # Create Manufacturer
                self.logger.info(f"Creating Manufacturer: {manufacturer_name}")
                slug = slugify(manufacturer_name)
                manufacturer = self.netbox.create_manufacturer(manufacturer_name, slug)
                if manufacturer:
                    netbox_manufacturers[manufacturer_name.lower()] = manufacturer
                else:
                    self.logger.error(f"Failed to create manufacturer {manufacturer_name}. Skipping device {serial}.")
                    continue

            # Ensure Item Type (Model) exists
            model_name = device['model']
            item_type = netbox_item_types.get(model_name.lower())
            
            if not item_type:
                # Create Item Type
                self.logger.info(f"Creating Item Type: {model_name}")
                slug = slugify(model_name)
                payload = {
                    'manufacturer': {'name': manufacturer['name']}, # Netbox might need ID or nested object depending on version/plugin. SRS says nested name.
                    'model': model_name,
                    'slug': slug,
                    'description': device['raw_model'] # Use raw model as description
                }
                item_type = self.netbox.create_item_type(payload)
                if item_type:
                    netbox_item_types[model_name.lower()] = item_type
                else:
                    self.logger.error(f"Failed to create item type {model_name}. Skipping device {serial}.")
                    continue

            # Sync Asset
            existing_asset = netbox_assets_by_serial.get(serial)
            
            asset_payload = {
                'name': device['name'],
                'description': device['raw_model'],
                'status': 'used',
                'serial': serial,
                'manufacturer': {'name': manufacturer['name']},
                'hardware_kind': 'inventoryitem', # SRS payload example
                'inventoryitem_type': {'model': model_name}
            }

            if not existing_asset:
                # CREATE
                self.logger.info(f"Creating Asset: {serial} ({device['name']})")
                self.netbox.create_asset(asset_payload)
            else:
                # UPDATE
                # Check for changes (simplified check)
                needs_update = False
                if existing_asset.get('name') != device['name']:
                    needs_update = True
                if existing_asset.get('status') != 'used':
                    needs_update = True
                
                if needs_update:
                    self.logger.info(f"Updating Asset: {serial}")
                    self.netbox.update_asset(existing_asset['id'], asset_payload)

        # RETIRE MISSING ASSETS
        # Only retire assets that are in Netbox but not in Source
        # AND are of a type we manage (e.g. have a serial).
        # SRS: "Does serial exist in Source Data? NO: Add to To_Retire list."
        
        for serial, asset in netbox_assets_by_serial.items():
            if serial not in processed_serials:
                if asset.get('status') != 'retired':
                    self.logger.info(f"Retiring Asset: {serial}")
                    self.netbox.update_asset(asset['id'], {'status': 'retired'})
