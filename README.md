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

DOS (denial-of-service) attack is cyber-attack in which the perpetrator seeks to make a machine or network resource unavailable to its intended users by temporarily or indefinitely disrupting services of a host connected to a network. DDOS stands for distributed denial-of-service and it involves attacking via multiple hosts contrary to just one which makes it much harder to detect. Ideally, we would want service to quickly recognize the origin of fake requests and not accept them after recognizing a pattern (static IP address, attacked protocol, specific http request). We can broadly recognize 3 types of DDOS attacks:
- Application Layer attacks - target the layer where web pages are generated on the server and delivered in response to HTTP requests. The basic attack is known as HTTP flood which is similar to pressing refresh in a web browser over and over on many different computers at once – large numbers of HTTP requests flood the server, resulting in denial-of-service.
- Protocol attacks - also known as a state-exhaustion attacks, cause a service disruption by over-consuming server resources and/or the resources of network equipment like firewalls and load balancers by utilizeing weaknesses in layer 3 and layer 4 of the protocol stack to render the target inaccessible. Example of such could SYN Flood that exploits TCP handshake and force service to wait for final step in chandshake that never occurs.
- Volumetric attacks - attempts to create congestion by consuming all available bandwidth between the target and the larger Internet.

In this study we will explore load balancer capabilities against first two types of attacks.
<a name="caseStudyConceptDescription"></a>
## 3. Case study concept description
Our case study will explore two main features of Kube-vip: load balancing and Virtual IP. We will perform DDOS attack on a simple cluster connected to network and investigate how kube-vip's load balancer will perform. For VIP testing, we will perform simulation of emergency shut-down of selected control nodes to check how long it takes to recover server functionality. Diagram below presents architecture of the case study concept.
![Diagram Śuu](https://github.com/wjwitek/kube-vip-case-study/assets/74113640/0c923d4d-efd9-4ded-a6ce-e99b8a21e31c)


<a name="solutionArchitecture"></a>
## 4. Solution architecture
Planned architecture includes 3 server nodes and two agent nodes. 

<a name="technologies"></a>
## 5. Technologies
- K3s - lightweight distribution of Kubernetes. 
- Kube-vip - load balancing framework for Kubernetes cluster.
- Docker - creating containers managed by Kubernetes
- K3sup - tool for easier setup and further development of K3s clusters
- HULK - Http Unbearable Load King - web server denial of service testing tool,
- hping3 - network tool able to send custom ICMP/UDP/TCP packets and to display target replies. It will be used for more advanced DOS tests.
<a name="environmentConfiguration"></a>
## 6. Environment configuration

We are setting up our enironment using KinD. Kube-vip is set up as a DeamonSet and also serves as Cloud Controller for our cluster. Here are the steps:

1. Creat cluster using a config file
```console
kind create cluster --config ./manifests/kind-config.yaml
```
2. Get address pool for kube-vip
```console
docker network inspect kind -f '{{ range $i, $a := .IPAM.Config }}{{ println .Subnet }}{{ end }}'
```
The result should be a subnet like: `172.18.0.0/16`
3. Deploy the kube-vip Cloud Controller
```console
kubectl apply -f https://raw.githubusercontent.com/kube-vip/kube-vip-cloud-provider/main/manifest/kube-vip-cloud-controller.yaml
```
4. Add address range belonging to subnet we got in 2.
```
kubectl create configmap --namespace kube-system kubevip --from-literal range-global=172.18.100.10-172.18.100.30
```
5. Create kube-vip's RBAC settings
```console
kubectl apply -f https://kube-vip.io/manifests/rbac.yaml
```
6. Export environment variables
```console
export KVVERSION=latest
export INTERFACE={interface used by nodes, commonly eth0}
export VIP={our chosen VIP, must be in subnet from point 2, e.g. 172.18.0.10}
```
7. Prepare kube-vip command
```console
alias kube-vip="ctr image pull ghcr.io/kube-vip/kube-vip:$KVVERSION; ctr run --rm --net-host ghcr.io/kube-vip/kube-vip:$KVVERSION vip /kube-vip"
```
8. Generate and apply kube-vip's manifest
```console
kube-vip manifest daemonset --interface $INTERFACE
                            --address $VIP
                            --inCluster
                            --taint
                            --controlplane
                            --services
                            --arp
                            --enableLoadBalancer | kubectl apply -f -
```
9. Replace addres in kubectl with VIP
```console
kubectl config set-cluster kind-kind --server=https://$VIP:6443
```
Now the kube-vip is working and we should be able to connect to control plane using `VIP` address, however we need to use flag `--insecure-skip-tls-verify`. To add the `VIP` to cluster
s certificates additional steps are needed.

1.Get current kubeadm config
```console
kubectl -n kube-system get configmap kubeadm-config --insecure-skip-tls-verify -o jsonpath='{.data.ClusterConfiguration}' > kubeadm.yaml
```
2.Modify the kubeadm.yaml by adding `VIP` under certSANs, file beginning should look similar to this:
```yaml
apiServer:
  certSANs:
  - localhost
  - 127.0.0.1
  - 172.20.0.10
  extraArgs:
    runtime-config: ""
  timeoutForControlPlane: 4m0s
```
3. Connect to a chosen node that hosts a control plane
```console
docker exec -it {container id} bash
```
4. Move the old certificates
```console
mv /etc/kubernetes/pki/apiserver.{crt,key} ~
```
5. Get the kubeadm.yaml file created earlier inside the docker container.
6. Generate new certificate
```console
kubeadm init phase certs apiserver --config kubeadm.yaml
```
7. Repeat the process on other nodes with control planes, howevert instead of creating new certificates copy `/etc/kubernetes/pki/apiserver.{crt,key}` from the first container.
8. On each container run
```console
kubeadm init phase upload-config kubeadm --config kubeadm.yaml
```

Now you should be able to use kubectl without the flag `--insecure-skip-tls-verify`.

<a name="ddosTest"></a>
## 6. DDOS Stress Test
For Protocol Attack we will use docker image of Hping3 packet generator image from dockerhub.

```console
docker pull sflow/hping3
```

We will carry out syn flood attack (-S flag) to our server (-p 80) by sending 10.000 packets of 120B size and randomizing our source to avoid detection:

```console
docker run --rm sflow/hping3 -c 10000 -d 120 -S -w 64 --rand-source <ip address>
```

<a name="ddosTest"></a>
## 8. DDOS Test Result
The experiment was conducted by measuring avarage response time for http request. We wanted to see how low scale denial of service attack will increase response time.

On cluster without configures Kube-vip we notice quite visible increase in response time (table below), but not exactly significant becouse of only one source of attack.
| Standard response time  | DDOS response time |  % increase |
| ------------- | ------------- | ---------- |
| 0.00525  | 0.00573  | 9.1% |

On cluster with configured Kube-vip we observe equal standard resopse time, but much bigger increase in reponse time during SYN flood attack.
| Standard response time  | DDOS response time |  % increase |
| ------------- | ------------- | ---------- |
| 0.00538  | 0.00651  | 21.0% |

We are not excatly sure why Kube-vip so drasticaly increase respond time during attack.
