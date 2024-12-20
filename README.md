# specta-ai-prototype


# **Specta AI**

Specta AI is a prototype web application that leverages an LLM and live sports data to deliver customized, real-time text-based sports broadcasts. The application enables users to select games, customize play-by-play commentary based on their preferences, and view engaging game summaries.

---

## **Features**

- **Game Selection**: Choose a game by selecting a date and game from a dynamically updated schedule.
- **Game Summaries**: Get engaging and informative summaries tailored to the game's current status (not started, in progress, or over).
- **Play-by-Play Broadcast Customization**:
  - Select players of interest.
  - Customize the tone and storyline of the broadcast.
- **Dynamic Prompt Handling**: Prompts for the LLM are dynamically tailored based on the context (game status and user inputs).
- **Authentication**: Simple login/logout system for user management.

---

## **Folder Structure**

```
project_directory/
├── app.py                   # Main Streamlit application
├── utils/
│   ├── auth.py              # Authentication functions
│   ├── prompt_helpers.py    # Helper functions for preparing prompts
│   ├── sports_data.py       # Functions for interacting with the sports data API
├── llm_interface.py         # Functions for interacting with the LLM
├── prompts/
│   ├── game_summary_prompt.txt  # Template for game summary prompts
│   ├── broadcast_prompt.txt     # Template for broadcast prompts
├── .streamlit/
│   └── secrets.toml         # Configuration for API keys and credentials
└── README.md                # Project documentation
```

---

## **Setup Instructions**

### **Prerequisites**

- Python 3.12
- Streamlit
- Access to the following APIs:
  - [SportsData.io Replay API](https://sportsdata.io/developers/replay)
  - OpenAI API (requires an API key)

### **Installation**

1. Clone the repository:
   ```bash
   git clone https://github.com/toratommy/specta-ai-prototype.git
   cd specta-ai-prototype
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the `secrets.toml` file:
   Create a `secrets.toml` file in the `.streamlit/` directory with the following structure:
   ```toml
   [credentials]
   username = "your_username"
   password = "your_password"

   [api_keys]
   sportsdataio = "YOUR_REPLAY_API_KEY"
   openai = "YOUR_OPENAI_API_KEY"
   ```

4. Set up prompt templates:
   Ensure the `prompts/` directory contains the following files:
   - `game_summary_prompt.txt`
   - `broadcast_prompt.txt`

   Example content for `game_summary_prompt.txt`:
   ```plaintext
   The following summarizes the current state of the game:
   {box_score_json}

   Instructions:
   {dynamic_instructions}

   Generate an engaging game summary based on the information above, emphasizing relevant and interesting details.
   ```

   Example content for `broadcast_prompt.txt`:
   ```plaintext
   Game Information:
   {game_info}

   User Preferences:
   {preferences}

   Generate a customized play-by-play broadcast tailored to the user's preferences, focusing on tone, storyline, and player interest.
   ```

---

## **Running the Application Locally**

1. Start the Streamlit app:
   ```bash
   streamlit run app.py
   ```

2. Open the app in your browser:
   ```
   http://localhost:8501
   ```

---

## **Customization**

### Prompts
To customize LLM behavior:
- Modify the `.txt` files in the `prompts/` directory.

### API Keys
Replace the placeholders in the `secrets.toml` file with your own API keys.

---

## **License**

This project is licensed under the [CC BY-NC-ND 4.0](LICENSE).

---

## **Acknowledgments**

- [SportsData.io](https://sportsdata.io) for the Replay API.
- [OpenAI](https://platform.openai.com/) for GPT-based LLM integration.
- Streamlit for providing an easy-to-use web app framework.
