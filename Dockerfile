# ---- Base image ----
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Fly will set PORT; default to 8080 for local runs
ENV PORT=8080

WORKDIR /app

# ---- System deps (minimal) ----
# If you later add packages that need compilation (e.g., some scientific libs),
# you may need build-essential. For most Dash stacks, this is fine as-is.
RUN pip install --no-cache-dir --upgrade pip

# ---- Install Python deps first (better layer caching) ----
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy app code ----
COPY . /app

# ---- Expose the port (mostly informational for many platforms) ----
EXPOSE 8080

# ---- Run ----
# main:server matches your main.py top-level `server = app.server`
# Bind to 0.0.0.0 so it's reachable outside the container.
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT} main:server"]