# Running kube-proxy in IPVS Mode

EKS in IP Virtual Server (IPVS) mode solves the [network latency issue](https://aws.github.io/aws-eks-best-practices/reliability/docs/controlplane/#running-large-clusters) often seen when running large clusters with over 1,000 services with `kube-proxy` running in legacy iptables mode. This performance issue is the result of sequential processing of iptables packet filtering rules for each packet. This latency issue has been addressed in nftables, the successor to iptables. However, as of the time of this writing, [kube-proxy is still under development](https://kubernetes.io/docs/reference/networking/virtual-ips/#proxy-mode-nftables) to make use of nftables. To get around this issue, you can configure your cluster to run `kube-proxy` in IPVS mode.

## Overview

IPVS, which has been GA since [Kubernetes version 1.11](https://kubernetes.io/blog/2018/07/09/ipvs-based-in-cluster-load-balancing-deep-dive/), uses hash tables rather than linear searching to process packets, providing efficiency for clusters with thousands of nodes and services. IPVS was designed for load balancing, making it a suitable solution for Kubernetes networking performance issues.

IPVS offers several options for distributing traffic to backend pods. Detailed information for each option can be found in the [official Kubernetes documentation](https://kubernetes.io/docs/reference/networking/virtual-ips/#proxy-mode-ipvs), but a simple list is shown below. Round Robin and Least Connections are among the most popular choices for IPVS load balancing options in Kubernetes.
```
- rr (Round Robin)
- wrr (Weighted Round Robin)
- lc (Least Connections)
- wlc (Weighted Least Connections)
- lblc (Locality Based Least Connections)
- lblcr (Locality Based Least Connections with Replication)
- sh (Source Hashing)
- dh (Destination Hashing)
- sed (Shortest Expected Delay)
- nq (Never Queue)
```

### Implementation

Only a few steps are required to enable IPVS in your EKS cluster. The first thing you need to do is ensure your EKS worker node images have the Linux Virtual Server administration `ipvsadm` package installed. To install this package on a Fedora based image, such as Amazon Linux 2023, you can run the following command on the worker node instance.
```bash
sudo dnf install -y ipvsadm
```
On a Debian based image, such as Ubuntu, the installation command would look like this.
```bash
sudo apt-get install ipvsadm
```

Next, you need to load the kernel modules for the IPVS configuration options listed above. We recommend writing these modules to a file inside of the `/etc/modules-load.d/` directory so that they survive a reboot.
```bash
sudo sh -c 'cat << EOF > /etc/modules-load.d/ipvs.conf
ip_vs
ip_vs_rr
ip_vs_wrr
ip_vs_lc
ip_vs_wlc
ip_vs_lblc
ip_vs_lblcr
ip_vs_sh
ip_vs_dh
ip_vs_sed
ip_vs_nq
nf_conntrack
EOF'
```
You can run the following command to load these modules on a machine that is already running.
```bash
sudo modprobe ip_vs 
sudo modprobe ip_vs_rr
sudo modprobe ip_vs_wrr
sudo modprobe ip_vs_lc
sudo modprobe ip_vs_wlc
sudo modprobe ip_vs_lblc
sudo modprobe ip_vs_lblcr
sudo modprobe ip_vs_sh
sudo modprobe ip_vs_dh
sudo modprobe ip_vs_sed
sudo modprobe ip_vs_nq
sudo modprobe nf_conntrack
```
!!! note
    It is highly recommended to execute these worker node steps as part of you worker node's bootstrapping process via [user data script](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html) or in any build scripts executed to build a custom worker node AMI.

Next, you will configure your cluster's `kube-proxy` DaemonSet to run in IPVS mode. This is done by setting the `kube-proxy` `mode` to `ipvs` and the `ipvs scheduler` to one of the load balancing options listed above, for example: `rr` for Round Robin.
!!! Warning
    This is a disruptive change and should be performed in off-hours. We recommend making these changes during initial EKS cluster creation to minimize impacts.

You can issue an AWS CLI command to enable IPVS by updating the `kube-proxy` EKS Add-on.
```bash
aws eks update-addon --cluster-name $CLUSTER_NAME --addon-name kube-proxy \
  --configuration-values '{"ipvs": {"scheduler": "rr"}, "mode": "ipvs"}' \
  --resolve-conflicts OVERWRITE
```
Or you can do this by modifying the `kube-proxy-config` ConfigMap in your cluster.
```bash
kubectl -n kube-system edit cm kube-proxy-config
```
Find the `scheduler` setting under `ipvs` and set the value to one of the IPVS load balancing options listed above, for example: `rr` for Round Robin.
Find the `mode` setting, which defaults to `iptables`, and change the value to `ipvs`.
The result of either option should look similar to the configuration below.
```yaml hl_lines="9 13"
  iptables:
    masqueradeAll: false
    masqueradeBit: 14
    minSyncPeriod: 0s
    syncPeriod: 30s
  ipvs:
    excludeCIDRs: null
    minSyncPeriod: 0s
    scheduler: "rr"
    syncPeriod: 30s
  kind: KubeProxyConfiguration
  metricsBindAddress: 0.0.0.0:10249
  mode: "ipvs"
  nodePortAddresses: null
  oomScoreAdj: -998
  portRange: ""
  udpIdleTimeout: 250ms
```

If your worker nodes were joined to your cluster prior to making these changes, you will need to restart the kube-proxy DaemonSet.
```bash
kubectl -n kube-system rollout restart ds kube-proxy
```

### Validation

You can validate that your cluster and worker nodes are running in IPVS mode by issuing the following command on one of your worker nodes.
```bash
sudo ipvsadm -L
```

At a minimum, you should see a result similar to the one below, showing entries for the Kubernetes Cluster IP service at `10.100.0.1` and the codedns service at `10.100.0.10`.
```hl_lines="4 7 10"
IP Virtual Server version 1.2.1 (size=4096)
Prot LocalAddress:Port Scheduler Flags
  -> RemoteAddress:Port           Forward Weight ActiveConn InActConn
TCP  ip-10-100-0-1.us-east-1. rr
  -> ip-192-168-113-81.us-eas Masq        1      0          0
  -> ip-192-168-162-166.us-ea Masq        1      1          0
TCP  ip-10-100-0-10.us-east-1 rr
  -> ip-192-168-104-215.us-ea Masq        1      0          0
  -> ip-192-168-123-227.us-ea Masq        1      0          0
UDP  ip-10-100-0-10.us-east-1 rr
  -> ip-192-168-104-215.us-ea Masq        1      0          0
  -> ip-192-168-123-227.us-ea Masq        1      0          0
```