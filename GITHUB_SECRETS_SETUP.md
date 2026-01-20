# GitHub Secrets Setup Guide

Follow these steps to configure GitHub Actions for automated deployments.

## Step 1: Get Your SSH Private Key

```bash
cat ~/.ssh/id_ed25519_beget_vps
```

This will output something like:
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
...
-----END OPENSSH PRIVATE KEY-----
```

**Copy the ENTIRE output** (including the BEGIN and END lines).

## Step 2: Add Secrets to GitHub

1. Go to your repository: https://github.com/AgasiArgent/deficit
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

Add the following secret:

### VPS_SSH_KEY

- **Name**: `VPS_SSH_KEY`
- **Value**: Paste the entire SSH private key from Step 1

Click **Add secret**

## Step 3: Verify Existing Secrets

Make sure these secrets already exist (they should):

- ✅ `VPS_HOST` = `217.26.25.207`
- ✅ `VPS_USERNAME` = `root`
- ✅ `TELEGRAM_BOT_TOKEN` = `8586048540:AAEGaQ_daca976d1n-r0e2RqE9nRX4fiNIE`
- ✅ `OWNER_USER_ID` = `43379140`

## Step 4: Remove Old Password Secret

After adding `VPS_SSH_KEY`, delete the old `VPS_PASSWORD` secret:

1. Find `VPS_PASSWORD` in the secrets list
2. Click **Remove** or the trash icon
3. Confirm deletion

**Why?** SSH keys are more secure than passwords, and we don't need both.

## Step 5: Test the Workflow

After adding the secret, test the deployment:

### Option A: Push a commit (triggers automatically)

```bash
git add .
git commit -m "test: trigger deployment"
git push
```

### Option B: Manual trigger

1. Go to https://github.com/AgasiArgent/deficit/actions
2. Click **Deploy Deficit Bot** workflow
3. Click **Run workflow** → **Run workflow**

## Step 6: Verify Deployment

1. Go to https://github.com/AgasiArgent/deficit/actions
2. Watch the workflow run (takes ~2-3 minutes)
3. Check that all steps are green ✅

If successful, you'll see:
- ✅ Checkout code
- ✅ Deploy to VPS
- "🎉 Deployment complete!" in logs

## Troubleshooting

### Error: "Permission denied (publickey)"

**Solution:** The SSH key isn't properly configured. Double-check:
1. You copied the ENTIRE private key (including BEGIN/END lines)
2. No extra spaces or line breaks were added
3. The public key is on the VPS (we already confirmed it is)

### Error: "Host key verification failed"

**Solution:** This shouldn't happen with the current setup, but if it does, the workflow needs `StrictHostKeyChecking` disabled.

### Workflow still using password?

**Solution:** Make sure you committed and pushed the updated `.github/workflows/deploy.yml` file.

---

## Summary

Once configured, every push to `master` will:
1. ✅ Clone/pull latest code to VPS
2. ✅ Build Docker image
3. ✅ Run database migrations
4. ✅ Restart the bot
5. ✅ Show logs

**All automatic! 🚀**
