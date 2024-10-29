# baseball_email_report.py
import pandas as pd
import matplotlib.pyplot as plt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib
import io
from datetime import datetime, date
from typing import List, Dict, Optional
from baseball_plotting import plot_baseball_stats_final

class MLBSeasonSchedule:
    def __init__(self, season_year: int):
        """
        Initialize MLB season schedule handler.
        
        Args:
            season_year (int): MLB season year
        """
        self.season_year = season_year
        # Default MLB season dates (can be updated if needed)
        self.season_start = date(season_year, 3, 20)
        self.season_end = date(season_year, 9, 30)
        
    def is_game_day(self, check_date: date) -> bool:
        """
        Check if given date is within MLB season.
        
        Args:
            check_date (date): Date to check
            
        Returns:
            bool: True if date is within season
        """
        return self.season_start <= check_date <= self.season_end
    
    def get_next_game_day(self) -> Optional[date]:
        """
        Get the next game day from current date.
        
        Returns:
            Optional[date]: Next game day or None if season is over
        """
        today = date.today()
        if today > self.season_end:
            return None
        elif today < self.season_start:
            return self.season_start
        else:
            return today if self.is_game_day(today) else None

class BaseballReportEmailer:
    def __init__(self, smtp_server: str, smtp_port: int, sender_email: str, sender_password: str, from_address: str = None):
        """
        Initialize the emailer with SMTP settings.
        
        Args:
            smtp_server (str): SMTP server address
            smtp_port (int): SMTP port
            sender_email (str): Sender's email address (API token for Postmark)
            sender_password (str): Sender's password (API token for Postmark)
            from_address (str): Verified sender address for Postmark
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.from_address = from_address

    def create_player_plot(self, player_data: pd.DataFrame) -> io.BytesIO:
        """
        Create a plot for a player and return it as bytes.
        
        Args:
            player_data (pd.DataFrame): DataFrame containing player's statistics
            
        Returns:
            io.BytesIO: Plot image as bytes
        """
        fig = plot_baseball_stats_final(player_data)
        img_bytes = io.BytesIO()
        fig.savefig(img_bytes, format='png', bbox_inches='tight')
        plt.close(fig)
        img_bytes.seek(0)
        return img_bytes

    def format_email_html(self, date: str, players_data: List[Dict]) -> str:
        """
        Format the email HTML content.
        
        Args:
            date (str): Report date
            players_data (List[Dict]): List of player statistics
            
        Returns:
            str: Formatted HTML content
        """
        html = f"""
        <html>
        <body>
        <h1>MLB underestimated players – {date}</h1>
        """
        
        for i, player in enumerate(players_data, 1):
            html += f"""
            <div style="margin-bottom: 30px;">
                <h2>{i}. Player name: {player['name']}</h2>
                <p>100PA rolling wOBA: {player['rolling_woba']:.3f}</p>
                <p>diff_rolling_OBA: {player['diff_oba']:.3f}</p>
                <img src="cid:player_plot_{i}" style="max-width: 800px;"><br>
            </div>
            """
        
        html += "</body></html>"
        return html

    def send_report(self, recipients: List[str], players_data: List[Dict], 
                   date: str) -> None:
        """
        Send the email report using Postmark.
        """
        msg = MIMEMultipart('related')
        msg['Subject'] = f'MLB Underestimated Players Report - {date}'
        msg['From'] = self.from_address
        msg['To'] = ', '.join(recipients)
        msg['X-Postmark-Server-Token'] = self.sender_email

        # Create HTML content
        html_content = self.format_email_html(date, players_data)
        msg.attach(MIMEText(html_content, 'html'))

        # Attach plots
        for i, player in enumerate(players_data, 1):
            img = MIMEImage(player['plot_bytes'].getvalue())
            img.add_header('Content-ID', f'<player_plot_{i}>')
            msg.attach(img)

        # Send email with retry logic and debug information
        max_retries = 3
        retry_delay = 30  # 30 seconds between retries
        
        for attempt in range(max_retries):
            try:
                print(f"\nAttempt {attempt + 1} to send email:")
                print(f"Connecting to {self.smtp_server}:{self.smtp_port}")
                
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    print("Connected successfully")
                    server.set_debuglevel(1)  # Enable debug output
                    
                    print("Starting TLS")
                    server.starttls()
                    print("TLS started")
                    
                    print("Attempting login with Postmark API token")
                    server.login(self.sender_email, self.sender_password)
                    print("Login successful")
                    
                    print("Sending message")
                    server.send_message(msg)
                    print("Message sent successfully!")
                    break
                    
            except Exception as e:
                print(f"\nError details: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                print(f"Retrying in {retry_delay} seconds...")
                import time
                time.sleep(retry_delay)