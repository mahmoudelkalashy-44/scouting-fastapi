# app/services/scout_ai.py
import logging
import time
import re
from typing import Optional, List
from groq import Groq

from app.config import settings

logger = logging.getLogger(__name__)

class ScoutAI:
    """كلاس لتوليد التقارير الكشفية باستخدام الذكاء الاصطناعي"""
    
    GAME_STYLES = {
        "Tiki-Taka": "This style of play, focuses on ball possession, control, and accurate passing.",
        "Counter-Attack": "Teams adopting a counter-attacking style focus on solid defense and rapid advancement in attack when they regain possession of the ball.",
        "High Press": "This style involves intense pressure on the opposing team from their half of the field.",
        "Direct Play": "This style of play is more direct and relies on long and vertical passes.",
        "Pragmatic Possession": "Some teams aim to maintain ball possession as part of a defensive strategy.",
        "Reactive": "In this style, a team adapts to the ongoing game situations.",
        "Physical and Defensive": "Some teams place greater emphasis on solid defense and physical play.",
        "Positional Play": "This style aims to dominate the midfield and create passing triangles.",
        "Catenaccio": "This style, originating in Italy, focuses on defensive solidity and counterattacks.",
        "Counter Attacking": "This style relies on solid defensive organization and quick transition to attack.",
        "Long Ball": "This style involves frequent use of long and direct passes."
    }
    
    PLAYER_EXPERIENCE = {
        "Veteran": "A player with a long career and extensive experience in professional football.",
        "Experienced": "A player with experience, but not necessarily in the late stages of their career.",
        "Young": "A player in the early or mid-career, often under 25 years old.",
        "Promising": "A young talent with high potential but still needs to fully demonstrate their skills."
    }
    
    LEAGUES = {
        "Serie A": "Tactical and defensive football with an emphasis on defensive solidity.",
        "Ligue 1": "Open games with a high number of goals and a focus on discovering young talents.",
        "Premier League": "Fast-paced, physical, and high-intensity play.",
        "Bundesliga": "High-pressing approach and the development of young talents.",
        "La Liga": "Possession of the ball and technical play."
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.client = None
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
    
    def _build_prompt(self, similar_players_df_str: str, game_style: str, 
                      player_experience: str, league: str, formation: str, 
                      skills: List[str]) -> str:
        """بناء الـ Prompt للذكاء الاصطناعي"""
        return f"""
Generate a Football Talent Scout report based on the DATA PROVIDED (maximum 250 words) written in a formal tone FOLLOWING THE EXAMPLE.
It is essential to compare player attributes and select the most suitable candidate from the available options from among similar players, based on the TEAM REQUIREMENTS provided.
THE PLAYER CHOSEN MUST NECESSARILY BE AMONG THE POSSIBLE PLAYERS CONSIDERED IN THE FOOTBALL SCOUT REPORT.
INDICATE the player chosen at the end of the REPORT.

DATA:
------------------------------------
{similar_players_df_str}
------------------------------------

TEAM REQUIREMENTS:
Style of play: {self.GAME_STYLES.get(game_style, game_style)}
Player type required: {self.PLAYER_EXPERIENCE.get(player_experience, player_experience)}
Preferred league: {self.LEAGUES.get(league, league)}
Key ability: {skills}
Ideal formation: {formation}

EXAMPLE TO FOLLOW:
### Report
After a detailed analysis of the data, we have identified candidates who best meet the requirements of your team.

##### Three potential candidates:
**[Player X]**: Highlights strengths and addresses weaknesses.
**[Player Y]**: Highlights strengths and addresses weaknesses.
**[Player Z]**: Highlights strengths and addresses weaknesses.

[Provide the reasons for choosing the recommended player over the others].

The recommended player: Name of player recommended.
"""
    
    def _extract_recommended_player(self, text: str) -> Optional[str]:
        """استخراج اسم اللاعب الموصى به من النص"""
        pattern = r"The recommended player:\s*([^:\n]+)"
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            name = matches[0].strip().rstrip('.')
            # إزالة علامات التنسيق
            if name.startswith('**') and name.endswith('**'):
                name = name.strip('*')
            return name
        return None
    
    def generate_report(self, similar_players_df_str: str, game_style: str,
                       player_experience: str, league: str, formation: str,
                       skills: List[str]) -> dict:
        """توليد تقرير كشفي"""
        if not self.client:
            return {
                "error": "Groq API key not provided",
                "report_text": "⚠️ Please provide a valid Groq API key to generate AI reports."
            }
        
        start_time = time.time()
        
        try:
            prompt = self._build_prompt(
                similar_players_df_str, game_style, player_experience, 
                league, formation, skills
            )
            
            response = self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are a soccer scout and you must be good at finding the best talents in your team starting from the players rated by the similar player system."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1024,
            )
            
            report_text = response.choices[0].message.content
            recommended_player = self._extract_recommended_player(report_text)
            
            return {
                "report_text": report_text,
                "recommended_player": recommended_player,
                "generation_time_ms": round((time.time() - start_time) * 1000, 2),
                "model_used": settings.GROQ_MODEL
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating scout report: {str(e)}")
            return {
                "error": str(e),
                "report_text": f"⚠️ Error generating report: {str(e)}"
            }