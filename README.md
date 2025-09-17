# CIPP GDAP Invite Generator

A simple and secure web-based GDAP (Granular Delegated Admin Privileges) invite generator that integrates with the CIPP (CyberDrain Improved Partner Portal) API.

## ⚠️ SECURITY WARNING

**IMPORTANT: This application MUST be protected with Cloudflare Zero Trust before deployment.** 

This tool has access to your CIPP API and can generate GDAP invitations. **Never expose this application directly to the internet without proper authentication controls.** Always set up Cloudflare Zero Trust protection as the first step before deploying.


## 📋 Prerequisites

- Cloudflare account with Workers access and Zero Trust enabled
- CIPP instance with API access
- GitHub account

## 🔐 CIPP API Setup

To use this application, you need to configure API access in your CIPP instance:

1. **Generate API Key Credentials in CIPP**:
   - Log into your CIPP instance
   - Generate an API key credential
   - Store the credentials in a safe place (you'll need them for configuration)

2. **Create CIPP Role with Required Permissions**:
   - Create a new CIPP role with only these permissions:
     - `CIPP.Core.Read`
     - `Tenant.Relationship.ReadWrite`

3. **Assign Role to API Key**:
   - Assign the newly created role to your API key

4. **Configure Credentials**:
   - Input the API credentials into your `wrangler.toml` file
   - Add the API secret to Cloudflare secrets (as shown in deployment steps above)

## 🛠️ Setup Instructions

### 1. Set Up Cloudflare Zero Trust Protection

**CRITICAL FIRST STEP**: Before deploying this application, you must set up Cloudflare Zero Trust to protect access.

1. **Log in to Cloudflare Dashboard** and navigate to **Zero Trust**
2. **Create a new Application**:
   - Go to **Access** → **Applications**
   - Click **Add an application**
   - Select **Self-hosted**
   - Enter your application details:
     - **Application name**: `CIPP GDAP Generator`
     - **Subdomain**: Choose the subdomain you'll use (e.g., `gdap`)
     - **Domain**: Your Cloudflare domain
     - **Full URL**: `https://gdap.yourdomain.com` (replace with your actual subdomain and domain)
3. **Configure Access Policies**:
   - Add policies to restrict access to authorized users/groups
   - Configure authentication methods (email, SSO, etc.)
   - Set session duration and other security settings
4. **Save the application** - This MUST be done before deploying the Worker

### 2. Copy Repository and Connect to Cloudflare

1. **Copy the contents of this repository** to a new GitHub repo and make it Private.
2. **Connect GitHub to Cloudflare**:
   - In Cloudflare Dashboard, go to **Workers & Pages**
   - Click **Create application**
   - Select **Pages** → **Connect to Git**
   - Connect your GitHub account if not already connected
   - Select your forked repository: `CIPP-GDAP-Invite-Generator`

### 3. Configure wrangler.toml

Edit the `wrangler.toml` file with your specific configuration:

```toml
name = "your-app-name"
main = "src/worker.ts"
compatibility_date = "2025-08-05"
compatibility_flags = ["nodejs_compat"]

# Configure your custom domain (optional)
[[routes]]
pattern = "your-domain.com"
custom_domain = true

[vars]
# App Configuration
APP_NAME = "Your GDAP Generator"
LOGO_URL = "https://your-domain.com/logo.svg"
SUBDOMAIN = "your-subdomain"

# CIPP API Configuration
CIPP_API_CLIENT_ID = "your-client-id"
CIPP_API_URL = "https://your-cipp-instance.azurewebsites.net"
CIPP_TENANT_ID = "your-tenant-id"

# Theme Configuration
THEME_PRIMARY_COLOR = "#7189ff"
```

### 4. Deploy to Cloudflare

1. **Configure deployment settings** in your forked repository:
   - Edit the `wrangler.toml` file with your specific configuration (see configuration section above)
   - Commit and push changes to your GitHub repository

2. **Deploy from Cloudflare Dashboard**:
   - In your connected Cloudflare Pages project, go to **Deployments**
   - Cloudflare will automatically deploy when you push changes to your repository
   - Alternatively, click **Create deployment** for manual deployment

3. **Add the secret variable**:
   - In Cloudflare Dashboard, navigate to **Workers & Pages**
   - Select your deployed application
   - Go to **Settings** → **Variables and Secrets**
   - Click **+ Add** and create:
     - **Variable name**: `CIPP_API_SECRET`
     - **Value**: Your CIPP API secret key
     - **Type**: Secret (encrypted)

4. **Verify Zero Trust Protection**:
   - Access your application URL
   - Confirm that Cloudflare Zero Trust authentication is required
   - Test that unauthorized users cannot access the application

## 🔧 Environment Variables

### Required Variables (wrangler.toml)

| Variable | Description | Example |
|----------|-------------|---------|
| `APP_NAME` | Display name for your application | `"CIPP GDAP Generator"` |
| `LOGO_URL` | URL to your application logo/favicon | `"https://example.com/logo.svg"` |
| `CIPP_API_CLIENT_ID` | Client ID for CIPP API | `"REDACTED-CLIENT-ID"` |
| `CIPP_API_URL` | Your CIPP instance URL | `"https://cipp.example.com"` |
| `CIPP_TENANT_ID` | MSP tenant ID for authentication | `"REDACTED-TENANT-ID"` |
| `CIPP_ROLE_TEMPLATE_LOCK` | Lock to a specific role template (optional) | `"CIPP Defaults"` |
| `SUBDOMAIN` | Subdomain for routing (if using custom domains) | `"gdap"` |
| `THEME_PRIMARY_COLOR` | Primary color for the UI theme | `"#7189ff"` |

### Required Secrets (Cloudflare Dashboard)

| Secret | Description | How to Obtain |
|--------|-------------|---------------|
| `CIPP_API_SECRET` | CIPP API client secret | Generated in the CIPP API setup section |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CIPP_ROLE_TEMPLATE_LOCK` | Locks the app to use only a specific role template. When set, users cannot select different templates. Leave empty for normal template selection. | `""` (empty) |


## 📄 License

This project is open source and available under the [GPL-3.0 License](LICENSE).

## 👥 Authors and Support 💖

**Good Heart Tech** - *A nonprofit 501(c)(3) MSP providing free IT services to other nonprofits on a volunteer basis*

Learn more about our mission and services at [goodhearttech.org](https://goodhearttech.org)

## 🔗 Related Projects & Acknowledgments
A huge thank you to the entire CIPP team for their incredible work and dedication. Your tools have been a game-changer for Good Heart Tech and continue to provide immense value to the entire MSP community. The innovation, thoughtfulness, and support you bring make complex challenges far more manageable, and we’re deeply grateful for the impact you’ve had on our work.
- [CIPP (CyberDrain Improved Partner Portal)](https://github.com/KelvinTegelaar/CIPP)
- [CIPP Application](https://cipp.app)
