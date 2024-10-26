# Error Logs Solutions Suggestions using Gen AI

Provide Suggestions to solve the errors in logs using the Gen AI.

## Table of Contents

* [Overview](#overview)
* [Installation](#installation)
* [Usage](#usage)
* [Scaling](#scaling)


## Overview

This project employs a prompt-based architecture, utilizing a large language model (LLM) for log analysis.  Input logs are fed to the LLM, which extracts relevant log messages, removing noise like timestamps and log levels.  The extracted messages are then analyzed by the model to determine the root cause, suggest solutions, and provide further guidance.

The system comprises two modules:

* `server.py`: Hosts the LLM, extracts log messages, and prompts the model for analysis. It uses an asynchronous queue to handle multiple requests concurrently, processing them in FIFO order. The server streams the LLM's generated output to the client.
* `client.py`: Sends input logs and generation parameters to the server via an API endpoint.  This script can be used to read log files and transmit their contents to the server.

The server's streaming output can be modified on the client-side to display the full response instead of streaming individual words.

The code is formatted using Black for readability.

## Installation

This project supports Python 3.11 for both client and server.

### Server Installation

1. **Install Server Dependencies:**

   ```bash
   python3 -m pip install -r server_requirements.txt
   ```

2. **Run the Server:** Use Uvicorn, a production-ready ASGI server, to run the application.

   ```bash
   uvicorn server:app --port 9300 --host 0.0.0.0 
   ```
   This command starts the server on port 9300, making it accessible from any network interface (`0.0.0.0`).


### Client Installation

1. **Install Client Dependencies:**

   ```bash
   python3 -m pip install -r client_requirements.txt
   ```

2. **Configuration:**  Place the `client_config.yaml` configuration file in the same directory as `client.py`.  This file should contain necessary settings for connecting to the server (e.g., host and port).  

The client only requires the `pyaml` library to read the configuration file, it can rather be hardcoded but not recommended best practice for production.

3. **Run the Client:**

   ```bash
   python3 client.py
   ```

# Usage

Configure model and generation parameters within the respective YAML configuration files for the server and client.

Recommended Models:

Larger models generally yield better results. The following are recommended:
- `meta-llama/Llama-3.2-8B-Instruct`
- `meta-llama/Llama-3.2-70B-Instruct`
- `mistralai/Ministral-8B-Instruct-2410`

**Make sure to add your access token in the `server_config.yaml` when using the gated model**

**Providing Context**: For optimal performance, provide more than 5 log entries to give the model sufficient context. This leads to more accurate analysis and better suggestions.


## Client Interaction:

Upon execution, the client will prompt the user to input the logs they wish to analyze. Copy and paste the relevant log entries into the console.

```bash
$ python3 client.py
INPUT: Dec 10 06:55:46 LabSZ sshd[24200]: Invalid user webmaster from 173.234.31.186
Dec 10 06:55:46 LabSZ sshd[24200]: input_userauth_request: invalid user webmaster [preauth]
Dec 10 06:55:46 LabSZ sshd[24200]: pam_unix(sshd:auth): check pass; user unknown
Dec 10 06:55:46 LabSZ sshd[24200]: pam_unix(sshd:auth): authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost=173.234.31.186 
Dec 10 06:55:48 LabSZ sshd[24200]: Failed password for invalid user webmaster from 173.234.31.186 port 38926 ssh2
Dec 10 06:55:48 LabSZ sshd[24200]: Connection closed by 173.234.31.186 [preauth]
Dec 10 07:02:47 LabSZ sshd[24203]: Connection closed by 212.47.254.145 [preauth]
```

```bash
======================================== Log Analysis ======================================== 

**Analysis of Log Data**

Based on the provided log data, the main application or service that appears to be having problems is **RAS KERNEL**.

**Key Exceptions:**

1. **RAS_KERNEL INFO instruction cache parity error corrected**: This indicates that the application is experiencing a cache parity error, which is a critical error that can cause significant performance issues.
2. **RAS_KERNEL INFO double-hummer alignment exceptions**: These exceptions suggest that the application is encountering issues related to double-hummer alignment, which is a critical alignment error that can cause performance issues.

**Root Cause Analysis:**

Based on the log data, it appears that the application is experiencing a cache parity error and double-hummer alignment exceptions. The root cause of this issue is likely related to the **RAS_KERNEL** configuration, specifically the **instruction cache** and **double-hummer alignment** settings.

**Remedial Actions:**

To resolve the issue, the following remedial actions can be taken:

1. **Adjust instruction cache settings**: Adjust the instruction cache settings to reduce the number of cache misses and improve performance.
2. **Optimize double-hummer alignment**: Optimize the double-hummer alignment settings to improve performance.
3. **Verify cache configuration**: Verify that the cache configuration is correct and up-to-date.
4. **Update RAS_KERNEL configuration**: Update the RAS_KERNEL configuration to reflect the latest performance improvements.
5. **Monitor cache performance**: Monitor cache performance to ensure that the application is not experiencing excessive cache misses.

**Additional Details:**

* The application is running on a 32-bit operating system.
* The application is using a 64-bit kernel.
* The application is experiencing performance issues in the instruction cache.
* The double-hummer alignment exceptions are occurring in the instruction cache.

**Preventative Measures:**

To avoid this issue from recurring in the future, the following preventative measures can be taken:

1. **Regularly update the operating system and kernel**: Regularly update the operating system and kernel to ensure that you have the latest performance improvements.
2. **Monitor cache performance**: Monitor cache performance regularly to ensure that the application is not experiencing excessive cache misses.
3. **Adjust instruction cache settings**: Adjust the instruction cache settings to reduce the number of cache misses and improve performance.
4. **Optimize double-hummer alignment**: Optimize the double-hummer alignment settings to improve performance.
5. **Verify cache configuration**: Verify that the cache configuration is correct and up-to-date.

**Additional Notes:**

* The log data indicates that the application is experiencing performance issues in the instruction cache and double-hummer alignment.
* The application is using a 64-bit kernel, which may be a contributing factor to the performance issues.
* The log data does not provide sufficient information to identify the exact cause of the performance issues. Further investigation is required to determine the root cause of the issue.
======================================== Finished ======================================== 
```

The intended usage is only for analyzing the log. Any other type of input may give inaccurate results.

## Scaling

The model is server-hosted, allowing for containerization using Docker. An automated script can build the Docker image and run the service within the container.

## Future Work

* **Scaling with Kubernetes:**  As request volume increases, Kubernetes can be employed to automate the deployment of multiple containers, ensuring responsiveness and availability.

* **Optimized Log Processing for Language Model Integration:**  If comprehensive log analysis via the language model is desired, the following strategy can be adopted:

    1. **Log Parsing:** Utilize methods from the `logpai/logparser` repository to extract structured log messages.

    2. **Error Filtering:** Employ zero-shot classification to filter logs.  Analyze only those classified as errors, excluding "info" and "warning" messages. This reduces the language model's workload.

    3. **Contextual Enrichment:** Provide the language model with 10-20 preceding log entries alongside the error log. This added context enhances analysis and generates more plausible solutions, minimizing hallucinations.
