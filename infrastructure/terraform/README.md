# Terraform (Future)

This folder is a placeholder for future cloud deployment (e.g., EKS/AKS) once local workflows and OpenShift migration are complete.

Suggested future layout:
- `providers.tf` — provider config
- `backend.tf` — remote state (S3 + DynamoDB lock or Terraform Cloud)
- `network.tf` — VPC/subnets/security groups
- `cluster.tf` — Kubernetes/EKS cluster
- `registry.tf` — optionally manage GHCR creds as secrets in cluster
- `outputs.tf` — kubeconfig hints, cluster endpoints, etc.

For now, local Kubernetes (Docker Desktop) is the primary environment.
