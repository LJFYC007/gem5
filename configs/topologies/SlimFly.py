# Copyright (c) 2010 Advanced Micro Devices, Inc.
#               2016 Georgia Institute of Technology
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from m5.params import *
from m5.objects import *

from common import FileSystemConfig

from topologies.BaseTopology import SimpleTopology


class SlimFly(SimpleTopology):
    description = "SlimFly"

    def __init__(self, controllers):
        self.nodes = controllers

    # Makes a generic mesh
    # assuming an equal number of cache and directory cntrls

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        nodes = self.nodes
        num_routers = 50
        link_latency = options.link_latency  # used by simple and garnet
        router_latency = options.router_latency  # only used by garnet

        # Create the routers
        routers = [
            Router(router_id=i, latency=router_latency)
            for i in range(num_routers)
        ]
        network.routers = routers

        # Link counter to set unique link ids
        link_count = 0

        # Connect each node to the appropriate router
        ext_links = []
        for (i, n) in enumerate(nodes):
            router_id = i % num_routers
            ext_links.append(
                ExtLink(
                    link_id=link_count,
                    ext_node=n,
                    int_node=routers[router_id],
                    latency=link_latency,
                )
            )
            link_count += 1

        network.ext_links = ext_links

        # Create the ring links
        int_links = []

        q = 5
        e = 2
        X = [1, 4]
        Y = [2, 3]

        def get_router_id(b, x, y, q):
            return b * q * q + x * q + y

        # Connect (0, x, y) with (0, x, y') if y - y' ∈ X
        for x in range(q):
            for y in range(q):
                for y_prime in range(q):
                    if (y - y_prime) % q in X:
                        src_router = routers[get_router_id(0, x, y, q)]
                        dst_router = routers[get_router_id(0, x, y_prime, q)]
                        int_links.append(
                            IntLink(
                                link_id=link_count,
                                src_node=src_router,
                                dst_node=dst_router,
                                src_outport="East",
                                dst_inport="West",
                                latency=link_latency,
                                weight=1,
                            )
                        )
                        link_count += 1

        # Connect (1, m, c) with (1, m, c') if c - c' ∈ Y
        for m in range(q):
            for c in range(q):
                for c_prime in range(q):
                    if (c - c_prime) % q in Y:
                        src_router = routers[get_router_id(1, m, c, q)]
                        dst_router = routers[get_router_id(1, m, c_prime, q)]
                        int_links.append(
                            IntLink(
                                link_id=link_count,
                                src_node=src_router,
                                dst_node=dst_router,
                                src_outport="East",
                                dst_inport="West",
                                latency=link_latency,
                                weight=1,
                            )
                        )
                        link_count += 1

        # Connect (0, x, y) with (1, m, c) if y = mx + c
        for x in range(q):
            for y in range(q):
                for m in range(q):
                    c = (y - m * x) % q
                    src_router = routers[get_router_id(0, x, y, q)]
                    dst_router = routers[get_router_id(1, m, c, q)]
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=src_router,
                            dst_node=dst_router,
                            src_outport="North",
                            dst_inport="South",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    link_count += 1

                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=dst_router,
                            dst_node=src_router,
                            src_outport="South",
                            dst_inport="North",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    link_count += 1

        network.int_links = int_links

    def registerTopology(self, options):
        for i in range(options.num_cpus):
            FileSystemConfig.register_node(
                [i], MemorySize(options.mem_size) // options.num_cpus, i
            )
