# Kops

handles the generation of Kops configuration files

[![Build Status](https://travis-ci.org/Flaconi/ansible-role-kops.svg?branch=master)](https://travis-ci.org/Flaconi/ansible-role-kops)
[![Version](https://img.shields.io/github/tag/Flaconi/ansible-role-kops.svg)](https://github.com/Flaconi/ansible-role-kops/tags)
[![Ansible Galaxy](https://img.shields.io/ansible/role/d/25923.svg)](https://galaxy.ansible.com/Flaconi/kops/)

## Requirements

* Ansible 2.5

## Additional variables

Additional variables that can be used (either as `host_vars`/`group_vars` or via command line args):

| Variable                             | Default                       | Description                  |
|--------------------------------------|-------------------------------|------------------------------|
| `kops_profile`                       | undefined      | Boto profule name to be used |
| `kops_default_version`               | `v1.10.4`      | Kubernetes Cluster version |
| `kops_default_region`                | `eu-central-1` | Default region to use |
| `kops_default_image`                 | `kope.io/k8s-1.9-debian-jessie-amd64-hvm-ebs-2018-03-11` | Default AMI to use. [See here for other AMIs'](https://github.com/kubernetes/kops/blob/master/channels/stable) |
| `kops_default_api_access`            | `[0.0.0.0/32]` | Array of allowed IP's to access the API from |
| `kops_default_ssh_access`            | `[0.0.0.0/32]` | Array of allowed IP's to ssh into the machines from |
| `kops_default_az`                    | `[a, b, c]`    | Available availability zones to be used by master, worker and bastion hosts |
| `kops_default_master_az`             | `[a, b, c]`    | Availability zones to launch master nodes in |
| `kops_default_worker_az`             | `[a, b, c]`    | Availability zones to launch worker nodes in |
| `kops_default_bastion_az`            | `[a]`          | Availability zones to launch bastion node(s) in |
| `kops_default_master_instance_type`  | `t2.medium`    | Default instance type for master nodes |
| `kops_default_worker_instance_type`  | `t2.medium`    | Default instance type for worker nodes |
| `kops_default_bastion_instance_type` | `t2.micro`     | Default instance type for bastion nodes |
| `kops_default_master_count`          | `3`            | Number of master nodes to launch |
|` kops_default_worker_min_size`       | `1`            | Minimum number of worker nodes per instance group |
|` kops_default_worker_max_size`       | `3`            | Maximum number of worker nodes per instance group |
|` kops_default_worker_vol_size`       | `200`          | Root volume size in GB for each worker node |
| `kops_default_ssh_pub_key`           | undefined      | Public ssh key for create cluster scripts |
| `kops_default_build_directory`       | `build`        | Template generation directory |

## Example definition

#### With sane defaults
When using the sane defaults, the only thing to configure for each cluster is

* cluster name
* s3 bucket name
* its worker nodes

```yml
kops_cluster:
  - name: playground-cluster-shop.k8s.local
    s3_bucket_name: playground-cluster-shop-state-store
    workers:
      - name: c4xlargea
      - name: c4xlargeb
      - name: c4xlargec
```

#### Fully customized
Instead of using somebody's sane defaults, you can also fully customize your cluster.

```yml
kops_cluster:
  - name: playground-cluster-shop.k8s.local
    version: v1.10.4
    type: private
    region: eu-central-1
    image: kope.io/k8s-1.8-debian-jessie-amd64-hvm-ebs-2018-02-08
    s3_bucket_name: playground-cluster-shop-state-store
    ssh_pup_key: "ssh-ed25519 AAAANSLxbLKF6DL8GDFE70AAAAIP8kH/aB4LKI2+S6a921rCwl2OZdL09iBhGHJ23jk"
    api_access:
      - 185.28.180.95/32
    ssh_access:
      - 185.28.180.95/32
    az: [a, b, c]
    bastion:
      az: [a]
      instance_type: t2.micro
    masters:
      count: 3
      instance_type: t2.medium
      az: [a, b, c]
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


## Testing

#### Requirements

* Docker
* [yamllint](https://github.com/adrienverge/yamllint)

#### Run tests

```bash
# Lint the source files
make lint

# Run integration tests with default Ansible version
make test

# Run integration tests with custom Ansible version
make test ANSIBLE_VERSION=2.4
```
