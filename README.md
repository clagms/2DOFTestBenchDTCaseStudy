# 2 DOF Testbench Digital Twin Stack (RabbitMQ + InfluxDB)

This repository contains the Digital Twin Framework for the 2DoF TestBench owned and maintained by Giuseppe Abbiati, in collaboration with Ecem and Claudio.

- [2 DOF Testbench Digital Twin Stack (RabbitMQ + InfluxDB)](#2-dof-testbench-digital-twin-stack-rabbitmq--influxdb)
  - [Overview](#overview)
  - [Prerequisites](#prerequisites)
  - [First Time Setup](#first-time-setup)
  - [Running the DT (After Setup)](#running-the-dt-after-setup)
  - [Docker-Compose Explanation](#docker-compose-explanation)
  - [Configuration](#configuration)
  - [Test Scripts](#test-scripts)
  - [Operations](#operations)
  - [Troubleshooting](#troubleshooting)


## Overview

- Docker Compose (`docker-compose.yml`) brings up 3 **core services**:
  - RabbitMQ (AMQP + MQTT + Management UI)
  - InfluxDB 2.x (time-series database)
  - The testbench server, that can respond to commands to move the actuators and get sensor readings.
- Python smoke tests:
  - `rabbitmq/test_rabbitmq.py` publishes and retrieves a message via a local queue.
  - `influxdb/test_influxdb.py` writes 10 points and queries them back using Flux.
- Central configuration: [startup.conf](startup.conf) (application, copied from [startup_template.conf](startup_template.conf)) and [logging.conf](logging.conf) (logging).

## Prerequisites

- Docker Desktop with Compose v2
- Python 3.11 (virtual environment recommended)
- Open ports:
  - RabbitMQ: 5672 (AMQP), 15672 (Mgmt UI), 1883 (MQTT)
  - InfluxDB: 8086 (API), 8088 (RPC)

## First Time Setup

1) Create `startup.conf`: Copy [startup_template.conf](startup_template.conf) and rename the copy to [startup.conf](startup.conf).

2) Start core services
    
    ```bash
    docker compose up --build -d
    docker compose ps
    ```

    You should see this:

    ```bash
    PS C:\work\github\2DOFTestBenchDTCaseStudy> docker compose ps
    NAME               IMAGE       COMMAND                  SERVICE     CREATED          STATUS                    PORTS
    influxdb-server    influxdb    "/entrypoint.sh infl…"   influxdb    20 seconds ago   Up 20 seconds             0.0.0.0:8086->8086/tcp, [::]:8086->8086/tcp, 0.0.0.0:8088->8088/tcp, [::]:8088->8088/tcp
    mockupbin-server   mockupbin   "./TestBenchAUCAE2Do…"   mockupbin   20 seconds ago   Up 14 seconds
    rabbitmq-server    rabbitmq    "docker-entrypoint.s…"   rabbitmq    20 seconds ago   Up 20 seconds (healthy)   0.0.0.0:1883->1883/tcp, [::]:1883->1883/tcp, 0.0.0.0:5672->5672/tcp, [::]:5672->5672/tcp, 0.0.0.0:15672->15672/tcp, [::]:15672->15672/tcp
    ```

3) Create a Python virtual environment and install dependencies
    
    Windows (PowerShell):
    
    ```
    python -m venv .venv
    ./.venv/Scripts/Activate.ps1
    pip install -r requirements.txt
    ```
    
    Linux/macOS:
    
    ```
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

4) Run smoke test for influxDB:
    
    ```
    python -m influxdb.test_influxdb
    ```
    
    If you get an **unauthorized access error**, you probably need to update the access `token` in the [startup.conf](startup.conf)generated from the [management page](http://localhost:8086/). Follow [this guide](https://docs.influxdata.com/influxdb/cloud/admintokens/create-token/), and use the credentials, org, and bucket as in the [startup.conf](startup.conf).
    
    After running the script you should see some data generated in the influxdb page, and the following output:
    
    ```bash
    Sending 10 data points to influxdb...
    test-data,source=test-script test-field=0.5673840337333702 1762594986950114000
    ...
    test-data,source=test-script test-field=0.533298928538687 1762594987998678000
    Sent 10 data points to influxdb.
    Reading 10 data points from influxdb...
    Query used:
    
      from(bucket: "testbench")
          |> range(start: -10h, stop: now())
          |> filter(fn: (r) => r["_measurement"] == "test-data")
          |> filter(fn: (r) => r["_field"] == "test-field")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    
                              _time  test-field
    0 2025-11-08 09:42:58.581577+00:00    0.943441
    ...
    9 2025-11-08 09:43:07.998678+00:00    0.533299
    Read 10 data points from influxdb.
    ```

5) Test the RabbitMQ instance:

    ```
    python -m rabbitmq.test_rabbitmq
    ```

    You should see the following output:

    ```bash
    2025-11-08 10:43:59.082 DEBUG RabbitMQClass : Connected.
    2025-11-08 10:43:59.091 INFO RabbitMQClass : Bound test--> amq.gen-pFcT3o-kgut3T2ev1W2lvA
    Sending message...
    2025-11-08 10:43:59.091 DEBUG RabbitMQClass : Message sent to test.
    2025-11-08 10:43:59.091 DEBUG RabbitMQClass : {'text': '321'}
    Message sent.
    Retrieving message.2025-11-08 10:43:59.135 DEBUG RabbitMQClass : Received message is b'{"text": "321"}' <Basic.GetOk(['delivery_tag=1', 'exchange=TestBench_AMQP', 'message_count=0', 'redelivered=False', 'routing_key=test'])> <BasicProperties>
    Received message is {'text': '321'}
    2025-11-08 10:43:59.135 DEBUG RabbitMQClass : Deleting created queues by Rabbitmq class
    2025-11-08 10:43:59.136 DEBUG RabbitMQClass : Deleting queue:amq.gen-pFcT3o-kgut3T2ev1W2lvA
    2025-11-08 10:43:59.143 DEBUG RabbitMQClass : Closing channel in rabbitmq
    2025-11-08 10:43:59.144 DEBUG RabbitMQClass : Closing connection in rabbitmq
    2025-11-08 10:43:59.145 DEBUG RabbitMQClass : Connection closed.
    2025-11-08 10:43:59.150 DEBUG RabbitMQClass : Deleting queues, close channel and connection
    2025-11-08 10:43:59.151 DEBUG RabbitMQClass : Connection closed.
    ```

6) Check the logs of the testbench server:

    ```bash
    docker logs mockupbin-server
    ```

    You should see something like:
    ```bash
    Failed to load dynlib/dll '/opt/indel/lib/libinco_32.so'. Most likely this dynlib/dll was not found when the application was frozen.
    inco32 driver not installed
    ::on
    forward kinematics iteration 0 residual norm 0.0
    forward kinematics iteration 0 residual norm 0.0
    Initial Position Joint Space: [0. 0.]
    Initial Force Joint Space: [0. 0.]
    Initial Position Task Space: [0. 0.]
    Initial Force Task Space: [0. 0.]
    2026-01-25 06:28:25.860 INFO TestBenchAUCAE2DofRMQServer : Connecting to rabbitmq server and setting up TestBenchAUCAE2DofRMQServer...
    ...
    2026-01-25 06:28:28.880 DEBUG TestBenchAUCAE2DofRMQServer : Ready to listen for msgs in queue TestBenchAUCAE2DofRMQServerQueue bound to topic TestBenchAUCAE2DofRMQServerRoutingKey
    2026-01-25 06:28:28.880 INFO TestBenchAUCAE2DofRMQServer : TestBenchAUCAE2DofRMQServer setup complete. Ready to serve.
    ```

## Running the DT (After Setup)

1) Start core services if you haven't started them.
   
    ```bash
    docker compose up --build -d
    docker compose ps
    ```

    You should see this:

    ```bash
    NAME               IMAGE       COMMAND                  SERVICE     CREATED         STATUS                   PORTS
    influxdb-server    influxdb    "/entrypoint.sh infl…"   influxdb    6 minutes ago   Up 6 minutes             0.0.0.0:8086->8086/tcp, [::]:8086->8086/tcp, 0.0.0.0:8088->8088/tcp, [::]:8088->8088/tcp
    mockupbin-server   mockupbin   "./TestBenchAUCAE2Do…"   mockupbin   6 minutes ago   Up 6 minutes
    rabbitmq-server    rabbitmq    "docker-entrypoint.s…"   rabbitmq    6 minutes ago   Up 6 minutes (healthy)   0.0.0.0:1883->1883/tcp, [::]:1883->1883/tcp, 0.0.0.0:5672->5672/tcp, [::]:5672->5672/tcp, 0.0.0.0:15672->15672/tcp, [::]:15672->15672/tcp
    ```

2) The notebook [TestBenchAUCAE2DofRMQServer_dev.ipynb](TestBenchAUCAE2DofRMQServer_dev.ipynb) shows a series of interactions with the DT services. 


## Docker-Compose Explanation

Starts up three containers:
-   rabbitmq: Builds from rabbitmq/ while tagging as rabbitmq, exposes AMQP/MQTT/management ports 5672, 15672, 1883; healthcheck pings the broker with generous retries/start period.
-   influxdb: Builds from influxdb/ with tag influxdb, exposes HTTP/line protocol ports 8086, 8088; persists data via bind mount ./influxdb/ -> /var/lib/influxdb/.
-   mockupbin: Builds from Dockerfile.server at repo root, tagged mockupbin; waits for rabbitmq to be healthy before starting.

## Configuration

- Application config: `startup.conf`
  - rabbitmq: host, port, vhost `/`, exchange `TestBench_AMQP`, type `topic`, credentials (`TestBench2DOF` / `12345678`)
  - influxdb: `url`, `org`, `bucket`, and an access token suitable for the seeded local volume
- Logging: `logging.conf` (logs to console and `log.log`)
- Resource lookup: `config/config.py` searches `PYTHONPATH` and `.` for files; run from repo root or set `PYTHONPATH=.`

## Test Scripts

- `rabbitmq/test_rabbitmq.py`
  
  - Loads RabbitMQ settings from `startup.conf`
  - Declares a temporary local queue, publishes a JSON message to routing key `test`, then polls and prints the received message

- `influxdb/test_influxdb.py`
  
  - Loads InfluxDB settings from `startup.conf`
  - Writes 10 points to measurement `test-data` and queries them back with a Flux pipeline

Optional RPC utilities for advanced usage:

- `rabbitmq/rpc_server.py` and `rabbitmq/rpc_client.py` implement a simple RPC pattern on top of AMQP (correlation IDs and reply queues).

## Operations

- View and follow container logs
  
  ```
  docker logs -f rabbitmq-server
  docker logs -f influxdb-server
  docker logs -f mockupbin-server
  ```

- Stop stack
  
  ```
  docker compose down
  ```

- Rebuild images and restart
  
  ```
  docker compose build --no-cache
  docker compose up -d
  ```

- Reset InfluxDB data (destructive)
  
  ```
  docker compose down
  # Remove contents of the local influxdb/ directory (e.g., influxd.bolt, engine/)
  # Then bring services back up
  docker compose up -d
  ```

## Troubleshooting

- Ports already in use: adjust mappings in `docker-compose.yml` or free the ports.
- Config not found: run from repo root or set `PYTHONPATH=.`
- InfluxDB auth/query issues: ensure `url`, `org`, `bucket`, and token in `startup.conf` match your local data volume.
- RabbitMQ auth errors: verify `rabbitmq/rabbitmq.conf` matches `startup.conf`; rebuild the image if you change defaults.

