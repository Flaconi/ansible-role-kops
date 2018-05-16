# Kops

handles the generation of Kops configuration files

[![Build Status](https://travis-ci.org/Flaconi/ansible-role-kops.svg?branch=master)](https://travis-ci.org/Flaconi/ansible-role-kops)

## Requirements

* Ansible 2.5

## Example definition

#### With sane defaults
When using the sane defaults, the only thing to configure for each cluster is

* the name
* its worker nodes

```yml
kops_cluster:
  - name: playground-cluster-shop.k8s.local
    workers:
      - name: c4xlargea
        instance_type: c4.xlarge
        min_size: 1
        max_size: 3
        volume_size: 200
        availability_zones: [a]
      - name: c4xlargeb
        instance_type: c4.xlarge
        min_size: 1
        max_size: 3
        volume_size: 200
        availability_zones: [b]
      - name: c4xlargec
        instance_type: c4.xlarge
        min_size: 1
        max_size: 3
        volume_size: 200
        availability_zones: [c]
```

#### Fully customized
Instead of using somebody's sane defaults, you can also fully customize your cluster.

```yml
kops_cluster:
  - name: playground-cluster-shop.k8s.local
    version: v1.10.2
    type: private
    region: eu-central-1
    image: kope.io/k8s-1.8-debian-jessie-amd64-hvm-ebs-2018-02-08
    s3_bucket_name: playground-cluster-shop-state-store
    api_access:
      - 185.28.184.194/32
    ssh_access:
      - 185.28.184.194/32
    bastion:
      availability_zones: [a]
      instance_type: t2.micro
    masters:
      instance_type: t2.medium
    workers:
      - name: c4xlargea
        instance_type: c4.xlarge
        min_size: 1
        max_size: 3
        volume_size: 200
        availability_zones: [a]
      - name: c4xlargeb
        instance_type: c4.xlarge
        min_size: 1
        max_size: 3
        volume_size: 200
        availability_zones: [b]
      - name: c4xlargec
        instance_type: c4.xlarge
        min_size: 1
        max_size: 3
        volume_size: 200
        availability_zones: [c]
```
