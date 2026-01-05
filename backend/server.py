import httpx, asyncio, os, dotenv, aiosmtplib, mimetypes
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from email.message import EmailMessage
from pydantic import BaseModel
from bs4 import BeautifulSoup
from lxml import html
import pandas as pd
dotenv.load_dotenv()

# CONSTANTS
DEPTS = {0: 'Architecture', 1: 'Physics', 2: 'Artificial Intelligence', 3: 'Computational Finance', 4: 'Computer Science', 5: 'Computer Science (TIEST)', 6: 'Cyber Security', 7: 'Data Science', 8: 'Development Studies', 9: 'Economics & Finance', 10: 'English Linguistics', 11: 'Gaming and Animation', 12: 'Chemistry', 13: 'Management Sciences', 14: 'Textile Sciences', 15: 'Automotive Engg.', 16: 'Bio-Medical Engg.', 17: 'Chemical Engg.', 18: 'Civil Engg.', 19: 'Civil Engg. (TIEST)', 20: 'Computer Systems Engg.', 21: 'Construction Engg.', 22: 'Electrical Engg.', 23: 'Electronics Engg.', 24: 'Food Engg.', 25: 'Industrial & Manufacturing Engg.', 26: 'Materials Engg.', 27: 'Mechanical Engg.', 28: 'Metallurgical Engg.', 29: 'Petroleum Engg.', 30: 'Polymer & Petrochemical Engg.', 31: 'Software Engg.', 32: 'Telecommunications Engg.', 33: 'Textile Engg.', 34: 'Urban Engg.'}
YEARS = {1: '1st', 2: '2nd', 3: '3rd', 4: '4th', 5: '5th'}

# DB INITIALIZATION
mongo_client = AsyncIOMotorClient(os.getenv('MONGODB_URL'))
db = mongo_client['users']
col = db['users']

# FASTAPI CODE
class User(BaseModel):
    email : str
    department: int
    year: int

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://neduet-result-notifier.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/insert_user")
async def store_details(data : User):
    if await col.find_one({"email": data.email}): 
        raise HTTPException(409, "The following email already exists in the database.")
    else: 
        await col.insert_one({"email": data.email, "department": int(data.department), "year": int(data.year), "notify": True})
        smtp = aiosmtplib.SMTP(
            hostname='smtp.gmail.com',
            port=465,
            use_tls=True
        )
        await smtp.connect()
        await smtp.login('ned.resultnotifier@gmail.com', os.getenv('PASSWORD'))
        await send_email(data.email, data.department, data.year, smtp, first_time=True)
        await smtp.quit()
        return Response(status_code=200)
    
@app.get("/get_details")
async def get_details():
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get('https://www.neduet.edu.pk/examination_results')
        webpage = resp.content
    df = await asyncio.to_thread(lambda: pd.read_html(webpage)[1].to_numpy(dtype=str))
    
    doc = html.fromstring(webpage)
    text = doc.xpath('//a[@id="Bachelors"]/parent::th')[0].text_content()
    EXAM = text.split('(')[1].split(')')[0].strip()

    return {'all_results_released' : '-' not in df, 'exam_name': EXAM}

@app.post("/check_results")
async def check_results():
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get('https://www.neduet.edu.pk/examination_results')
        webpage = resp.content

    df = await asyncio.to_thread(lambda: pd.read_html(webpage)[1].to_numpy(dtype=str))

    if '-' not in df:
        return Response(status_code=200)
    
    soup = await asyncio.to_thread(BeautifulSoup, webpage, "html.parser")
    table = soup.find_all("table")[1]
    images = []
    for tr in table.find_all("tr")[3:]:
        cells = tr.find_all("td")
        row = []
        for cell in cells:
            links = [a["href"] for a in cell.find_all("a")]
            row.append(links)
        images.append(row)
    
    smtp = aiosmtplib.SMTP(
        hostname='smtp.gmail.com',
        port=465,
        use_tls=True
    )
    await smtp.connect()
    await smtp.login('ned.resultnotifier@gmail.com', os.getenv('PASSWORD'))
    
    tasks = []
    async for user in col.find({'notify': True}):
        status = df[user['department'], user['year']]
        if '-' not in status:
            tasks.append(send_email(user['email'], user['department'], user['year'], smtp, attachments=images[user['department']][user['year']]))
            tasks.append(col.delete_one({'_id': user['_id']}))

    await asyncio.gather(*tasks)
    await smtp.quit()
    return Response(status_code=200)

async def send_email(to_email, department, year, server, attachments = None, first_time = False):
    department = DEPTS[department]
    year = YEARS[year]

    msg = EmailMessage()
    msg["Subject"] = "NEDUET Results Confirmation" if first_time else f"{year} Year Results are Released!"
    msg["From"] = "ned.resultnotifier@gmail.com"
    msg["To"] = to_email

    if not first_time:
        msg.set_content(f"""
Hello,

The results for the Department of {department}, {year} Year have been officially released on the NEDUET website.
You can view your results from here (https://www.neduet.edu.pk/examination_results) or from the attachments provided.

If this tool was helpful for you, please feel free to star the repository over here (https://github.com/muhammadrafayasif/ned-result-notifier).
Contributions of any kind are welcome and encouraged!

Congratulations and best of luck for your next steps!

Regards,  
NEDUET Results Bot
""")
    else:
        msg.set_content(f"""
Hello, 

You will be notified as soon as the results for the Department of {department}, {year} Year are released officially on the NEDUET website. 

Regards, 
NEDUET Results Bot
""")

    if attachments:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for n, url in enumerate(attachments):
                try:
                    response = await client.get('https://www.neduet.edu.pk' + url)
                    response.raise_for_status()
                    image_bytes = response.content
                except httpx.HTTPError:
                    print(f"Failed to fetch {url}, skipping...")
                    continue

                # Determine MIME type
                mime_type, _ = mimetypes.guess_type(url)
                if mime_type is None:
                    mime_type = "application/octet-stream"
                maintype, subtype = mime_type.split("/")

                # Attach image
                msg.add_attachment(image_bytes, maintype=maintype, subtype=subtype, filename=str(n))

    await server.send_message(msg)