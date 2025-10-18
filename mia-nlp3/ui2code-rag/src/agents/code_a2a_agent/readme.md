# Code Agent

## Docker commands
```bash
docker build --no-cache -t code-agent .
docker run --env-file .env -p 10001:10001 --name code-agent code-agent
```