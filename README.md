# Force Posture Tracker

An open-source Streamlit app for logging and analyzing force posture events, powered by the Claude API.

## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Project Structure

```
├── app.py              # Main Streamlit app
├── pages/
│   └── about.py        # About page
├── data/
│   └── events.json     # Events database
├── utils/
│   ├── loader.py       # Load and filter events
│   └── parser.py       # Claude API event extractor
├── assets/
│   └── style.css       # Custom styling
└── requirements.txt
```

## Environment Variables

Set your Anthropic API key before running:

```bash
export ANTHROPIC_API_KEY=your_key_here
```
