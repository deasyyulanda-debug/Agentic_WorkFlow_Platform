# 🚀 Frontend Installation Guide (Windows)

## Prerequisites Check

Before starting, verify you have Python installed:
```powershell
python --version
```
Should show: Python 3.11.x or higher ✅

## Step 1: Install Node.js

Node.js is required to run the Next.js frontend.

### Download Node.js

1. Visit: https://nodejs.org/
2. Download the **LTS (Long Term Support)** version (recommended)
3. Run the installer (`node-v18.x.x-x64.msi` or similar)

### Installation Steps

1. **Run the installer** - Double-click the downloaded `.msi` file
2. **Accept the license agreement**
3. **Choose installation location** - Default is fine (`C:\Program Files\nodejs`)
4. **Select components** - Check all boxes:
   - [x] Node.js runtime
   - [x] npm package manager
   - [x] Add to PATH (Important!)
   - [x] Tools for Native Modules (optional but recommended)
5. **Install**
6. **Restart your terminal** (PowerShell or Command Prompt)

### Verify Installation

Open a **new** PowerShell/Command Prompt window and run:

```powershell
node --version
npm --version
```

Expected output:
```
v18.19.0  (or higher)
10.2.3    (or higher)
```

✅ If you see version numbers, Node.js is installed correctly!

## Step 2: Install Frontend Dependencies

### Navigate to Frontend Directory

```powershell
cd C:\Users\amitt\Agentic_WorkFlow_Platform\apps\web
```

### Install All Packages

```powershell
npm install
```

This will install all required packages:
- Next.js 14
- React 19
- TanStack Query (React Query)
- Axios
- Tailwind CSS
- Radix UI components
- Lucide React icons
- date-fns
- sonner (notifications)
- And many more...

**Note**: This may take 2-5 minutes depending on your internet speed.

Expected output:
```
added 350 packages, and audited 351 packages in 2m

50 packages are looking for funding
  run `npm fund` for details

found 0 vulnerabilities
```

## Step 3: Configure Environment Variables

### Create Environment File

```powershell
# Copy example file
Copy-Item .env.local.example .env.local
```

Or manually:
1. Open `apps\web\.env.local.example` in Notepad
2. Copy the contents
3. Create a new file `apps\web\.env.local`
4. Paste the contents

### Verify Configuration

The `.env.local` file should contain:
```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

This tells the frontend where to find the backend API.

## Step 4: Start the Development Server

### Ensure Backend is Running

In a separate terminal, make sure the backend is running:

```powershell
# In a new PowerShell window
cd C:\Users\amitt\Agentic_WorkFlow_Platform\apps\api
.\venv\Scripts\activate
python run.py
```

Backend should be running at: http://localhost:8000

### Start Frontend

In your frontend terminal:

```powershell
npm run dev
```

Expected output:
```
  ▲ Next.js 14.x.x
  - Local:        http://localhost:3000
  - Network:      http://192.168.x.x:3000

 ✓ Ready in 3.2s
```

## Step 5: Open the Application

Open your browser and navigate to:

**http://localhost:3000**

You should see the landing page of the Agentic Workflow Platform!

### Available Pages

- **Landing**: http://localhost:3000
- **Dashboard**: http://localhost:3000/dashboard
- **Workflows**: http://localhost:3000/workflows
- **Runs**: http://localhost:3000/runs
- **Settings**: http://localhost:3000/settings

## 🎉 Success!

If you can see the landing page, congratulations! Your frontend is running successfully.

## Common Issues & Solutions

### Issue 1: "npm: command not found"

**Cause**: Node.js not installed or not added to PATH

**Solution**:
1. Install Node.js from nodejs.org
2. Restart your terminal
3. Verify with `npm --version`

### Issue 2: "Cannot find module 'next'"

**Cause**: Dependencies not installed

**Solution**:
```powershell
cd apps\web
Remove-Item -Recurse -Force node_modules
Remove-Item -Force package-lock.json
npm install
```

### Issue 3: "Port 3000 already in use"

**Cause**: Another application is using port 3000

**Solution A** - Kill the process:
```powershell
# Find process using port 3000
netstat -ano | findstr :3000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F
```

**Solution B** - Use a different port:
```powershell
$env:PORT=3001; npm run dev
```

Frontend will run on http://localhost:3001

### Issue 4: "Failed to fetch from http://localhost:8000"

**Cause**: Backend is not running or wrong URL

**Solution**:
1. Verify backend is running: http://localhost:8000/api/v1/health
2. Check `.env.local` has correct `NEXT_PUBLIC_API_URL`
3. Restart frontend after changing `.env.local`

### Issue 5: "Network error" or CORS issues

**Cause**: CORS not configured correctly

**Solution**:
1. Check backend CORS settings in `apps/api/src/core/config.py`
2. Ensure `http://localhost:3000` is in CORS origins
3. Restart both backend and frontend

### Issue 6: Build errors with TypeScript

**Cause**: TypeScript compilation errors

**Solution**:
```powershell
# Clear Next.js cache
Remove-Item -Recurse -Force .next

# Rebuild
npm run dev
```

### Issue 7: Slow installation on Windows

**Cause**: Windows Defender scanning each file

**Solution**:
Add `node_modules` folder to Windows Defender exclusions:
1. Open Windows Security
2. Virus & threat protection
3. Manage settings
4. Add exclusions
5. Add folder: `C:\Users\amitt\Agentic_WorkFlow_Platform\apps\web\node_modules`

## Development Tips

### Hot Reload

Next.js supports hot module replacement. Save any file and changes appear instantly in the browser!

### Clear Cache

If you experience issues:
```powershell
Remove-Item -Recurse -Force .next
npm run dev
```

### View Build Output

For production build:
```powershell
npm run build
npm start
```

### Inspect Network Requests

1. Open browser DevTools (F12)
2. Go to Network tab
3. See all API requests to backend
4. Check for errors or failed requests

## Next Steps

1. **Configure Providers**: 
   - Navigate to http://localhost:3000/settings
   - Add your OpenAI/Anthropic/Gemini/DeepSeek API key
   
2. **Create a Workflow**:
   - Go to http://localhost:3000/workflows
   - Click "New Workflow"
   - Add steps and configure

3. **Execute Workflow**:
   - Click "Run" on any workflow
   - Monitor execution in real-time

## Useful Commands

```powershell
# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linter
npm run lint

# Install specific package
npm install package-name

# Update all packages
npm update

# Check for outdated packages
npm outdated

# View installed packages
npm list --depth=0
```

## Additional Resources

- **Node.js Documentation**: https://nodejs.org/docs
- **Next.js Documentation**: https://nextjs.org/docs
- **npm Documentation**: https://docs.npmjs.com/
- **React Documentation**: https://react.dev/

## Support

If you encounter issues not covered here:
1. Check [DEPLOYMENT.md](../../DEPLOYMENT.md) for comprehensive troubleshooting
2. Review [apps/web/README.md](README.md) for frontend-specific details
3. Verify backend is running with correct CORS configuration

---

**Happy Coding!** 🚀

Once frontend is running, you'll have a complete full-stack Agentic Workflow Platform!
