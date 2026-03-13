# Deploy Checklist

Pre-launch audit for photostash. Fix all BLOCKING items before running `just helm-install`.

---

## BLOCKING (must fix before deploy)

### [terraform/cloudflare] `terraform.tfvars` missing

Copy from `terraform/cloudflare/terraform.tfvars.example` and fill in:

- `cloudflare_api_token` (empty in example)
- `domain` (placeholder `"example.com"`)
- `server_ip` (empty — set from `terraform output -raw server_ip` after Hetzner apply)

### [helm/site] `values.secret.yaml` missing

Copy from `helm/site/values.secret.yaml.example` and fill in all `CHANGE_ME` values:

- `postgres.volumePath` — from `terraform -chdir=terraform/hetzner output -raw postgres_volume_mount_path`
- `domain`
- `image` — `ghcr.io/CHANGE_ME/photostash:main`
- `app.admins`
- `app.allowedHosts`
- `app.contactEmail`
- `app.mailgunSenderDomain`
- `secrets.postgresPassword`
- `secrets.djangoSecretKey`
- `secrets.redisPassword`
- `secrets.cloudflare.cert` (PEM content from Cloudflare origin certificate)
- `secrets.cloudflare.key` (PEM content from Cloudflare origin private key)

### [helm/observability] `values.secret.yaml` missing

Copy from `helm/observability/values.secret.yaml.example` and fill in:

- `kube-prometheus-stack.grafana.adminPassword`
- `grafana.ingress.hosts[0]` (still `grafana.example.com`)

### [GitHub Actions secrets] Not configured

`gh secret list` returned empty. These secrets are referenced in workflows but not set:

- `HELM_VALUES_SECRET`
- `KUBECONFIG_BASE64`

Set them via: `gh secret set <NAME>`

### [helm/site] Object storage not enabled

The app has a photo upload feature. With `useS3Storage: "false"` (the default), uploaded
files live on the pod and will be lost on every redeploy.

Provision the bucket first:

```bash
cd terraform/storage
export TF_VAR_access_key=<from Hetzner console>
export TF_VAR_secret_key=<from Hetzner console>
terraform init && terraform apply
```

Then fill in `helm/site/values.secret.yaml`:

```yaml
secrets:
  useS3Storage: "true"
  hetznerStorageAccessKey: "<access-key>"
  hetznerStorageSecretKey: "<secret-key>"
  hetznerStorageBucket: "photostash-media"
  hetznerStorageEndpoint: "https://fsn1.your-objectstorage.com"
  hetznerStorageRegion: "fsn1"
```

S3 credentials are generated in: Hetzner console > Cloud > Security > S3 credentials > Generate credentials

**What Terraform gives you vs what you supply:**

| Helm key | Source |
|---|---|
| `hetznerStorageAccessKey` | The access key you generated in the Hetzner console (same value passed as `TF_VAR_access_key`) |
| `hetznerStorageSecretKey` | The secret key from the Hetzner console (same value passed as `TF_VAR_secret_key`) |
| `hetznerStorageBucket` | `terraform output -raw bucket_name` |
| `hetznerStorageEndpoint` | `terraform output -raw endpoint_url` |
| `hetznerStorageRegion` | Same as the `location` variable you passed in (default: `fsn1`) |

Terraform only creates the bucket — it does not generate the credentials. The access/secret key
pair comes from the Hetzner console and is only shown once. Save it in a password manager before
running Terraform.

---

## ADVISORY (review before go-live)

- **[terraform/hetzner]** `admin_ips = ["0.0.0.0/0", "::/0"]` — SSH (port 22) and K3s API
  (port 6443) are open to the entire internet. Restrict to your own IP or VPN exit node
  before first `terraform apply`.
- **[helm/site]** `app.adminUrl` will default to `"admin/"` — change to a non-guessable
  path for security.
- **[helm/site]** `app.metaAuthor`, `app.metaDescription`, `app.metaKeywords` — fill in
  before go-live (SEO/branding).
- **[~/.kube/photostash.yaml]** Run `just get-kubeconfig` after Hetzner provisioning to
  confirm the kubeconfig exists.

---

## OK

- `terraform/hetzner/terraform.tfvars` — `hcloud_token`, `ssh_public_key`, and `k3s_token`
  are all set with non-placeholder values.

---

## Deploy sequence (once all BLOCKING items are resolved)

1. `terraform apply` in `terraform/hetzner/` — note `server_ip` and `postgres_volume_mount_path` outputs
2. `terraform apply` in `terraform/cloudflare/` (after creating `terraform.tfvars`)
3. `terraform apply` in `terraform/storage/` — provision the media bucket
4. Create `helm/site/values.secret.yaml` with all secrets filled in
5. Create `helm/observability/values.secret.yaml` with all secrets filled in
6. Add `HELM_VALUES_SECRET` and `KUBECONFIG_BASE64` to GitHub repo secrets
7. `just get-kubeconfig` — fetch kubeconfig from the cluster
8. `just helm-install`
