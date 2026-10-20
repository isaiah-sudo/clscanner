import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Tuple
from app.database import get_all_settings, mark_deal_notified

logger = logging.getLogger("clscanner.notifier")

def generate_deal_email_html(deal: Dict[str, Any]) -> str:
    """Generates a high-conversion, responsive HTML email for a detected deal."""
    title = deal.get("title", "Craigslist Item")
    price = deal.get("price", 0.0)
    est_resale = deal.get("est_resale_value", 0.0)
    est_profit = deal.get("est_profit", 0.0)
    margin = deal.get("profit_margin", 0.0)
    matched_rule = deal.get("matched_rule", "TECH DEAL")
    location = deal.get("location", "Local Area")
    city = deal.get("city", "Craigslist")
    url = deal.get("url", "#")
    image_url = deal.get("image_url", "")
    score = deal.get("deal_score", 1)
    
    score_badge = "🔥 INSANE DEAL" if score == 3 else ("🔥 GREAT DEAL" if score == 2 else "👍 GOOD PROFIT")
    badge_bg = "#dc2626" if score == 3 else ("#ea580c" if score == 2 else "#16a34a")
    
    # Query for eBay Sold listings
    clean_query = "+".join(matched_rule.split())
    ebay_sold_url = f"https://www.ebay.com/sch/i.html?_nkw={clean_query}&LH_Sold=1&LH_Complete=1"

    img_html = ""
    if image_url:
        img_html = f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="{image_url}" alt="{title}" style="max-width: 100%; max-height: 320px; border-radius: 8px; object-fit: cover; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);" />
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>New Deal Detected</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; margin: 0; padding: 24px 12px; color: #f8fafc;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 12px; overflow: hidden; border: 1px solid #334155;">
            
            <!-- Header Banner -->
            <div style="background: linear-gradient(135deg, #2563eb, #1d4ed8); padding: 20px; text-align: center;">
                <span style="display: inline-block; background-color: {badge_bg}; color: white; font-weight: 800; font-size: 13px; text-transform: uppercase; padding: 4px 12px; border-radius: 9999px; margin-bottom: 8px;">
                    {score_badge}
                </span>
                <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 700;">New Computer Deal Detected!</h1>
                <p style="color: #bfdbfe; margin: 4px 0 0 0; font-size: 14px;">Matched Target: <strong>{matched_rule}</strong> in {city.capitalize()}</p>
            </div>
            
            <!-- Content -->
            <div style="padding: 24px;">
                {img_html}
                
                <h2 style="margin: 0 0 16px 0; font-size: 18px; line-height: 1.4; color: #ffffff;">
                    {title}
                </h2>
                
                <!-- Financials Grid -->
                <div style="background-color: #0f172a; border-radius: 8px; padding: 16px; margin-bottom: 24px; border: 1px solid #334155;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 6px 0; color: #94a3b8; font-size: 14px;">Buy Price:</td>
                            <td style="padding: 6px 0; text-align: right; color: #ef4444; font-weight: 700; font-size: 18px;">${price:.2f}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; color: #94a3b8; font-size: 14px;">Est. Resale:</td>
                            <td style="padding: 6px 0; text-align: right; color: #38bdf8; font-weight: 700; font-size: 18px;">${est_resale:.2f}</td>
                        </tr>
                        <tr style="border-top: 1px solid #334155;">
                            <td style="padding: 10px 0 4px 0; color: #e2e8f0; font-size: 15px; font-weight: 600;">Est. Flip Profit:</td>
                            <td style="padding: 10px 0 4px 0; text-align: right; color: #22c55e; font-weight: 800; font-size: 20px;">+${est_profit:.2f} ({margin:.0f}%)</td>
                        </tr>
                        <tr>
                            <td style="padding: 4px 0; color: #94a3b8; font-size: 13px;">Location:</td>
                            <td style="padding: 4px 0; text-align: right; color: #cbd5e1; font-size: 13px;">{location or city.capitalize()}</td>
                        </tr>
                    </table>
                </div>
                
                <!-- Action Buttons -->
                <div style="text-align: center; margin-bottom: 16px;">
                    <a href="{url}" style="display: block; width: 100%; box-sizing: border-box; background-color: #2563eb; color: white; text-decoration: none; padding: 14px 20px; border-radius: 8px; font-weight: 700; font-size: 16px; margin-bottom: 10px; text-align: center;">
                        🚀 Open Listing on Craigslist
                    </a>
                    <a href="{ebay_sold_url}" style="display: block; width: 100%; box-sizing: border-box; background-color: #334155; color: #93c5fd; text-decoration: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; font-size: 14px; text-align: center;">
                        🔍 Verify Recent eBay Sold Comps
                    </a>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="background-color: #0f172a; padding: 16px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #334155;">
                CLScanner Automated Flip Finder • Running on Oracle Cloud Always Free
            </div>
        </div>
    </body>
    </html>
    """

def send_email(to_email: str, subject: str, html_content: str, config: Dict[str, Any]) -> Tuple[bool, str]:
    """Sends an HTML email using SMTP configuration."""
    host = config.get("smtp_host", "").strip()
    port = int(config.get("smtp_port", 587))
    user = config.get("smtp_user", "").strip()
    password = config.get("smtp_pass", "").strip()
    use_tls = str(config.get("smtp_use_tls", "true")).lower() == "true"
    
    if not host or not user or not password or not to_email:
        return False, "SMTP configuration or recipient email is missing."
        
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"CLScanner Alerts <{user}>"
    msg["To"] = to_email
    
    msg.attach(MIMEText(html_content, "html"))
    
    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=15) as server:
                server.login(user, password)
                server.sendmail(user, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(host, port, timeout=15) as server:
                if use_tls:
                    server.starttls()
                server.login(user, password)
                server.sendmail(user, [to_email], msg.as_string())
                
        logger.info(f"Email successfully sent to {to_email}: {subject}")
        return True, "Email sent successfully!"
    except Exception as e:
        err_msg = f"Failed to send email: {str(e)}"
        logger.error(err_msg)
        return False, err_msg

def notify_deal_if_enabled(deal: Dict[str, Any]) -> bool:
    """Checks if email notifications are enabled and sends notification for a new deal."""
    settings = get_all_settings()
    enabled = settings.get("smtp_enabled", "false").lower() == "true"
    to_email = settings.get("notify_email", "").strip()
    
    if not enabled or not to_email:
        return False
        
    title = deal.get("title", "Computer Deal")
    price = deal.get("price", 0.0)
    profit = deal.get("est_profit", 0.0)
    rule = deal.get("matched_rule", "TECH")
    
    score = deal.get("deal_score", 1)
    fire = "🔥🔥🔥" if score == 3 else ("🔥🔥" if score == 2 else "🔥")
    subject = f"{fire} [Flip Alert] ${profit:.0f} Profit: {rule} for ${price:.0f} - {title[:35]}"
    
    html = generate_deal_email_html(deal)
    success, err = send_email(to_email, subject, html, settings)
    if success:
        mark_deal_notified(deal["id"])
    return success

def test_smtp_connection(to_email: str, settings: Dict[str, Any]) -> Tuple[bool, str]:
    """Sends a verification test email to ensure SMTP settings are working."""
    subject = "✅ CLScanner Notification Test - Connection Successful!"
    html = """
    <div style="font-family: sans-serif; background-color: #0f172a; padding: 24px; color: #f8fafc; border-radius: 8px;">
        <h2 style="color: #22c55e;">🎉 Your CLScanner email alerts are working!</h2>
        <p>This is a test notification confirming your SMTP credentials are configured correctly.</p>
        <p>When high-profit computer parts or systems under $250 are found on Craigslist, you will receive instant alerts here.</p>
    </div>
    """
    return send_email(to_email, subject, html, settings)
