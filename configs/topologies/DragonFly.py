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


class DragonFly(SimpleTopology):
    description = "DragonFly"

    def __init__(self, controllers):
        self.nodes = controllers

    # Makes a generic mesh
    # assuming an equal number of cache and directory cntrls

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        nodes = self.nodes

        num_groups = options.num_groups
        num_routers_per_group = options.num_routers_per_group
        link_latency = options.link_latency  # used by simple and garnet
        router_latency = options.router_latency  # only used by garnet

        num_routers = num_groups * num_routers_per_group

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

        # Create the links
        int_links = []

        def get_router_id(i, x):
            return x + i * num_routers_per_group

        # Connect routers in the same group
        for i in range(num_groups):
            for x in range(num_routers_per_group - 1):
                for y in range(x + 1, num_routers_per_group):
                    src_router = routers[get_router_id(i, x)]
                    dst_router = routers[get_router_id(i, y)]
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
        for i in range(num_groups):
            for x in range(num_routers_per_group - 1):
                for y in range(x + 1, num_routers_per_group):
                    src_router = routers[get_router_id(i, y)]
                    dst_router = routers[get_router_id(i, x)]
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=src_router,
                            dst_node=dst_router,
                            src_outport="West",
                            dst_inport="East",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    link_count += 1

        # Connect groups
        for i in range(num_groups - 1):
            for j in range(i + 1, num_groups):
                src_router = routers[
                    get_router_id(i, (j - 1) % num_routers_per_group)
                ]
                dst_router = routers[
                    get_router_id(j, i % num_routers_per_group)
                ]
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
        for i in range(num_groups - 1):
            for j in range(i + 1, num_groups):
                src_router = routers[
                    get_router_id(j, i % num_routers_per_group)
                ]
                dst_router = routers[
                    get_router_id(i, (j - 1) % num_routers_per_group)
                ]
                int_links.append(
                    IntLink(
                        link_id=link_count,
                        src_node=src_router,
                        dst_node=dst_router,
                        src_outport="West",
                        dst_inport="East",
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
