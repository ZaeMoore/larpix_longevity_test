LarPix Longevity Test Scripts
Authors: Marina Reggiani-Guzzo, Zae Moore (Syracuse University)

# Initial requirements

You should have the following files in your directory:

- Install virtual environment with all packages:
  ```
  python3 -m venv my_new_env
  source my_new_env/bin/activate
  pip install -r /path/to/requirements.txt
  ```

- `.token`. It is a file that simply contains the grafana-cloud token.

- `influxdb_config.py`. This is a python script with the following variables: `token`, `ORG`, `url` and `BUCKET`, which are all information about your InfluxDB database.
  ```
  # influxdb_config.py
  token = "my_token"
  ORG = "my_org"
  url = "my_url"
  BUCKET = "my_bucket"
  ```
  This information is then retrieved in scripts using InfluxDB as follows:
  ```
  from influxdb_config import token, ORG, url, BUCKET
  ```

# Files in the repository

Find below a brief description of the files in this repository:

- `calculate_power_on_command.py`. This script calculates the necessary applied --vdda and --vddd for a desired readout
VDDA and VDDD, for either nominal or accelerated mode.

- `failure_test.py`. This script compares the latest V_pedestal, readout IDDD and IDDA and compare them to the baseline ones, collected at the beginning of the longevity test. The percentual value is then saved to the InfluxDB database.

- `monitor_compressor.py`. This script retrieves information from the compressor and saves it to a database. Please make sure the compressor is connected to the network, otherwise the connection to the computer cannot be established -- this is often done by forwarding the network from the computer via an ethernet cable.

- `monitor_ctc100.py`. This script retrieves information from the ctc100 device and saves it to a database. Please make sure the usb port used by the ctc100 device is set to executable, otherwise the connection to the computer cannot be established.

- `monitor_labjack.py`. This script retrieves information from the labjack device and saves it to a database.

- `monitor_larpix_readout.py`. This script is called by run_longevity_test.py and records the actual data values from the larpix boards and calls on the failure test script.

- `measure_baseline.py`. This script collects the vddd, vdda, iddd and idda for all pacman tiles, as well as the mean pedestal and the number of packets of each channel. The information is then saved into a dictionary, an influxdb database, or both. Read description for more information.

- `requirements.txt`. This is a list of packages installed in the virtual environment. Follow steps under "Initial requirements" to correctly set up the environment.

- `run_longevity_test.py`. This script is responsible for actually performing the longevity test throughout its duration. It sets the required voltages when necessary, it collects the information from the LArPIX boards and the vital signals from the rest of the system, and it performs the failure tests. This script should be running all the time!

- `start_grafana_cloud.sh`. This script starts the grafana-cloud server.

- `syracuse_start_monitoring_all_variables.sh`. This script starts the scripts that collect information from the compressor, ctc100, and labjack.

# How to run scripts

1. **Network to compressor**. The very first thing is to make sure that the compressor is receiving network connection. Go to "wired connections" and check if the network is active for compressor. Then, physically disconnect the usb cable leading to the compressor, wait 5 seconds, and connect it again. The network connection should have been established by now.

2. **Run script to collect data**.
    - **Automated path**: In principle you should be able to simply run the script below. It will start influxdb, grafana-cloud server and run the scripts that collect information from compressor, ctc100 and labjack, each one in a different terminal.
      ```
      source syracuse_start_monitoring_all_variables.sh
      ```

    - **Manually**: if you want to run the scripts for the compressor, ctc100 and labjack individually, do the following.

      Make sure grafana-cloud and influxdb-server is active
      ```
      source start_grafana_cloud.sh
        
      sudo systemctl start influxdb
      sudo systemctl enable influxdb
      ```
      Then, open three different terminals:
      ```
      # on terminal 1
      source /home/syr-neutrino/Desktop/Longevity_Test/larpix/bin/activate
      sudo chmod a+rw /dev/ttyUSB0
      python3 monitor_compressor.py
        
      # on terminal 2
      source /home/syr-neutrino/Desktop/Longevity_Test/larpix/bin/activate
      python3 monitor_labjack.py
        
      # on terminal 3
      source /home/syr-neutrino/Desktop/Longevity_Test/larpix/bin/activate
      python3 monitor_ctc100.py
      ```


3. **Run script to collect data and perform failure tests**. You should be able to run run_longevity_test.py and it will automatically collect data and evaluate failure tests for as long as it is running. If a tile fails one of the failure tests, all tiles will be turned off and only the healthy ones will be turned back on.
    - python3 run_longevity_test.py
