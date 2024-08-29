import os
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import shutil

# Define simulation parameters
injection_rates = np.linspace(0.01, 1.0, 50)
traffic_patterns = [
    # "uniform_random",
    # "tornado",
    "custom",
]
topologies = [
    ("original", "--topology=SlimFly --vcs-per-vnet=1"),
    ("deadlock-free", "--topology=SlimFly --vc-algorithm=1"),
]

results = {}

# Create temporary output directory
temp_dir = "temp"
os.makedirs(temp_dir, exist_ok=True)

# Run simulations
for custom_name, topology in topologies:
    topology_params = topology.split()
    topology_name = (
        custom_name  # Use custom name instead of extracting from topology
    )

    for pattern in traffic_patterns:
        key = f"{topology_name}"
        results[key] = {
            "injection_rate": [],
            "average_latency": [],
            "reception_rate": [],
        }
        print(
            f"Running simulation for topology: {topology_name}, traffic pattern: {pattern}"
        )
        for rate in injection_rates:

            # Run GEM5 simulation and ignore output
            cmd = (
                f"../build/NULL/gem5.opt ../configs/example/garnet_synth_traffic.py "
                f"--network=garnet --num-cpus=64 --num-dirs=64 "
                f"{topology} "
                f"--inj-vnet=0 --synthetic={pattern} "
                f"--sim-cycles=10000 --injectionrate={rate}"
            )
            subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Parse output data
            stats_file = "m5out/stats.txt"
            network_stats_file = os.path.join(
                temp_dir, f"network_stats_{topology_name}_{pattern}_{rate}.txt"
            )
            with open(network_stats_file, "w") as nsf:
                subprocess.run(
                    f"grep 'packets_injected::total' {stats_file} | sed 's/system.ruby.network.packets_injected::total\s*/packets_injected = /' >> {network_stats_file}",
                    shell=True,
                )
                subprocess.run(
                    f"grep 'packets_received::total' {stats_file} | sed 's/system.ruby.network.packets_received::total\s*/packets_received = /' >> {network_stats_file}",
                    shell=True,
                )
                subprocess.run(
                    f"grep 'average_packet_queueing_latency' {stats_file} | sed 's/system.ruby.network.average_packet_queueing_latency\s*/average_packet_queueing_latency = /' >> {network_stats_file}",
                    shell=True,
                )
                subprocess.run(
                    f"grep 'average_packet_network_latency' {stats_file} | sed 's/system.ruby.network.average_packet_network_latency\s*/average_packet_network_latency = /' >> {network_stats_file}",
                    shell=True,
                )
                subprocess.run(
                    f"grep 'average_packet_latency' {stats_file} | sed 's/system.ruby.network.average_packet_latency\s*/average_packet_latency = /' >> {network_stats_file}",
                    shell=True,
                )
                subprocess.run(
                    f"grep 'average_hops' {stats_file} | sed 's/system.ruby.network.average_hops\s*/average_hops = /' >> {network_stats_file}",
                    shell=True,
                )

                total_packets_received = int(
                    subprocess.getoutput(
                        f"grep 'packets_received::total' {stats_file} | awk '{{print $2}}'"
                    )
                )
                num_cpus = int(
                    subprocess.getoutput(f"grep -c 'cpu' {stats_file}")
                )
                sim_cycles = int(
                    subprocess.getoutput(
                        f"grep 'simTicks' {stats_file} | awk '{{print $2}}'"
                    )
                )
                reception_rate = total_packets_received / num_cpus / sim_cycles

                results[key]["injection_rate"].append(rate)
                avg_latency = float(
                    subprocess.getoutput(
                        f"grep 'average_packet_latency' {network_stats_file} | awk '{{print $3}}'"
                    )
                )
                results[key]["average_latency"].append(avg_latency)
                results[key]["reception_rate"].append(reception_rate)

# Plot Latency-Throughput curves
plt.figure(figsize=(12, 8))
for key in results:
    topology_name = key
    plt.plot(
        results[key]["injection_rate"],
        results[key]["reception_rate"],
        label=f"{topology_name}",
    )

plt.xlabel("Injection Rate")
plt.ylabel("Reception Rate")
plt.title("Reception Rate Curve for Different Traffic Patterns")
plt.legend()
plt.grid(True)

# Save plot to the script directory
output_image = "../report/deadlock.png"
plt.savefig(output_image)

# Delete temporary folder and its contents
shutil.rmtree(temp_dir)

print(
    f"Simulation and plotting complete. The results are saved as {output_image}."
)
