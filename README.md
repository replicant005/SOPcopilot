# Squill

Video Demo (Click the banner below!):
[![Squill Demo](public/banner.png)](https://www.youtube.com/watch?v=OgVhrRd_cm8)

If you only want to interact with the first frontend pages, here is the deployed version: [https://sopcopilot.vercel.app/](https://squill-frontend-hygdkx9z9-toyakkis-projects.vercel.app)

Squill is an application that guides students through the Statement of Purpose writing process by generating thoughtful questions rather than writing the content for them. Squill will take some personal information such as application details and resume points and formulate a set of personalized and beneficial questions to inspire its users to write and be more clear about the identity they portray through their applications.

---
# Project Structure (Root Level)
```bash
.
main.py # Backend entrypoint (API + agent orchestration)
agents/                # LangGraph-based question generation pipeline
econf/                 # Environment configuration & runtime assets
frontend/              # Next.js (App Router) frontend application
public/                # Static assets
.env.example           # Environment variable template
README.md              # Project overview and architecture
```

# Frontend Project Structure
```bash
app/            # Next.js App Router pages
components/     # Reusable UI components
public/         # Static assets (images, SVGs, icons)
```

# Request Flow
``` bash
User (UI)
   ↓
Frontend (Next.js)
   ↓
Backend API (main.py)
   ↓
LangGraph Agent Pipeline
   ↓
Generated Questions
   ↓
Frontend 
   ↓
User (UI)
```

# Tech Stack Summary
**Frontend**
* Next.js (App Router), TypeScript
    * Chosen for fast iteration, server components, and strong typing.
    * And it is easy to vibe code.

**Backend**
* Python (main.py)
  * Simple, explicit orchestration layer that integrates cleanly with LangGraph.
  * And it is easy to vibe code.

**LLM Provider**
* Cohere (COHERE_API_KEY, see .env.example)
  * High-quality text generation with strong instruction-following.
  * And to support this great Canadian startup, eh. 

**Orchestration**

* LangGraph (agent workflows)
  * Provides explicit stateful graphs instead of brittle prompt chains.
  * And to win the Forresters Challenge: https://www.linkedin.com/feed/update/urn:li:activity:7419442041513963520/

# Quick Start
You will need to run both a frontend and backend server. Start with the backend.
### Download the Directory and Start a Terminal
Click the download button, then start a terminal at the directory you just downloaded, ``SOPcopilot``.

### Initialize a virtual environment and install dependencies
Ensure your new terminal is in the root directory, ``SOPcopilot``. Then, run:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Create a ``.env`` file and fill it out
Duplicate the ``.env.example`` file. Rename it to ``.env``. Then, replace ``COHERE_API_KEY=your_api_key`` with your API key from Cohere. If you do not have one, Cohere offers free keys (limit 20 calls/minute): sign up [here](https://dashboard.cohere.com/welcome/register). As a caveat, we unfortunately cannot guarantee full functionality with these free keys.

The first line should look something like ``COHERE_API_KEY=abcdefghijk1234jlkjfIJo3nFD(pa98sdUFJUCI`` (<— this is a fake key. Don't share your API keys!)

### Run ``main.py`` to start the backend server
Run the command:
```bash
python3 main.py
```
Then, leave this terminal running. *NOTE:* if you see an error message like "AttributeError: module 'tensorflow' has no attribute 'contrib'", run ``pip uninstall agents`` and try this step again.

### Open a new terminal
Open a new terminal in which to run the frontend server.

### Navigate to ``frontend``
In the terminal, move to the ``/frontend`` folder. If you're starting from the root directory, ``SOPcopilot``, run ``cd frontend``.

### Install Dependencies
From the ``frontend`` directory, run:
```bash
npm install
```

### Create a ``.env.local`` file and fill it out
Duplicate the file called ``.env.local.example``. Rename it ``.env.local``. Then, going back to the backend terminal, copy the bottom message that looks like this:
```Running on http://123.45.67.890:10000```
Paste that IP address into ``.env.local`` in place of ``YOUR_BACKEND_URL``. For example, the file should look like ``BACKEND_URL=http://123.45.67.890:10000``.

### Run the Frontend Server
Start the server with:
```bash
npm run dev
```

### View the Application
Once the server is running, open your browser and navigate to:
```
http://localhost:3000
```
And begin using the application. We hope you enjoy!
