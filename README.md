# 🧠 NeuroStudy Coach

AI-powered study planning for neurodivergent students. NeuroStudy Coach uses a PyTorch neural network to generate personalised study schedules based on your profile (ADHD, Autism, Dyslexia, Dyscalculia). All data stays on your machine.

---

## Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/omz-singer/NeuroStudy-Coach
cd NeuroStudy-Coach
```

### 2. Set up the environment
```bash
py -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```

### 3. Add your API key (for the AI Study Assistant)
Create a `.env` file in the project folder and add:
```
ANTHROPIC_API_KEY=your-key-here
```
Get a free key at https://console.anthropic.com

### 4. Run the app
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.
