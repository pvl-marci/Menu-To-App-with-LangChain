# Menu Creator AI

This project allows you to upload an image of a menu through a Telegram bot, which is then processed by an AI model to extract the relevant information and convert it into a CSV format. The CSV data is then loaded into a PostgreSQL database that is connected to Directus. Later, a web UI can be built to fetch the data from Directus.

## Features

- Upload an image of your menu through Telegram.
- AI extracts menu items and converts them into a CSV file.
- The CSV data is automatically uploaded to a PostgreSQL database.
- Data can be accessed via Directus for further management and retrieval.

## Prerequisites

I was utilizing a Directus instance to connect to my database and subsequently retrieve items for display in a web application.
