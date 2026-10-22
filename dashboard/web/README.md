# dashboard/web

The PREPLINE dashboard front end. See [../README.md](../README.md) for how to start it, the pages, the data it reads
and the tests.

```powershell
npm install
npx vite --port 5173      # needs the API on http://127.0.0.1:8000 (VITE_API_BASE overrides)
npx tsc -b; npx vite build
npx playwright test
```
