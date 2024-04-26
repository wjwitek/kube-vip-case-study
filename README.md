# kube-vip - Load balancing services for Kubernetes clusters
#### Ewa Miklewska, Weronika Witek, Bartesz Zbiegień, Jan Ziętek

## Table of Contents
1. [Introduction](#introduction)
2. [Theoretical background](#theoreticalBackground)
3. [Case study concept description](#caseStudyConceptDescription)
4. [Solution architecture](#solutionArchitecture)
5. [Environment configuration](#environmentConfiguration)

<a name="introduction"></a>
## 1. Introduction

A lot of modern application have to support large number of users and provide reliable service. This is often achieved by hosting multiple copies of the application via frameworks like Kubernetes and having a load balancer. This service is responsible for managing to which copy the traffic goes and allows user to not care about which copy of the app they're connecting to.\\
Kube-vip is a framework that provides such load balancing functionality. What differs it from other solutions is that runs directly in the Kubernetes cluster, making it lighter and not reliable on any external software.

<a name="theoreticalBackground"></a>
## 2. Theoretical background
Kube-vip is a framework that supports creating highly available Kubernetes clusters. It offers three functionalities: VIP, load balancing in control plane and supporting load balancing of a service. Because of this it always works with multi-node or multi-pod clusters.\\
Virtual IP (VIP) allows for ensuring that an endpoint is always available. Within the cluster a leader is elected, which will than assume the VIP. If the leader fails or is changed for other reasons, the VIP is moved to the next leader.
When kube-vip is configured to work as a load balancer for control plane it listens for API requests and than distributes them to multiple Kubernete's API servers across many nodes. This is done via TCP-based round-robin protocol on the kernel level (so before packets are sent to real TCP port).\\
For the service load balancing, kube-vip takes more of a supporting role. It still requires external load controller, typically connected to the cluster via Cloud Controller. The kube-vip's role in this case is making the load balancer's endpoint visible to the rest of the cluster. For example if a load balancer is taking care of multiple copies of a backend service, kube-vip will advertise the VIP under which they are 'aggregated' to the frontend service in the same cluster.

<a name="caseStudyConceptDescription"></a>
## 3. Case study concept description
Our case study will explore two main features of Kube-vip: load balancing and Virtual IP. We will perform DDOS attack on a simple cluster connected to network and investigate how kube-vip's load balancer will perform. For VIP testing, we will perform simulation of emergency shut-down of selected control nodes to check how long it takes to recover server functionality. Diagram below presents architecture of the case study concept.
![Diagram Śuu](https://github.com/wjwitek/kube-vip-case-study/assets/74113640/0c923d4d-efd9-4ded-a6ce-e99b8a21e31c)


<a name="solutionArchitecture"></a>
## 4. Solution architecture

<a name="technologies"></a>
## 5. Technologies
- K3s - lightweight distribution of Kubernetes. 
- Kube-vip - load balancing framework for Kubernetes cluster.
- Docker - creating containers managed by Kubernetes
- K3sup - tool for easier setup and further development of K3s clusters

<a name="environmentConfiguration"></a>
## 6. Environment configuration

Kube-vip can be setup as a DeamonSet. To do this a manifest needs to be created. First, template needs to be copied from repository:
```console
sudo mkdir -p /var/lib/rancher/k3s/server/manifests/

curl https://kube-vip.io/manifests/rbac.yaml > kube-vip-rbac.yaml
```
Than the rest of the manifest is generated by running commands:
```console
export VIP={chosen_vip}

export INTERFACE={control_plane_interface}

KVVERSION=$(curl -sL https://api.github.com/repos/kube-vip/kube-vip/releases | jq -r ".[0].name")

alias kube-vip="sudo docker run --network host --rm ghcr.io/kube-vip/kube-vip:$KVVERSION"

kube-vip manifest daemonset \
    --interface $INTERFACE \
    --address $VIP \
    --inCluster \
    --taint \
    --controlplane \
    --services \
    --arp \
    --leaderElection
```
The generated part needs to be added to `rbac.yaml`, seperated by `---`. Then the manifest needs to be moved to directory with manifests:
```console
sudo mv kube-vip-rbac.yaml /var/lib/rancher/k3s/server/manifests/kube-vip-rbac.yaml
```

After those preperations we can create K3s servers:
```console
curl -sfL https://get.k3s.io | sh -s - --tls-san {chosen_vip}
```

and replace ip with {chosen_vip} in config file `/etc/rancher/k3s/k3s.yaml`.
