FROM node:18-alpine

# Munkakönyvtár beállítása
WORKDIR /app

# Package fájlok másolása
COPY package*.json ./

# Függőségek telepítése
RUN npm install

# Forráskód másolása
COPY . .

# Port beállítása
EXPOSE 3000

# Next.js dev server indítása npx-szel hogy biztosan megtalálja
CMD ["npx", "next", "dev", "-H", "0.0.0.0"] 