import os
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import shutil

# 定义仿真参数
injection_rates = np.linspace(0.01, 1.0, 50)
traffic_patterns = [
    "uniform_random",
    "shuffle",
    "transpose",
    "tornado",
    "neighbor",
]
results = {}

# 创建临时输出目录
temp_dir = "temp"
os.makedirs(temp_dir, exist_ok=True)

# 运行仿真
for pattern in traffic_patterns:
    results[pattern] = {
        "injection_rate": [],
        "average_latency": [],
        "reception_rate": [],
    }
    print(f"Running simulation for traffic pattern: {pattern}")
    for rate in injection_rates:

        # 运行GEM5仿真并忽略输出
        cmd = (
            f"./build/NULL/gem5.opt configs/example/garnet_synth_traffic.py "
            f"--network=garnet --num-cpus=64 --num-dirs=64 "
            f"--topology=Mesh_XY --mesh-rows=8 "
            f"--inj-vnet=0 --synthetic={pattern} "
            f"--sim-cycles=10000 --injectionrate={rate}"
        )
        subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # 解析输出数据
        stats_file = "m5out/stats.txt"
        network_stats_file = os.path.join(
            temp_dir, f"network_stats_{pattern}_{rate}.txt"
        )
        with open(network_stats_file, "w") as nsf:
            subprocess.run(
                f"grep 'packets_injected::total' {stats_file} | sed 's/system.ruby.network.packets_injected::total\s*/packets_injected = /' >> {network_stats_file}",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                f"grep 'packets_received::total' {stats_file} | sed 's/system.ruby.network.packets_received::total\s*/packets_received = /' >> {network_stats_file}",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                f"grep 'average_packet_queueing_latency' {stats_file} | sed 's/system.ruby.network.average_packet_queueing_latency\s*/average_packet_queueing_latency = /' >> {network_stats_file}",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                f"grep 'average_packet_network_latency' {stats_file} | sed 's/system.ruby.network.average_packet_network_latency\s*/average_packet_network_latency = /' >> {network_stats_file}",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                f"grep 'average_packet_latency' {stats_file} | sed 's/system.ruby.network.average_packet_latency\s*/average_packet_latency = /' >> {network_stats_file}",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                f"grep 'average_hops' {stats_file} | sed 's/system.ruby.network.average_hops\s*/average_hops = /' >> {network_stats_file}",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            total_packets_received = int(
                subprocess.getoutput(
                    f"grep 'packets_received::total' {stats_file} | awk '{{print $2}}'"
                )
            )
            num_cpus = int(subprocess.getoutput(f"grep -c 'cpu' {stats_file}"))
            sim_cycles = int(
                subprocess.getoutput(
                    f"grep 'simTicks' {stats_file} | awk '{{print $2}}'"
                )
            )
            reception_rate = total_packets_received / num_cpus / sim_cycles

            results[pattern]["injection_rate"].append(rate)
            avg_latency = float(
                subprocess.getoutput(
                    f"grep 'average_packet_latency' {network_stats_file} | awk '{{print $3}}'"
                )
            )
            results[pattern]["average_latency"].append(avg_latency)
            results[pattern]["reception_rate"].append(reception_rate)

# 绘制延迟-吞吐量曲线
plt.figure(figsize=(10, 6))
for pattern in traffic_patterns:
    plt.plot(
        results[pattern]["reception_rate"],
        results[pattern]["average_latency"],
        label=pattern,
    )

plt.xlabel("Throughput (1/Cycle)")
plt.ylabel("Average Latency (Cycles)")
plt.title("Latency-Throughput Curve for Different Traffic Patterns")
plt.legend()
plt.grid(True)

# 保存图片到脚本所在目录
output_image = "latency_throughput_curve.png"
plt.savefig(output_image)
plt.show()

# 删除临时文件夹及其内容
shutil.rmtree(temp_dir)

print(
    f"Simulation and plotting complete. The results are saved as {output_image}."
)
