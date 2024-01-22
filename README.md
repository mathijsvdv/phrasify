# AnkiConvo
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/mathijsvdv/anki-convo/main.svg)](https://results.pre-commit.ci/latest/github/mathijsvdv/anki-convo/main)

Anki add-on that uses LLMs like ChatGPT to turn your vocabulary flashcards into fresh sentences on the fly and have conversations using your vocabulary.

-----

**Table of Contents**

- [Installation](#installation)
- [License](#license)

## Installation

## Deployment
To create the necessary resources on AWS, including a VPC and an EKS cluster, run the following command:
```bash
cd terraform
terraform init
terraform apply
```

Then you need to configure `kubectl` to use the EKS cluster:
```bash
make eksconfig
```

To deploy the API to EKS, run the following command:
```bash
make deploy K8S_ENV=dev-eks
```

### Structure of the EKS cluster
The EKS cluster is deployed in a VPC with 3 public and 3 private subnets. The public
subnets are used for the EKS control plane and the private subnets are used for the worker nodes.
The worker nodes are deployed in an autoscaling group with a minimum of 0 and a maximum of 5 nodes.

The EKS cluster is deployed with the following add-ons:
- [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.2/)
- [External DNS](https://github.com/kubernetes-sigs/external-dns)

Upon deletion of the EKS cluster, all resources created by the add-ons are automatically deleted.

## License
`anki-convo` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

## Development
### Branching strategy
This project uses the [GitHub Flow](https://githubflow.github.io/]) branching strategy. No pushes to `main` are allowed, only pull requests from feature branches that branch off of `main`. Each feature branch has the following naming convention:
```
git branch <issue-id>-<description-in-kebab-case>
```
It's recommended to open an issue in GitHub before you create a feature branch so that you can more easily track the work and provide much more context.

> **Example**: `git branch 123-cache-cards` is a feature branch implementing caching of cards, referring to Issue 123.
