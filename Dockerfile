# Use an appropriate base image
FROM node:14

# Install Python 3 and pip
RUN apt-get update && apt-get install -y python3 python3-pip

# Install Chrome dependencies
RUN apt-get install -y wget unzip xvfb libxi6 libgconf-2-4
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get update && apt-get install -y google-chrome-stable

# Download and install the specified version of ChromeDriver
RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/129.0.6668.70/linux64/chromedriver-linux64.zip -O /tmp/chromedriver.zip \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64

# Install Python dependencies
RUN pip3 install selenium

# Set the working directory
WORKDIR /app

# Copy your application code
COPY . .

# Install Node.js dependencies
RUN npm install

# Expose the port the app runs on
EXPOSE 8080

# Run your application
CMD ["sh", "-c", "node server.js"]