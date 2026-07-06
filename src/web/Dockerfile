FROM python:3.10-alpine

RUN apk add --no-cache \
    chromium \
    chromium-chromedriver \
    nss \
    freetype \
    harfbuzz \
    ttf-freefont \
    dbus
    
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/cache

COPY . .

RUN cp default_config.yml /app/cache/profile.yml

RUN chmod +x entrypoint.sh

EXPOSE 8080

CMD ["./entrypoint.sh"]