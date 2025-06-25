FROM node:18-alpine

WORKDIR /app

# Globális Next.js telepítése
RUN npm install -g next

# Package fájlok másolása
COPY package*.json ./

# Függőségek telepítése
RUN npm install

# Forráskód másolása
COPY . .

# Port beállítása
EXPOSE 3000

# Alkalmazás indítása fejlesztői módban
CMD ["next", "dev", "--hostname", "0.0.0.0"] 