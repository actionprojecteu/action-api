FROM node:11.3

WORKDIR /usr/src/app
# update system
RUN apt-get update

# Install app dependencies
# A wildcard is used to ensure both package.json AND package-lock.json are copied
# where available (npm@5+)
COPY package*.json ./

# run server
RUN npm install
COPY . .
CMD [ "npm", "start" ]

# port
EXPOSE 8888
