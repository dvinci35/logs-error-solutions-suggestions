# Error Logs Solutions Suggestions using Gen AI

Provide Suggestions to solve the errors in logs using the Gen AI.

## Table of Contents

* [Overview](#overview)
* [Installation](#installation)
* [Usage](#usage)
* [Scaling](#scaling)


## Overview

This project employs a prompt-based architecture, utilizing a large language model (LLM) for log analysis. Input logs are fed to the LLM, which extracts relevant log messages, removing noise like timestamps and log levels.  The extracted messages are then analyzed by the model to determine the root cause, suggest solutions, and provide further guidance.

The system comprises two modules:

* `server.py`: Hosts the LLM, extracts log messages, and prompts the model for analysis. It uses an asynchronous queue to handle multiple requests concurrently, processing them in FIFO order. The server streams the LLM's generated output to the client.
* `client.py`: Sends input logs and generation parameters to the server via an API endpoint.  This script can be used to read log files and transmit their contents to the server.

The server's streaming output can be modified on the client-side to display the full response instead of streaming individual words.

The code is formatted using Black for readability.

The server container uses Models available freely on Huggingface. You need a huggingface account to access gated open-source models.

The code was test on 4GB RTX3050 laptop GPU and operating system is Ubuntu 24.04.1.

Two models were used for testing purposes:
- `meta-llama/Llama-3.2-1B-Instruct`
- `microsoft/Phi-3.5-mini-instruct`

**UPDATES:**
- Previously the the modules were stand-alone. Now the code to build and run the container is provided and whole project can be used as is in production (if the intended use case can be fulfilled.)
- The server will use the model quantization if the gpu is available otherwise it will load the model in gpu (assuming a non-quantized model path/name is provided.)

## Installation

This project supports Python 3.11 for both client and server.

### Server Installation

**UPDATED INSTRUCTIONS:**
1. **Install the docker** using the [official documentation](https://docs.docker.com/engine/install/). The testing system is ubuntu 24.04.1 LTS

2. If you have GPU enabled system, then to use the gpu in docker container make sure to install docker cuda toolkit from the [official documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

<!-- 1. **Install Server Dependencies:**

   ```bash
   python3 -m pip install -r server_requirements.txt
   ```

2. **Run the Server:** Use Uvicorn, a production-ready ASGI server, to run the application.

   ```bash
   uvicorn server:app --port 9300 --host 0.0.0.0 
   ```
   This command starts the server on port 9300, making it accessible from any network interface (`0.0.0.0`). -->


### Client Installation

The testing system is ubuntu 24.04.1 LTS, and the python version is 3.11

1. **Install Client Dependencies:**

   ```bash
   python3 -m pip install -r client/client_requirements.txt
   ```

2. **Configuration:**  Place the `client_config.yaml` configuration file in the same directory as `client.py`.  This file should contain necessary settings for connecting to the server (e.g., host and port). 

   The client only requires the `pyaml` library to read the configuration file. The configurations can rather be hardcoded but not recommended best practice for production.

# Usage

**Updated Instructions**: 

Configure model and generation parameters within the [`server_config.yaml`](server-container/app/server_config.yaml) and Port to be exposed in the [`Dockerfile`](./server-container/Dockerfile)

**Make sure to add your access token when using the gated model**

```yaml
chat_completion_model_params:
   token: your_token_here
```

**Recommended Models:** Larger models generally yield better results. The following are recommended:
- `meta-llama/Llama-3.2-8B-Instruct`
- `meta-llama/Llama-3.2-70B-Instruct`
- `mistralai/Ministral-8B-Instruct-2410`

## Building and running the server image
- **To Build the Server Image**:

   Change the configurations in the [`server_config.yaml`](server-container/app/server_config.yaml) file to modify as per requirements. 

   The server will be hosted on the port `9300`. To change it modify in [`Dockerfile`](server-container/Dockerfile)
   The docker container will install all the dependencies required to run the server.
   ```bash
   cd server-container/
   docker build -t inf:inf .
   ```

- **To run the server image:**

   Run the following command to run the server container:
   ```
   docker run --gpus all -p 9300:9300 inf:inf
   ```

## Client Interaction:

Make sure to write the correct **Host name** and **port number** in the [client configurations](client/client_config.yaml)

To run the client simply execute the following command:

```bash
cd client/
python3 client.py
```

Upon execution, the client will prompt the user to input the logs they wish to analyze. Copy and paste the relevant log entries into the console.

**Providing Context**: For optimal performance, provide more than 5 log entries to give the model sufficient context. This leads to more accurate analysis and better suggestions.

```bash
python3 client.py
INPUT: Dec 10 06:55:46 LabSZ sshd[24200]: Invalid user webmaster from 173.234.31.186\nDec 10 06:55:46 LabSZ sshd[24200]: input_userauth_request: invalid user webmaster [preauth]\nDec 10 06:55:46 LabSZ sshd[24200]: pam_unix(sshd:auth): check pass; user unknown\nDec 10 06:55:46 LabSZ sshd[24200]: pam_unix(sshd:auth): authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost=173.234.31.186 \nDec 10 06:55:48 LabSZ sshd[24200]: Failed password for invalid user webmaster from 173.234.31.186 port 38926 ssh2\nDec 10 06:55:48 LabSZ sshd[24200]: Connection closed by 173.234.31.186 [preauth]\nDec 10 07:02:47 LabSZ sshd[24203]: Connection closed by 212.47.254.145 [preauth]
```


The ouput is similar to the following:
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
