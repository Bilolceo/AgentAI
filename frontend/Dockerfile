FROM node:20-alpine

WORKDIR /app

# NEXT_PUBLIC_* must be present at build time (Next.js inlines them into the
# client bundle). The browser calls the backend on the host-published port.
ARG NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE

COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "start"]
