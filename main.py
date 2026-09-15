import asyncio
import re
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from apify import Actor

async def main():
    async with Actor:
        # Leggi input
        input_data = await Actor.get_input()
        websites = input_data.get('websites', [])
        
        results = []
        
        for url in websites:
            try:
                # Scarica la pagina
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        url,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        },
                        timeout=30.0
                    )
                
                if response.status_code != 200:
                    Actor.log.warning(f'Skip {url} - Status: {response.status_code}')
                    continue
                
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # Estrai email con regex
                emails = []
                email_pattern = r'[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                matches = re.findall(email_pattern, html)
                
                if matches:
                    # Filtra email poco utili
                    filtered = [
                        e for e in matches 
                        if not any(x in e for x in ['.png', '.jpg', 'cdn', '.css'])
                    ]
                    emails = list(set(filtered))  # Rimuovi duplicate
                
                # Estrai telefono (pattern italiani + internazionali)
                phones = []
                phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?(?:\\(?\\d{2,4}\\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}'
                phone_matches = re.findall(phone_pattern, html)
                if phone_matches:
                    phones = list(set(phone_matches[:5]))  # Max 5 numeri, rimuovi duplicate
                
                # Estrai link social
                socials = {
                    'linkedin': [],
                    'instagram': [],
                    'facebook': []
                }
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if 'linkedin.com' in href:
                        socials['linkedin'].append(href)
                    elif 'instagram.com' in href:
                        socials['instagram'].append(href)
                    elif 'facebook.com' in href:
                        socials['facebook'].append(href)
                
                # Estrai indirizzo (tag <address>)
                address = ''
                address_tag = soup.find('address')
                if address_tag:
                    address = address_tag.get_text(strip=True).replace('\n', ' ').replace('\r', ' ')[:200]
                
                # Charging (Pay-per-Event) - solo se trova email
                if emails:
                    await Actor.charge(
                        event_name='website_scraped',
                        count=1,
                        total_amount_usd=0.12  # 12 centesimi per sito
                    )
                
                results.append({
                    'url': url,
                    'emails': emails,
                    'phones': phones,
                    'socials': socials,
                    'address': address,
                    'scrapedAt': Actor.get_current_datetime().isoformat()
                })
                
                Actor.log.info(f'✅ {url} - Emails: {len(emails)}')
                
                # Delay per evitare blocchi (1-3 secondi)
                await asyncio.sleep(1 + (hash(url) % 3))
                
            except Exception as e:
                Actor.log.error(f'❌ Error scraping {url}: {str(e)}')
                continue
        
        # Salva output
        await Actor.push_data(results)
