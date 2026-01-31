# Quiz Please Statistics Dashboard 📊

A Streamlit-based analytics dashboard for tracking Quiz Please game statistics, team performance, and head-to-head comparisons.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white)

## Features

### 🏠 Main Page
- Quick overview statistics (Total Teams, Total Games, Latest Game)
- Game selector with detailed leaderboard
- Winner highlights with podium-style coloring

### 📊 General Statistics
- Overall Team Standings table with rankings
- Top N Finishes Analysis (treemap visualization)
- Average Performance by Round (pivot table)

### 🏆 Team Analysis
- Performance Dynamics chart with median line
- Game Round Comparison (vs Winner and Max scores)
- Game History table
- **Team vs Team Comparison** with:
  - Metrics comparison table
  - Radar chart for performance profiles
  - Head-to-Head results for common games

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/selfadjoint/quiz-please-dashboard.git
   cd quiz-please-dashboard
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure database connection:
   Create `.streamlit/secrets.toml`:
   ```toml
   [connections.postgresql]
   host = "your_host"
   port = 5432
   database = "your_database"
   username = "your_username"
   password = "your_password"
   ```

5. Run the app:
   ```bash
   streamlit run "0_🏠_Main.py"
   ```

## Deployment to Streamlit Cloud

1. Push code to GitHub (secrets are excluded via `.gitignore`)
2. Connect your repo to [Streamlit Cloud](https://streamlit.io/cloud)
3. Add your database credentials in the app's **Secrets** section
4. Deploy!

## Project Structure

```
quiz-please-dashboard/
├── 0_🏠_Main.py           # Main page
├── pages/
│   ├── 1_📊_General_Stats.py
│   └── 2_🏆_Team_Analysis.py
├── src/
│   ├── db.py              # Database queries
│   └── utils.py           # Utility functions
├── assets/
│   └── logo.svg           # Quiz Please logo
├── requirements.txt
└── .gitignore
```

## Tech Stack

- **Frontend**: Streamlit
- **Visualizations**: Plotly
- **Data Processing**: Pandas
- **Database**: PostgreSQL via SQLAlchemy

## License

MIT
