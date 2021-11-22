# Kops

This Ansible role handles the generation of Kops configuration files and optionally also
updating kops state store as well as creating or updating the cluster.

Full dry-run is supported.

**Note:** By default only configuration files are created, actual state store or cluster actions
must be explicitly stated.

[![CI build](https://github.com/Flaconi/ansible-role-kops/actions/workflows/ci.yaml/badge.svg)](https://github.com/Flaconi/ansible-role-kops/actions/workflows/ci.yaml)
[![Version](https://img.shields.io/github/tag/Flaconi/ansible-role-kops.svg)](https://github.com/Flaconi/ansible-role-kops/tags)
[![Ansible Galaxy](https://img.shields.io/ansible/role/d/25923.svg)](https://galaxy.ansible.com/Flaconi/kops/)

## Role tagging

This Ansible role is tagged according to the latest compatible (and tested by us) version of [kops](https://github.com/kubernetes/kops/blob/master/docs/install.md) used.


## Requirements

* Ansible 2.8
* Python lib: [pyaml](https://github.com/yaml/pyyaml)
* Binary: [kops](https://github.com/kubernetes/kops/blob/master/docs/install.md)

## Run-time variables

When using this role it will simply generate the kops configuration files as well as shell scripts
to deploy each defined cluster. You can also choose to use Ansible to provision kops. This can be done for
multiple different stages as defined below:

| Variable            | Default   | Choices                 |
|---------------------|-----------|-------------------------|
| `kops_update`       | undefined | `state` `update`, `all` |
| `kops_cluster_name` | undefined | If `kops_cluster` list contains more than one cluster definition, you can limit the roll-out to this specific cluster from the list. (Defined by `kops_cluster[].name`) |

**Note:** As this role is fully dry-run capable you should use it in the following order for
productionized stacks:

1. Dry run to see state store differences
2. Run state store update
3. Dry run to see cluster update differences
4. Run cluster update

#### Update the state store

In order to update Kops' state store in S3, you need to add the following variable to your Ansible
command:
```
-e kops_update=state
```

#### Update the Cluster

In order to apply all settings from the state store to the cluster, you need to add the following
variables to your Ansible command:
```
-e kops_update=update
```

#### Update the state store and the cluster afterwards

In order to both apply state store updates in S3 and then update the cluster accordingly, you need
to add the following variable to your Ansible command:
```
-e kops_update=all
```

#### Limit update to a specific cluster

In case your kops_cluster list contains multiple items, you can limit the whole roll-out/dry-run
to a specific cluster defined by its name:
```
-e kops_cluster_name=playground-cluster-shop.k8s.local
```


## Additional variables

Additional variables that can be used (either as `host_vars`/`group_vars` or via command line args):

| Variable                                     | Default        | Description                  |
|----------------------------------------------|----------------|------------------------------|
| `kops_profile`                               | undefined      | Boto profule name to be used |
| `kops_default_version`                       | `v1.10.7`      | Kubernetes Cluster version |
| `kops_default_region`                        | `eu-central-1` | Default region to use |
| `kops_default_image`                         | `kope.io/k8s-1.9-debian-jessie-amd64-hvm-ebs-2018-03-11` | Default AMI to use. [See here for other AMIs'](https://github.com/kubernetes/kops/blob/master/channels/stable) |
| `kops_default_api_access`                    | `[0.0.0.0/32]` | Array of allowed IP's to access the API from |
| `kops_ssh_additional_cidrs_from_sg`          | `""` | Name of the Security Group with the corresponding Ingress CIDRs that will connect to the jumpbox via SSH |
| `kops_default_ssh_access`                    | `[0.0.0.0/32]` | Array of allowed IP's to ssh into the machines from |
| `kops_externally_managed_egress`             | `false`        | If you manage default routing separately, e.g. in case of VGW or TGW please set to True |
| `kops_default_az`                            | `[a, b, c]`    | Available availability zones to be used by master, worker and bastion hosts |
| `kops_default_master_az`                     | `[a, b, c]`    | Availability zones to launch master nodes in |
| `kops_default_worker_az`                     | `[a, b, c]`    | Availability zones to launch worker nodes in |
| `kops_default_bastion_az`                    | `[a]`          | Availability zones to launch bastion node(s) in |
| `kops_default_master_instance_type`          | `t2.medium`    | Default instance type for master nodes |
| `kops_default_worker_instance_type`          | `t2.medium`    | Default instance type for worker nodes |
| `kops_default_bastion_instance_type`         | `t2.micro`     | Default instance type for bastion nodes |
| `kops_default_master_count`                  | `3`            | Number of master nodes to launch |
|` kops_default_worker_min_size`               | `1`            | Minimum number of worker nodes per instance group |
|` kops_default_worker_max_size`               | `3`            | Maximum number of worker nodes per instance group |
|` kops_default_worker_vol_size`               | `200`          | Root volume size in GB for each worker node |
| `kops_default_ssh_pub_key`                   | undefined      | Public ssh key for create cluster scripts |
| `kops_default_build_directory`               | `build`        | Template generation directory |
| `kops_default_aws_account_limit`             | `[]`           | Limit generated cluster shell scripts to only run for the specified accounts to prevent accidental roll-out in wrong environment. |
| `kops_default_aws_iam_authenticator_enabled` | `false`        | Enable AWS IAM authenticator |

## Example definition

#### With sane defaults
When using the sane defaults, the only thing to configure for each cluster is

* cluster name
* s3 bucket name
* its worker nodes

```yml
kops_default_ssh_pub_key: ssh-ed25519 AAAANSLxbLKF6DL8GDFE70AAAAIP8kH/aB4LKI2+S6a921rCwl2OZdL09iBhGHJ23jk

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
# Generated shell scripts should only run in those AWS accounts.
# This prevents a user from accidentally rolling it out in wrong environments.
kops_default_aws_account_limit:
  - 123456789
  - 987654321

kops_cluster:
  - name: playground-cluster-shop.k8s.local
    master_public_name: api-playground-cluster-shop.example.net
    aws_iam_authenticator_enabled: true
    kube_api_server:
      oidcIssuerURL: https://oidc.example.net
      oidcClientID: clientID
      oidcUsernameClaim: email
      oidcUsernamePrefix: "oidc:"
      oidcGroupsClaim: groups
      oidcGroupsPrefix: "oidc:"
    # https://github.com/kubernetes/kops/blob/master/docs/cluster_spec.md#fileassets
    file_assets:
      - name: audit-policy-config
        path: /srv/kubernetes/audit/policy-config.yaml
        roles:
          - Master
        content: |
          apiVersion: audit.k8s.io/v1
          kind: Policy
          rules:
            - level: Metadata
    additionalPolicies:
        node: |
          [
            {
              "Effect": "Allow",
              "Action": ["route53:*"],
              "Resource": ["*"]
            }
          ]
        master: |
          [
            {
              "Effect": "Allow",
              "Action": ["route53:*"],
              "Resource": ["*"]
            }
          ]
    version: v1.10.4
    type: private
    region: eu-central-1
    image: kope.io/k8s-1.8-debian-jessie-amd64-hvm-ebs-2018-02-08
    s3_bucket_name: playground-cluster-shop-state-store
    ssh_pub_key: ssh-ed25519 AAAANSLxbLKF6DL8GDFE70AAAAIP8kH/aB4LKI2+S6a921rCwl2OZdL09iBhGHJ23jk
    api_access:
      - 185.28.180.95/32
    api_additional_sgs:
      - "security_group_name"
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
        cloud_labels:
          - key: team
            val: me
          - key: project
            value: ion
        node_labels:
          - key: name
            val: some-fancy-name
          - key: purpose
            value: something-important
    encryptionConfig:
      enabled: true
      image: "<PROVIDER>/aws-encryption-provider"
      kms_id: "12345678-9abc-defg-hijk-000000000001"
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
