# Benchmark VPS Machines: An Ansible Playbook and Python Script

## Overview

This repository contains an Ansible playbook and an accompanying Python script designed to benchmark a cluster of VPS (Virtual Private Server) nodes. The benchmarking suite tests multiple system components, including CPU, memory, file I/O, mutex performance, and thread latency. The results are saved in JSON format and then processed by a Python script to generate overall performance scores.

## Features

- **Comprehensive Tests**: Covers CPU, Memory, File I/O, Mutex, and Thread performance.
- **Scalable**: Can be run on multiple VPS instances simultaneously.
- **Customizable**: Allows custom weighting schemes in the Python script for different metrics.
- **User-friendly**: Automates the entire process, from installing required packages to generating final scores.

## Prerequisites

- Ubuntu 22.04 LTS or higher
- SSH access to all VPS nodes
- Ansible 2.9 or higher

## Installation

### Install Ansible on Ubuntu

To install Ansible, open a terminal and run the following commands:

```bash
sudo apt update
sudo apt install ansible
```

### Clone This Repository

```bash
git clone <repository_url>
cd <repository_name>
```

### Update Ansible Inventory File

An example inventory file `my_ansible_inventory_file.ini` is provided. Update this file with the IPs and SSH keys for your VPS instances.

```ini
[all]
TestnetSupernode01 ansible_host=14.1.135.41
TestnetSupernode02 ansible_host=14.1.135.42
...
[all:vars]
ansible_user=ubuntu
ansible_private_key_file="/path/to/your/private/key.pem"
```

## Usage

Navigate to the directory containing `benchmark-playbook.yml` and run:

```bash
ansible-playbook -v -i my_ansible_inventory_file.ini benchmark-playbook.yml
```

### Output

- JSON files containing raw benchmark data will be saved in `/tmp/` on the control node.
- The Python script will process these JSON files and generate a final JSON file containing overall performance scores in the `/home/<YOUR_USER_NAME>/benchmark_result_output_files` directory.

## Understanding the Code

### Ansible Playbook

1. **Tasks**: Each task in the playbook is designed to install required packages, run different sysbench tests, and collect metrics.
2. **Error Handling**: The playbook is designed to continue even if a benchmark fails on a particular node.
3. **Results**: Results are collected in dictionary form and saved as JSON files.

### Python Script

1. **Data Processing**: Reads raw JSON files and calculates overall performance scores based on customizable weighting schemes.
2. **Output**: Saves the final scores in a JSON file, sorted in descending order.

## Subscores and Data Processing

### Subscores Generated by the Ansible Playbook

The Ansible playbook runs a series of benchmark tests using sysbench, generating subscores for the following aspects:

1. **CPU Performance (`cpu_speed_test__events_per_second`)**: Measures the number of CPU events completed per second. Higher scores indicate better CPU performance.
2. **Memory Throughput (`memory_speed_test__MiB_transferred`)**: Measures the speed of memory operations in Mebibytes (MiB) transferred. Higher scores indicate faster memory throughput.
3. **File I/O Performance (`fileio_test__reads_per_second`)**: Measures the number of read operations completed per second. Higher scores indicate better file I/O performance.
4. **Mutex Latency (`mutex_test__avg_latency`)**: Measures the average latency of mutex operations. Lower scores indicate better performance.
5. **Thread Latency (`threads_test__avg_latency`)**: Measures the average latency of thread operations. Lower scores indicate better performance.

These subscores are extracted from the sysbench output using shell commands like `grep` and `awk`, and they are then stored in a dictionary called `benchmark_results`.

### JSON Formatting

The playbook uses Ansible's `set_fact` module to combine each subscore into a JSON-formatted string. For example, the CPU performance subscore might look like this in JSON:

```json
{
  "cpu_speed_test__events_per_second": 1000.5
}
```

These JSON-formatted subscores are combined to form a comprehensive JSON object for each host, which is then saved to a file.

### Normalization of Subscores in Python Script

The Python script processes these JSON files to generate overall performance scores. One critical step is the normalization of each subscore from 0 to 100, making the final scores relative to the most powerful machine in the benchmark test.

Here's how the normalization works:

1. **Identify Extremes**: For each metric, find the maximum and minimum values across all hosts.
2. **Normalize**: Use the following formula to scale each subscore:

\[
\text{Normalized Score} = \frac{{\text{Actual Score} - \text{Min Score}}}{{\text{Max Score} - \text{Min Score}}} \times 100
\]

If the Min Score and Max Score for a metric are the same (indicating no variation among the hosts), the normalized score is set to 100 for all hosts.

This approach ensures that the highest-performing host for each metric will have a normalized score of 100, while the lowest will have a normalized score of 0. All other hosts will have scores that are relative to these extremes.

## Example

Suppose we have two hosts, A and B, and their `cpu_speed_test__events_per_second` scores are 950 and 1050, respectively.

1. Max Score = 1050, Min Score = 950
2. For Host A: \( \frac{{950 - 950}}{{1050 - 950}} \times 100 = 0 \)
3. For Host B: \( \frac{{1050 - 950}}{{1050 - 950}} \times 100 = 100 \)

Host A will have a normalized CPU score of 0, and Host B will have a score of 100, indicating that Host B is relatively more powerful for this specific metric.

By applying this normalization process to each metric, the script provides a robust, comparative view of the performance capabilities of each host.

## Contributing

Feel free to open issues or submit pull requests to improve the code or add new features.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
