# Infrastructure

Provisioning and runtime infrastructure definitions.

## Baseline Approach
- Terraform in `terraform/` for cloud resource provisioning.
- Kubernetes manifests in `kubernetes/` for workload deployment.
- Target runtime is GKE Autopilot for UDP/QUIC compatibility and reduced ops burden.

See `docs/architecture/adr-0001-runtime-and-deployment.md` for rationale.
