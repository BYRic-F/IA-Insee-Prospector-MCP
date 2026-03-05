FROM astral/uv:python3.14-trixie-slim

# Install needed apt packages
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
WORKDIR /app
ADD . /app/
RUN uv sync --frozen && \
    uv pip install streamlit google-genai plotly

# Expose port (default 8000, configurable via MCP_PORT env var) /8501 Streamlit
EXPOSE 8000
EXPOSE 8501

# Run
ENTRYPOINT ["uv", "run"]
#CMD ["python", "main.py"]
CMD ["sh", "-c", "python main.py & streamlit run app_web.py --server.port 8501 --server.address 0.0.0.0"]
