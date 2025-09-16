interface Env {
  CIPP_API_CLIENT_ID: string;
  CIPP_API_URL: string;
  CIPP_TENANT_ID: string;
  CIPP_API_SECRET: string;
  THEME_PRIMARY_COLOR: string;
  APP_NAME: string;
  LOGO_URL: string;
  CIPP_ROLE_TEMPLATE_LOCK?: string;
}

// Token cache to avoid repeated Microsoft API calls
let tokenCache: { token: string; expires: number } | null = null;

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    
    // Serve the HTML interface
    if (request.method === 'GET' && url.pathname === '/') {
      return new Response(getHTML(env), {
        headers: { 'Content-Type': 'text/html' },
      });
    }
    
    
    // Handle role templates requests
    if (request.method === 'GET' && url.pathname === '/api/templates') {
      try {
        const token = await getToken(env);
        
        const response = await fetch(`${env.CIPP_API_URL}/api/ExecGDAPRoleTemplate`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (!response.ok) {
          throw new Error(`CIPP API error: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        return new Response(JSON.stringify(data), {
          headers: { 'Content-Type': 'application/json' },
        });
      } catch (error) {
        console.error('Templates request failed:', error);
        return new Response(JSON.stringify({ 
          error: 'Failed to fetch templates', 
          details: error.message 
        }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        });
      }
    }

    // Handle GDAP invite generation
    if (request.method === 'POST' && url.pathname === '/api/generate-invite') {
      try {
        const token = await getToken(env);
        const body = await request.json() as { roleMappings: any[] };
        
        const response = await fetch(`${env.CIPP_API_URL}/api/ExecGDAPInvite`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ roleMappings: body.roleMappings }),
        });
        
        if (!response.ok) {
          throw new Error(`CIPP API error: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        return new Response(JSON.stringify(data), {
          headers: { 'Content-Type': 'application/json' },
        });
      } catch (error) {
        console.error('Invite generation failed:', error);
        return new Response(JSON.stringify({ 
          error: 'Invite generation failed', 
          details: error.message 
        }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        });
      }
    }
    
    return new Response('Not Found', { status: 404 });
  },
};

async function getToken(env: Env): Promise<string> {
  // Check if we have a valid cached token
  if (tokenCache && Date.now() < tokenCache.expires) {
    console.log('Using cached Microsoft token');
    return tokenCache.token;
  }

  console.log('Fetching new token from Microsoft');
  const tokenUrl = `https://login.microsoftonline.com/${env.CIPP_TENANT_ID}/oauth2/v2.0/token`;
  
  const response = await fetch(tokenUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      client_id: env.CIPP_API_CLIENT_ID,
      client_secret: env.CIPP_API_SECRET,
      scope: `api://${env.CIPP_API_CLIENT_ID}/.default`,
      grant_type: 'client_credentials',
    }),
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Microsoft token request failed: ${response.status} ${response.statusText} - ${errorText}`);
  }
  
  const data = await response.json() as { access_token: string; expires_in: number };
  
  // Cache the token (expires_in is usually 3599 seconds = ~1 hour)
  // Cache for 50 minutes to be safe (10 minutes before actual expiry)
  tokenCache = {
    token: data.access_token,
    expires: Date.now() + (data.expires_in - 600) * 1000
  };
  
  console.log(`Token cached, expires in ${data.expires_in} seconds`);
  return data.access_token;
}

function getHTML(env: Env): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${env.APP_NAME}</title>
    <link rel="icon" type="image/svg+xml" href="${env.LOGO_URL}">
    <link rel="alternate icon" href="${env.LOGO_URL}">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #0f0f23;
            color: #e8e8e8;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: #1a1a2e;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            padding: 2rem;
            width: 100%;
            max-width: 600px;
            border: 1px solid #2a2a3e;
        }
        
        .header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .logo {
            width: 48px;
            height: 48px;
            margin: 0 auto 1rem;
        }
        
        h1 {
            color: #ffffff;
            font-size: 1.75rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            color: #a8a8a8;
            font-size: 0.9rem;
        }
        
        .status-message {
            margin-bottom: 1.5rem;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            font-size: 0.9rem;
            display: none;
        }
        
        .status-success {
            background: rgba(40, 167, 69, 0.1);
            border: 1px solid #28a745;
            color: #4caf50;
        }
        
        .status-error {
            background: rgba(220, 53, 69, 0.1);
            border: 1px solid #dc3545;
            color: #f44336;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        label {
            display: block;
            margin-bottom: 0.5rem;
            color: #d0d0d0;
            font-weight: 500;
        }
        
        select, button {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #3a3a4a;
            border-radius: 8px;
            background: #2a2a3a;
            color: #e8e8e8;
            font-size: 1rem;
            transition: all 0.2s ease;
        }
        
        select:focus, button:focus {
            outline: none;
            border-color: ${env.THEME_PRIMARY_COLOR};
            box-shadow: 0 0 0 3px rgba(113, 137, 255, 0.1);
        }
        
        select:hover {
            border-color: #4a4a5a;
        }
        
        select:disabled {
            background: #1a1a2a !important;
            color: #888 !important;
            cursor: not-allowed !important;
            opacity: 0.7;
        }
        
        .roles-list {
            background: #252535;
            border: 1px solid #3a3a4a;
            border-radius: 8px;
            padding: 1rem;
            max-height: 200px;
            overflow-y: auto;
            margin-top: 0.5rem;
        }
        
        .role-item {
            padding: 0.5rem 0;
            border-bottom: 1px solid #3a3a4a;
            color: #c8c8c8;
            font-size: 0.9rem;
        }
        
        .role-item:last-child {
            border-bottom: none;
        }
        
        .generate-btn {
            background: linear-gradient(135deg, ${env.THEME_PRIMARY_COLOR}, #5a6bcf);
            border: none;
            color: white;
            font-weight: 600;
            cursor: pointer;
            margin-top: 1rem;
            position: relative;
            overflow: hidden;
        }
        
        .generate-btn:disabled {
            background: #3a3a4a;
            cursor: not-allowed;
            opacity: 0.6;
        }
        
        .generate-btn:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(113, 137, 255, 0.3);
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 1rem;
            color: #a8a8a8;
        }
        
        .initial-loading {
            text-align: center;
            padding: 3rem 1rem;
            color: #a8a8a8;
        }
        
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid #3a3a4a;
            border-radius: 50%;
            border-top-color: ${env.THEME_PRIMARY_COLOR};
            animation: spin 1s ease-in-out infinite;
            margin-right: 0.5rem;
        }
        
        .large-spinner {
            width: 32px;
            height: 32px;
            border: 3px solid #3a3a4a;
            border-top-color: ${env.THEME_PRIMARY_COLOR};
            margin: 0 auto 1rem;
        }
        
        .loading-text {
            font-size: 1.1rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }
        
        .loading-subtext {
            font-size: 0.9rem;
            opacity: 0.7;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .results {
            margin-top: 2rem;
            padding: 1rem;
            background: #252535;
            border-radius: 8px;
            border: 1px solid #3a3a4a;
            display: none;
        }
        
        .success {
            border-color: #28a745;
            background: rgba(40, 167, 69, 0.1);
        }
        
        .error {
            border-color: #dc3545;
            background: rgba(220, 53, 69, 0.1);
        }
        
        .message {
            margin-bottom: 1rem;
            font-size: 0.95rem;
            line-height: 1.4;
        }
        
        .url-buttons {
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
        }
        
        .url-btn {
            flex: 1;
            min-width: 160px;
            padding: 0.75rem 1rem;
            background: #3a3a4a;
            border: 1px solid #4a4a5a;
            color: #e8e8e8;
            text-decoration: none;
            border-radius: 6px;
            text-align: center;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.2s ease;
            display: inline-block;
            cursor: pointer;
        }
        
        .url-btn:hover {
            background: #4a4a5a;
            border-color: ${env.THEME_PRIMARY_COLOR};
            transform: translateY(-1px);
        }
        
        .copy-btn {
            background: linear-gradient(135deg, ${env.THEME_PRIMARY_COLOR}, #5a6bcf);
            border-color: ${env.THEME_PRIMARY_COLOR};
            color: white;
        }
        
        .copy-btn:hover {
            background: linear-gradient(135deg, #5a6bcf, ${env.THEME_PRIMARY_COLOR});
            border-color: #5a6bcf;
        }
        
        
        .hidden {
            display: none !important;
        }
        
        
        @media (max-width: 480px) {
            .container {
                padding: 1.5rem;
            }
            
            .url-buttons {
                flex-direction: column;
            }
            
            .url-btn {
                min-width: auto;
            }
            
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="${env.LOGO_URL}" alt="Logo" class="logo">
            <h1>GDAP Invite Generator</h1>
            <p class="subtitle">Generate Microsoft 365 GDAP relationship invites using the CIPP API.</p>
        </div>
        
        <div class="initial-loading" id="initialLoading">
            <div class="large-spinner spinner"></div>
            <div class="loading-text">Loading Application</div>
            <div class="loading-subtext">Connecting to CIPP API and retrieving role templates...</div>
        </div>
        
        <div class="status-message" id="statusMessage"></div>
        
        <div id="mainForm" class="hidden">
            <div class="form-group">
                <label for="templateSelect">Select Role Template:</label>
                <select id="templateSelect">
                    <option value="">Choose a template...</option>
                </select>
            </div>
            
            <div class="form-group" id="rolesGroup" style="display: none;">
                <label id="rolesLabel">Roles in selected template:</label>
                <div class="roles-list" id="rolesList"></div>
            </div>
            
            <button class="generate-btn" id="generateBtn" disabled>
                <span id="btnText">Generate GDAP Invite</span>
                <div class="loading" id="btnLoading">
                    <div class="spinner"></div>
                    Generating invite...
                </div>
            </button>
        </div>
        
        <div class="results" id="results"></div>
    </div>

    <script>
        let templates = [];
        let selectedTemplate = null;
        const roleTemplateLock = ${JSON.stringify(env.CIPP_ROLE_TEMPLATE_LOCK || '')};
        console.log('Template lock setting:', roleTemplateLock);

        async function initializeApp() {
            try {
                // Load role templates directly through our API
                await loadTemplates();
                
            } catch (error) {
                console.error('Initialization failed:', error);
                showStatusMessage('Failed to load application: ' + error.message, 'error');
                document.getElementById('initialLoading').classList.add('hidden');
            }
        }

        function showStatusMessage(message, type) {
            const statusEl = document.getElementById('statusMessage');
            statusEl.className = 'status-message status-' + type;
            statusEl.textContent = message;
            statusEl.style.display = 'block';
            
            // Auto-hide success messages after 3 seconds
            if (type === 'success') {
                setTimeout(() => {
                    statusEl.style.display = 'none';
                }, 3000);
            }
        }

        async function loadTemplates() {
            try {
                // Update loading message
                document.querySelector('.loading-text').textContent = 'Loading Role Templates';
                document.querySelector('.loading-subtext').textContent = 'Retrieving available GDAP templates...';
                
                const response = await fetch('/api/templates', {
                    method: 'GET'
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.details || 'Failed to fetch templates');
                }
                
                const data = await response.json();
                console.log('Templates loaded:', data);
                
                if (data.Results && data.Results.length > 0) {
                    templates = data.Results;
                    
                    // Always populate the template dropdown first
                    populateTemplateSelect();
                    
                    // Check if a specific template is locked
                    if (roleTemplateLock) {
                        const lockedTemplate = templates.find(t => t.TemplateId === roleTemplateLock);
                        if (lockedTemplate) {
                            // Auto-select the locked template
                            selectedTemplate = lockedTemplate;
                            document.getElementById('templateSelect').value = roleTemplateLock;
                            
                            // Disable the dropdown and style it as locked
                            const templateSelect = document.getElementById('templateSelect');
                            templateSelect.disabled = true;
                            templateSelect.style.background = '#1a1a2a';
                            templateSelect.style.color = '#888';
                            templateSelect.style.cursor = 'not-allowed';
                            
                            // Update the label to show it's locked
                            const templateLabel = templateSelect.previousElementSibling;
                            templateLabel.innerHTML = 'Role Template <span style="color: #a8a8a8; font-size: 0.85rem;">(locked by administrator)</span>:';
                            
                            // Load roles and enable Generate button
                            displayRoles(selectedTemplate.RoleMappings);
                            document.getElementById('generateBtn').disabled = false;
                            
                            showStatusMessage('Using locked template: ' + roleTemplateLock, 'success');
                        } else {
                            throw new Error('Locked template "' + roleTemplateLock + '" not found in available templates');
                        }
                    }
                    
                    document.getElementById('initialLoading').classList.add('hidden');
                    document.getElementById('mainForm').classList.remove('hidden');
                } else {
                    throw new Error('No role templates found in response');
                }
            } catch (error) {
                console.error('Error loading templates:', error);
                showStatusMessage('Failed to load role templates: ' + error.message, 'error');
                document.getElementById('initialLoading').classList.add('hidden');
            }
        }

        function populateTemplateSelect() {
            const select = document.getElementById('templateSelect');
            select.innerHTML += templates.map(template => 
                '<option value="' + template.TemplateId + '">' + template.TemplateId + '</option>'
            ).join('');
        }


        function onTemplateChange() {
            const templateId = document.getElementById('templateSelect').value;
            
            selectedTemplate = templateId ? templates.find(t => t.TemplateId === templateId) : null;
            
            if (selectedTemplate) {
                displayRoles(selectedTemplate.RoleMappings);
                document.getElementById('generateBtn').disabled = false;
            } else {
                document.getElementById('rolesGroup').style.display = 'none';
                document.getElementById('generateBtn').disabled = true;
            }
            
            hideResults();
        }

        function displayRoles(roles) {
            const rolesList = document.getElementById('rolesList');
            
            document.getElementById('rolesLabel').textContent = 'Roles in selected template (' + roles.length + '):';
            rolesList.innerHTML = roles.map(role => '<div class="role-item">' + role.RoleName + '</div>').join('');
            document.getElementById('rolesGroup').style.display = 'block';
        }

        async function generateInvite() {
            if (!selectedTemplate) return;
            
            const btn = document.getElementById('generateBtn');
            const btnText = document.getElementById('btnText');
            const btnLoading = document.getElementById('btnLoading');
            
            btn.disabled = true;
            btnText.classList.add('hidden');
            btnLoading.style.display = 'block';
            hideResults();
            
            try {
                const response = await fetch('/api/generate-invite', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ roleMappings: selectedTemplate.RoleMappings })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showResults(data);
                } else {
                    throw new Error(data.details || data.error || 'Failed to generate invite');
                }
            } catch (error) {
                console.error('Error generating invite:', error);
                showError(error.message || 'Failed to generate invite. Please try again.');
            } finally {
                btn.disabled = false;
                btnText.classList.remove('hidden');
                btnLoading.style.display = 'none';
            }
        }

        function showResults(data) {
            const results = document.getElementById('results');
            const isSuccess = data.Invite && data.Invite.InviteUrl;
            
            results.className = 'results ' + (isSuccess ? 'success' : 'error');
            
            let html = '<div class="message">' + (data.Message || 'No message provided') + '</div>';
            
            if (isSuccess) {
                html += '<div class="url-buttons">' +
                    '<button onclick="copyToClipboard(\\'' + data.Invite.InviteUrl + '\\', this)" class="url-btn copy-btn">Copy Invite URL</button>' +
                    '</div>';
            }
            
            results.innerHTML = html;
            results.style.display = 'block';
        }

        async function copyToClipboard(text, button) {
            const originalText = button.textContent;
            
            function setButtonSuccess() {
                button.textContent = 'Copied!';
                button.style.background = '#28a745';
                button.style.borderColor = '#28a745';
                
                setTimeout(() => {
                    button.textContent = originalText;
                    button.style.background = 'linear-gradient(135deg, ${env.THEME_PRIMARY_COLOR}, #5a6bcf)';
                    button.style.borderColor = '${env.THEME_PRIMARY_COLOR}';
                }, 2000);
            }
            
            try {
                await navigator.clipboard.writeText(text);
                setButtonSuccess();
            } catch (err) {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                
                try {
                    document.execCommand('copy');
                    setButtonSuccess();
                } catch (fallbackErr) {
                    button.textContent = 'Copy failed';
                    setTimeout(() => button.textContent = originalText, 2000);
                }
                
                document.body.removeChild(textArea);
            }
        }

        function showError(message) {
            const results = document.getElementById('results');
            results.className = 'results error';
            results.innerHTML = '<div class="message">' + message + '</div>';
            results.style.display = 'block';
        }

        function hideResults() {
            document.getElementById('results').style.display = 'none';
        }

        // Event listeners
        document.getElementById('templateSelect').addEventListener('change', onTemplateChange);
        document.getElementById('generateBtn').addEventListener('click', generateInvite);

        // Initialize the application
        initializeApp();
    </script>
</body>
</html>`;
}