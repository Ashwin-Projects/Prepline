# Taxonomy v1.0 cheat sheet

All 83 nodes of `data/taxonomy/taxonomy_v1.0.json`, grouped by domain (37 high_level_concept, 46 granular_skill).

- **Syllabus rows** take `high_level_concept` ids (marked **H**).
- **Interview rows** take `granular_skill` ids (marked g).
- `none` is allowed when no node fits (see LABELLING_GUIDE.md).

## dsa (29)

| topic_id | name | type | description |
|---|---|---|---|
| `dsa` | Data Structures and Algorithms | **H** | Core computer science data structures, storage abstractions, and algorithmic problem-solving paradigms. |
| `dsa.arrays` | Arrays and Strings | **H** | Linear contiguous memory structures, character sequences, indexing, and array manipulation algorithms. |
| `dsa.arrays.two_pointers` | Two Pointers Technique | g | Searching pairs or subarrays in linear structures using converging or fast-slow pointer iterations. |
| `dsa.arrays.sliding_window` | Sliding Window Technique | g | Maintaining dynamic or fixed-size contiguous subarray windows to solve range and substring optimization problems. |
| `dsa.arrays.prefix_sum` | Prefix Sum | g | Precomputing cumulative sum arrays to perform constant-time range sum queries. |
| `dsa.linked_lists` | Linked Lists | **H** | Singly and doubly linked pointer-based node sequences, insertions, deletions, and list operations. |
| `dsa.linked_lists.traversal_reversal` | Linked List Manipulation & Cycle Detection | g | Reversing linked list pointers, merging sorted lists, finding middle nodes, and Floyd's cycle-finding algorithm. |
| `dsa.stacks_queues` | Stacks and Queues | **H** | LIFO stack and FIFO queue abstract data types, implementation variants, and sequence evaluation. |
| `dsa.stacks_queues.monotonic_stack` | Monotonic Stack and Queue | g | Maintaining elements in strictly increasing or decreasing order inside stacks/queues to find next greater or smaller elements. |
| `dsa.trees` | Trees and Binary Trees | **H** | Hierarchical node data structures, binary trees, balanced trees, and recursive tree traversals. |
| `dsa.trees.traversal` | Tree Traversals | g | Visiting tree nodes using preorder, inorder, postorder, and level-order breadth-first traversals. |
| `dsa.trees.bst` | Binary Search Trees | g | Ordered binary search trees, insertion, deletion, searching, and maintaining BST invariants. |
| `dsa.trees.lowest_common_ancestor` | Lowest Common Ancestor | g | Finding the lowest shared ancestor node of two target nodes in binary trees and binary search trees. |
| `dsa.heaps` | Heaps and Priority Queues | **H** | Min-heaps, max-heaps, priority queues, binary heap representations, and heapify operations. |
| `dsa.heaps.top_k` | Top K Elements and K-Way Merge | g | Using min/max priority queues to efficiently track top K frequent elements and merge K sorted streams. |
| `dsa.graphs` | Graphs and Network Topologies | **H** | Vertices, edges, directed/undirected graphs, adjacency representations, and graph algorithms. |
| `dsa.graphs.bfs_dfs` | Graph Traversal (BFS & DFS) | g | Exploring graphs using queue-based Breadth-First Search and recursive or stack-based Depth-First Search. |
| `dsa.graphs.shortest_path` | Shortest Path Algorithms | g | Computing single-source and all-pairs shortest paths using Dijkstra's, Bellman-Ford, and Floyd-Warshall algorithms. |
| `dsa.graphs.topological_sort` | Topological Sorting | g | Ordering vertices in Directed Acyclic Graphs (DAGs) using Kahn's algorithm or DFS for dependency resolution. |
| `dsa.graphs.disjoint_set` | Disjoint Set Union (Union-Find) | g | Managing partitioned sets using Union-Find with path compression and rank-based union for connectivity. |
| `dsa.sorting_searching` | Sorting and Searching | **H** | Comparison and non-comparison sorting techniques, linear search, and binary search methodologies. |
| `dsa.sorting_searching.binary_search` | Binary Search | g | Logarithmic search on sorted arrays, rotated arrays, and binary search on monotonic answer spaces. |
| `dsa.dp` | Dynamic Programming | **H** | Optimization via overlapping subproblems, optimal substructure, memoization, and tabular state transitions. |
| `dsa.dp.1d` | 1D Dynamic Programming | g | Solving linear recurrence state transitions including Fibonacci variants, house robber, and climbing stairs. |
| `dsa.dp.knapsack` | Knapsack and Subset DP | g | 0/1 Knapsack, unbounded knapsack, coin change, and subset sum optimization problems. |
| `dsa.dp.grid` | Grid Path Dynamic Programming | g | Finding minimum path sums and unique traversal paths across 2D grid matrices. |
| `dsa.dp.lcs` | String and Subsequence DP | g | Longest Common Subsequence, Edit Distance, and String Alignment dynamic programming algorithms. |
| `dsa.backtracking` | Recursion and Backtracking | **H** | Exploring state space trees recursively, pruning invalid branches, and generating combinatorial structures. |
| `dsa.backtracking.subsets_permutations` | Subsets and Permutations | g | Generating power sets, permutations, combinations, and solving constraint satisfaction problems. |

## dbms (14)

| topic_id | name | type | description |
|---|---|---|---|
| `dbms` | Database Management Systems | **H** | Database architectures, data modeling, relational algebra, SQL querying, transactions, and indexing. |
| `dbms.relational_model` | Relational Model and ER Diagrams | **H** | Entities, relationships, keys (primary, foreign), and relational schema design. |
| `dbms.sql` | Structured Query Language (SQL) | **H** | Data Definition Language (DDL), Data Manipulation Language (DML), and complex relational queries. |
| `dbms.sql.queries_aggregations` | SQL Aggregations and Grouping | g | Filtering, grouping, HAVING clauses, and aggregate functions (COUNT, SUM, AVG, MIN, MAX). |
| `dbms.sql.joins` | SQL Joins | g | Combining rows from multiple relational tables using INNER JOIN, LEFT JOIN, RIGHT JOIN, FULL JOIN, and self joins. |
| `dbms.sql.subqueries` | SQL Subqueries and Window Functions | g | Nested subqueries, correlated subqueries, Common Table Expressions (CTEs), and window ranking functions. |
| `dbms.normalization` | Database Normalization | **H** | Functional dependencies, eliminating data redundancy, and database normal forms. |
| `dbms.normalization.normal_forms` | Normal Forms (1NF, 2NF, 3NF, BCNF) | g | Decomposing tables to satisfy First, Second, Third, and Boyce-Codd Normal Forms. |
| `dbms.transactions` | Transactions and Concurrency Control | **H** | Database transaction management, ACID properties, schedule serializability, and concurrency control. |
| `dbms.transactions.acid` | ACID Properties | g | Atomicity, Consistency, Isolation, and Durability guarantees in transactional databases. |
| `dbms.transactions.isolation_locking` | Transaction Isolation and Locking | g | Read Committed, Repeatable Read, Serializable isolation levels, 2-Phase Locking (2PL), and deadlock resolution. |
| `dbms.indexing` | Database Indexing and Storage | **H** | Disk storage organization, page layouts, file structures, and database index mechanisms. |
| `dbms.indexing.b_trees` | B-Trees and B+ Tree Indexing | g | Clustered and non-clustered indexes implemented using balanced B-Tree and B+ Tree structures. |
| `dbms.nosql` | NoSQL Databases | **H** | Non-relational data models including Key-Value, Document, Wide-Column, and Graph store architectures. |

## os (14)

| topic_id | name | type | description |
|---|---|---|---|
| `os` | Operating Systems | **H** | Operating system kernel architecture, process management, memory management, file systems, and hardware abstractions. |
| `os.process_management` | Processes and Threads | **H** | Process state transitions, process control blocks, execution threads, and user-space vs kernel-space execution. |
| `os.process_management.context_switch` | Context Switching and Process Control Block | g | Register state saving, process control block (PCB) metadata, and context switch CPU overhead. |
| `os.process_management.multithreading` | Multithreading and User/Kernel Threads | g | Thread execution models, POSIX threads, race conditions, and user-level vs kernel-level thread mapping. |
| `os.cpu_scheduling` | CPU Scheduling | **H** | Processor allocation strategies, scheduling queues, preemptive and non-preemptive scheduling algorithms. |
| `os.cpu_scheduling.algorithms` | CPU Scheduling Algorithms | g | First-Come First-Served (FCFS), Shortest Job First (SJF), Round Robin (RR), and Priority Scheduling. |
| `os.process_synchronization` | Process Synchronization and IPC | **H** | Inter-process communication, critical section problem, mutual exclusion, and synchronization primitives. |
| `os.process_synchronization.semaphores_mutex` | Semaphores, Mutexes, and Monitors | g | Mutex locks, counting semaphores, monitors, and classic concurrency problems (Producer-Consumer, Dining Philosophers). |
| `os.memory_management` | Memory Management and Virtual Memory | **H** | Main memory allocation, contiguous memory, paging, segmentation, and virtual memory systems. |
| `os.memory_management.paging_segmentation` | Paging, TLB, and Segmentation | g | Logical to physical address translation, page tables, Translation Lookaside Buffer (TLB), and memory segmentation. |
| `os.memory_management.page_replacement` | Demand Paging and Page Replacement | g | Page fault handling, thrashing, and page replacement algorithms (FIFO, LRU, Optimal, Clock). |
| `os.deadlocks` | Deadlocks | **H** | Necessary conditions for deadlock, resource allocation graphs, and handling strategies. |
| `os.deadlocks.prevention_avoidance` | Deadlock Prevention and Banker's Algorithm | g | Breaking Coffman conditions, Banker's safety algorithm, deadlock detection, and recovery mechanisms. |
| `os.file_systems` | File Systems | **H** | File concepts, directory organization, disk block allocation strategies, and inode structures. |

## cn (14)

| topic_id | name | type | description |
|---|---|---|---|
| `cn` | Computer Networks | **H** | Data communications, layered network architectures, Internet protocol stack, and network security. |
| `cn.network_models` | Network Architecture Models | **H** | OSI 7-layer model, TCP/IP protocol stack, encapsulation, and packet headers. |
| `cn.network_models.osi_layers` | OSI Model and TCP/IP Layers | g | Physical, Data Link, Network, Transport, Session, Presentation, and Application layers and protocol mapping. |
| `cn.application_layer` | Application Layer Protocols | **H** | Client-server architecture, HTTP/HTTPS, DNS, FTP, SMTP, and application data exchange. |
| `cn.application_layer.http_https` | HTTP, HTTPS, and REST | g | HTTP request/response methods, status codes, headers, RESTful API conventions, and HTTPS security. |
| `cn.application_layer.dns` | Domain Name System (DNS) | g | DNS hierarchy, recursive/iterative domain resolution, record types (A, AAAA, CNAME, MX, TXT), and DNS caching. |
| `cn.transport_layer` | Transport Layer Protocols | **H** | End-to-end communication, port addressing, multiplexing, TCP, and UDP transport mechanisms. |
| `cn.transport_layer.tcp_udp` | TCP vs UDP Protocols | g | Connection-oriented reliable TCP vs connectionless lightweight UDP trade-offs and packet headers. |
| `cn.transport_layer.tcp_mechanisms` | TCP Handshake, Flow, and Congestion Control | g | TCP 3-way handshake, 4-way teardown, sliding window flow control, and slow-start congestion control. |
| `cn.network_layer` | Network Layer and Routing | **H** | Logical IP addressing, subnetting, packet forwarding, and routing algorithms. |
| `cn.network_layer.ip_subnetting` | IP Addressing, Subnetting, and CIDR | g | IPv4/IPv6 addressing, subnet masks, Classless Inter-Domain Routing (CIDR), and NAT. |
| `cn.network_layer.routing_protocols` | Routing Algorithms and Protocols | g | Distance-vector (RIP) and Link-state (OSPF) routing algorithms, BGP, and autonomous systems. |
| `cn.network_security` | Network Security Fundamentals | **H** | Symmetric/asymmetric encryption, digital signatures, SSL/TLS, firewalls, and network threats. |
| `cn.network_security.tls_ssl` | TLS/SSL Handshake and Encryption | g | TLS handshake protocol, public-key certificates, symmetric session key exchange, and transport encryption. |

## system_design (12)

| topic_id | name | type | description |
|---|---|---|---|
| `system_design` | System Design | **H** | Large-scale distributed systems design, high availability, fault tolerance, scalability, and architectural components. |
| `system_design.scalability` | Scalability and System Architectures | **H** | Monolithic vs microservices architectures, horizontal and vertical scaling, and back-of-the-envelope estimations. |
| `system_design.load_balancing` | Load Balancing | **H** | Traffic distribution, Layer 4 vs Layer 7 load balancing, health checking, and reverse proxies. |
| `system_design.load_balancing.algorithms` | Load Balancing Algorithms & Consistent Hashing | g | Round Robin, Weighted Least Connections, and Consistent Hashing for server distribution. |
| `system_design.caching` | Caching Strategies and CDNs | **H** | In-memory caching, distributed caches (Redis, Memcached), cache policies, and Content Delivery Networks. |
| `system_design.caching.strategies` | Cache Invalidation & Eviction Strategies | g | Cache-Aside, Write-Through, Write-Back caching patterns, LRU/LFU eviction, and cache stampede prevention. |
| `system_design.database_scaling` | Database Scaling and Partitioning | **H** | Scaling databases beyond single node capacity through replication, federation, and partitioning. |
| `system_design.database_scaling.sharding_replication` | Database Sharding and Read Replicas | g | Horizontal database sharding keys, primary-replica replication, read scaling, and split-brain scenarios. |
| `system_design.messaging` | Message Queues and Event-Driven Architecture | **H** | Asynchronous task processing, message brokers (Kafka, RabbitMQ), publish-subscribe, and event streaming. |
| `system_design.messaging.pub_sub` | Message Queue Patterns and Decoupling | g | Point-to-point queues, publish-subscribe topics, message ordering, idempotent consumer processing, and dead-letter queues. |
| `system_design.distributed_consensus` | Distributed Systems Trade-offs & CAP Theorem | **H** | Consistency, Availability, Partition Tolerance trade-offs, PACELC theorem, and leader election. |
| `system_design.rate_limiting` | Rate Limiting and API Gateways | g | Throttling incoming requests using Token Bucket, Leaky Bucket, Sliding Window Log algorithms, and API gateway routing. |
