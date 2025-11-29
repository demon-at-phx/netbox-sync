# Netbox-PDQ Sync

This application synchronizes IT asset data from PDQ Connect into Netbox. It is designed as a stateless, modular ETL pipeline that runs periodically to keep Netbox updated with the latest asset information from PDQ.

## Architecture

The application is composed of the following key components:

- **`main.py`**: The entry point of the application. It loads the configuration, sets up logging, and runs the main synchronization loop.
- **`app/settings.py`**: Handles loading and validation of the `config.ini` file.
- **`app/logger.py`**: Configures the logging for the application, including the option to send logs to an external syslog server.
- **`app/sync_engine.py`**: The core of the application. It orchestrates the synchronization process by fetching data from PDQ, comparing it with the data in Netbox, and then creating, updating, or retiring assets in Netbox as needed.
- **`app/connectors/pdq_connector.py`**: A dedicated module for interacting with the PDQ Connect API. It handles fetching and processing device data from PDQ.
- **`app/connectors/netbox_connector.py`**: A dedicated module for interacting with the Netbox API. It manages fetching baseline data from Netbox and creating, updating, and retiring assets.
- **`app/utils.py`**: Contains utility functions, such as `slugify`, used across the application.

The application operates in a loop, with each cycle performing the following steps:

1.  **Connect to Netbox**: Establishes a connection to the Netbox API and fetches the current state of all assets, manufacturers, and item types. This data is cached in memory for the duration of the sync cycle.
2.  **Fetch from PDQ**: Connects to the PDQ Connect API and fetches a complete list of all devices.
3.  **Compare and Sync**: The `SyncEngine` compares the list of devices from PDQ with the assets in Netbox based on their serial numbers.
    -   **New Devices**: If a device from PDQ does not exist in Netbox, a new asset is created. If the manufacturer or item type (model) of the device does not exist in Netbox, they are created first.
    -   **Existing Devices**: If a device from PDQ already exists in Netbox, the application checks for any differences and updates the asset information in Netbox if necessary.
    -   **Retired Devices**: Any assets that exist in Netbox but are no longer present in the data from PDQ are marked as "retired" in Netbox.

## Configuration

To run the application, you must first create a `config.ini` file. You can do this by copying the `config.ini.example` file and modifying it with your specific settings.

```bash
cp config.ini.example config.ini
```

The following are the minimum settings that need to be configured in the `config.ini` file:

```ini
[General]
sync_interval = 3600

[Netbox]
url = https://your-netbox-instance.com
token = YOUR_NETBOX_API_TOKEN

[PDQ]
url = https://app.pdq.com
token = YOUR_PDQ_API_TOKEN
```

-   **`sync_interval`**: The time in seconds between each synchronization cycle.
-   **`[Netbox] url`**: The URL of your Netbox instance.
-   **`[Netbox] token`**: Your Netbox API token.
-   **`[PDQ] url`**: The URL of your PDQ Connect instance.
-   **`[PDQ] token`**: Your PDQ Connect API token.

## Installation and Usage

### 1. Create a Python Virtual Environment

It is recommended to run the application in a Python virtual environment to manage its dependencies separately.

```bash
# Create the virtual environment
python3 -m venv .venv
```

### 2. Activate the Virtual Environment

Before installing the dependencies or running the application, you need to activate the virtual environment.

-   On **macOS** and **Linux**:

    ```bash
    source .venv/bin/activate
    ```

-   On **Windows**:

    ```bash
    .venv\Scripts\activate
    ```

### 3. Install the Requirements

With the virtual environment activated, you can now install the required Python packages.

```bash
pip install -r requirements.txt
```

### 4. Run the Application

Once the dependencies are installed and the `config.ini` file is configured, you can run the application with the following command:

```bash
python3 main.py
```
