# Visual Agent

## Docker comandos
```bash
docker build -t visual-agent .
docker run --env-file .env -p 10000:10000 --name visual-agent visual-agent
```