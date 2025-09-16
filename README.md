# CIPP GDAP Invite Generator

A simple and secure web-based GDAP (Granular Delegated Admin Privileges) invite generator that integrates with the CIPP (CyberDrain Improved Partner Portal) API.

## ⚠️ SECURITY WARNING

**IMPORTANT: This application MUST be protected with Cloudflare Zero Trust before deployment.** 

This tool has access to your CIPP API and can generate GDAP invitations. **Never expose this application directly to the internet without proper authentication controls.** Always set up Cloudflare Zero Trust protection as the first step before deploying.


## 📋 Prerequisites

- Cloudflare account with Workers access and Zero Trust enabled
- CIPP instance with API access
- GitHub account

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

### 2. Fork Repository and Connect to Cloudflare

1. **Fork this repository** to your GitHub account and make it Private.
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
| `CIPP_API_CLIENT_ID` | Azure app registration client ID for CIPP API | `"REDACTED-CLIENT-ID"` |
| `CIPP_API_URL` | Your CIPP instance URL | `"https://cipp.example.com"` |
| `CIPP_TENANT_ID` | Azure tenant ID for authentication | `"REDACTED-TENANT-ID"` |
| `CIPP_ROLE_TEMPLATE_LOCK` | Lock to a specific role template (optional) | `"CIPP Defaults"` |
| `SUBDOMAIN` | Subdomain for routing (if using custom domains) | `"gdap"` |
| `THEME_PRIMARY_COLOR` | Primary color for the UI theme | `"#7189ff"` |

### Required Secrets (Cloudflare Dashboard)

| Secret | Description | How to Obtain |
|--------|-------------|---------------|
| `CIPP_API_SECRET` | Azure app registration client secret | Generated in Azure Portal under App Registration → Certificates & secrets |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CIPP_ROLE_TEMPLATE_LOCK` | Locks the app to use only a specific role template. When set, users cannot select different templates. Leave empty for normal template selection. | `""` (empty) |

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

## 🚀 Usage

1. **Access**: Navigate to your Zero Trust protected URL and authenticate
2. **Select Template**: Choose from available GDAP role templates (or use locked template if configured)
3. **Review Roles**: Verify the included roles in the selected template
4. **Generate Invite**: Click "Generate GDAP Invite" to create the relationship
5. **Copy URL**: Use the "Copy Invite URL" button to share with your customer

## 🎨 Customization

- **Theming**: Modify `THEME_PRIMARY_COLOR` in `wrangler.toml`
- **Branding**: Update `APP_NAME` and `LOGO_URL` in `wrangler.toml`
- **Custom Domains**: Configure in the `[[routes]]` section of `wrangler.toml`

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 👥 Authors

**Good Heart Tech** - *A nonprofit MSP providing free IT services to other nonprofits on a volunteer basis*

Good Heart Tech is a 501(c)(3) nonprofit organization dedicated to empowering other nonprofits through free technology services. Our team of volunteer IT professionals provides:

- **Managed IT Services**: Complete IT infrastructure management
- **Cloud Migration**: Secure transitions to cloud-based solutions
- **Cybersecurity**: Protecting nonprofit data and operations
- **Training & Support**: Empowering nonprofit staff with technology skills
- **Custom Solutions**: Tailored applications like this GDAP generator

Learn more about our mission and services at [goodhearttech.org](https://goodhearttech.org)

## 💖 Support Our Mission

If this tool has helped your organization, consider supporting Good Heart Tech's mission to provide free IT services to nonprofits worldwide: [https://goodhearttech.org/donate/](https://goodhearttech.org/donate/)

## 🔗 Related Projects

- [CIPP (CyberDrain Improved Partner Portal)](https://github.com/KelvinTegelaar/CIPP)
- [CIPP Application](https://cipp.app)
- [Cloudflare Workers Documentation](https://developers.cloudflare.com/workers/)
