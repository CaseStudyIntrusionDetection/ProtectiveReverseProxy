# Development

## Starting in development mode (for the proxy application)
1. Run `docker-compose -f docker-compose.dev.yml up --build` in projects root
2. Open a shell in the container `docker-compose -f docker-compose.dev.yml exec protection_proxy bash`
3. Navigate: `cd /proxy/`
4. Start server in development mode `flask run --host=0.0.0.0 --port=5000 --reload`