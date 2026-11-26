FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    "mcp>=1.0,<2" \
    "python-dotenv>=1.0,<2" \
    "langchain-tavily>=0.2,<1"

COPY server.py ./server.py

ENV PYTHONUNBUFFERED=1

CMD ["python", "server.py"]
