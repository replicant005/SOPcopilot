# Squill

<p align="center">
  <img src="banner.png" alt="Banner Image" />
</p>

Squill is an application that guides students through the Statement of Purpose writing process by generating thoughtful questions rather than writing the content for them. Squill will take some personal information such as application details and resume points and formulate a set of personalized and beneficial questions to inspire its users to write and be more clear about the identity they portray through their applications.

Video Demo: ...

---

# Squill Frontend

This directory contains the frontend for **Squill**, a web application designed to guide students through writing Statements of Purpose using thoughtful, AI-generated questions.

The frontend is built with **Next.js** and **TypeScript**, along with standard web technologies such as HTML and CSS.

---

## Prerequisites

Before running the frontend locally, ensure you have the following installed:

### Node.js and npm
npm is required to install dependencies and run the development server.

Download Node.js (which includes npm) from:
https://nodejs.org/

Verify installation by running:
```bash
node -v
npm -v
```

## Getting Started
1. ### Install Dependencies
From the frontend directory, run:
```bash
npm install
```

This installs all required packages listed in package.json.

2. ### Run the Development Server
Start the local development server with:
```bash
npm run dev
```

3. ### View the Application
Once the server is running, open your browser and navigate to:
```bash
[npm run dev](http://localhost:3000)
```
The page will automatically reload as you make changes to the code.


## Frontend Project Structure
```bash
app/            # Next.js App Router pages
components/     # Reusable UI components
public/         # Static assets (images, SVGs, icons)
```
