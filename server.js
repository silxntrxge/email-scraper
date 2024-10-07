const express = require('express');
const bodyParser = require('body-parser');
const { spawn } = require('child_process');
const fs = require('fs');
const axios = require('axios');

const app = express();

// Increase JSON size limit to 100mb
app.use(bodyParser.json({ limit: '100mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '100mb' }));

// Log raw request body (truncated for very large payloads)
app.use((req, res, next) => {
    let data = '';
    req.on('data', chunk => {
        data += chunk;
        if (data.length > 1000000) { // Log only first 1MB
            console.log('Raw request body (truncated):', data.slice(0, 1000000));
            req.removeAllListeners('data');
        }
    });
    req.on('end', () => {
        if (data.length <= 1000000) {
            console.log('Raw request body:', data);
        }
        next();
    });
});

const PORT = process.env.PORT || 10000;

app.post('/scrape-emails', (req, res) => {
    console.log('Received POST request. Body length:', JSON.stringify(req.body).length);
    const { recordId, names, domain, niche, webhook } = req.body;

    // Write the configuration to a file
    const config = JSON.stringify({ names, domain, niche });
    fs.writeFileSync('config.json', config);

    console.log('Starting email scraping process...');
    const pythonProcess = spawn('python3', ['scraper.py']);

    let pythonOutput = '';

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Python stdout: ${data}`);
        pythonOutput += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python Error: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Python script exited with code ${code}`);
        
        if (code === 0) {
            // Read the emails from the file
            fs.readFile('final_combined_emails.txt', 'utf8', (err, data) => {
                if (err) {
                    console.error('Error reading emails file:', err);
                    res.status(500).send('Error reading emails');
                    return;
                }

                const emails = data.split('\n').filter(email => email.trim() !== '');

                // Send the webhook with recordId included
                axios.post(webhook, { recordId, emails })
                    .then(() => {
                        console.log('Webhook sent successfully');
                        res.status(200).send('Emails scraped and webhook sent');
                    })
                    .catch((error) => {
                        console.error('Error sending webhook:', error);
                        res.status(500).send('Error sending webhook');
                    });
            });
        } else {
            console.error('Error during scraping process:', pythonOutput);
            res.status(500).send('Error during scraping process');
        }
    });
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).send('Something broke!');
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});