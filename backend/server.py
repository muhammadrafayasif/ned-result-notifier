import httpx, asyncio, os, dotenv, resend
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from lxml import html
dotenv.load_dotenv()
resend.api_key = os.getenv('RESEND_API_KEY')

# CONSTANTS
DEPTS = {0: 'Architecture', 1: 'Physics', 2: 'Artificial Intelligence', 3: 'Computational Finance', 4: 'Computer Science', 5: 'Computer Science (TIEST)', 6: 'Cyber Security', 7: 'Data Science', 8: 'Development Studies', 9: 'Economics & Finance', 10: 'English Linguistics', 11: 'Gaming and Animation', 12: 'Chemistry', 13: 'Management Sciences', 14: 'Textile Sciences', 15: 'Automotive Engg.', 16: 'Bio-Medical Engg.', 17: 'Chemical Engg.', 18: 'Civil Engg.', 19: 'Civil Engg. (TIEST)', 20: 'Computer Systems Engg.', 21: 'Construction Engg.', 22: 'Electrical Engg.', 23: 'Electronics Engg.', 24: 'Food Engg.', 25: 'Industrial & Manufacturing Engg.', 26: 'Materials Engg.', 27: 'Mechanical Engg.', 28: 'Metallurgical Engg.', 29: 'Petroleum Engg.', 30: 'Polymer & Petrochemical Engg.', 31: 'Software Engg.', 32: 'Telecommunications Engg.', 33: 'Textile Engg.', 34: 'Urban Engg.'}
YEARS = {1: '1st', 2: '2nd', 3: '3rd', 4: '4th', 5: '5th'}

# DB INITIALIZATION
mongo_client = None
db = None
col = None

async def get_mongo_collection():
    global mongo_client, db, col
    if mongo_client is None:
        mongo_client = AsyncIOMotorClient(os.getenv('MONGODB_URL'))
        db = mongo_client['users']
        col = db['users']
    return col

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
    col = await get_mongo_collection()
    if await col.find_one({"email": data.email}): 
        raise HTTPException(409, "The following email already exists in the database.")
    else: 
        await col.insert_one({"email": data.email, "department": int(data.department), "year": int(data.year), "notify": True})
        await send_email(data.email, data.department, data.year, first_time=True)
        return Response(status_code=200)
    
@app.get("/get_details")
async def get_details():
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get('https://www.neduet.edu.pk/examination_results')
        webpage = resp.content
    
    doc = html.fromstring(webpage)
    text = doc.xpath('//a[@id="Bachelors"]/parent::th')[0].text_content()
    table = doc.xpath('//table')[1]
    results_released = table.xpath(".//td[text() = '-'] | .//th[text() = '-']")
    EXAM = text.split('(')[1].split(')')[0].strip()

    return {'all_results_released' : len(results_released) <= 1, 'exam_name': EXAM}

@app.post("/check_results")
async def check_results():
    col = await get_mongo_collection()
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get('https://www.neduet.edu.pk/examination_results')
        webpage = resp.content
    
    doc = html.fromstring(webpage)
    table = doc.xpath('//table')[1]
    images = []
    for tr in table.xpath('.//tr')[3:]:
        row = []
        for td in tr.xpath('./td'):
            links = [a.get('href') for a in td.xpath('.//a[@href]')]
            row.append(links)
        images.append(row)
    
    tasks = []
    users_to_update = []
    async for user in col.find({'notify': True}):
        results = images[user['department']][user['year']]
        if results:
            tasks.append(send_email(user['email'], user['department'], user['year'], attachment_urls = results))
            users_to_update.append(user['_id'])

    for i in range(0, len(tasks), 10):
        await asyncio.gather(*tasks[i:i+10])

    if users_to_update:
        await col.update_many({'_id': {'$in': users_to_update}}, {'$set': {'notify': False}})
    return Response(status_code=200)

async def send_email(to_email, department, year, attachment_urls = None, first_time = False):
    department = DEPTS[department]
    year = YEARS[year]

    subject = "NEDUET Results Confirmation" if first_time else f"{year} Year Results are Released!"
    email_from = "NEDUET Result Notifier <onboarding@resend.dev>"
    email_to = to_email

    if not first_time:
        body = f"""
Hello, <br><br>

The results for the <b>Department of {department}, {year} Year</b> have been officially released on the NEDUET website.
You can view your results from here (https://www.neduet.edu.pk/examination_results) or from the attachments provided.
<br>
If this tool was helpful for you, please feel free to star the repository over here (https://github.com/muhammadrafayasif/ned-result-notifier).<br>
Contributions of any kind are welcome and encouraged!
<br>
Congratulations and best of luck for your next steps!
<br><br>
Regards, <br>
NEDUET Results Bot
"""
    else:
        body = f"""
Hello, <br><br>

You will be notified as soon as the results for the <b>Department of {department}, {year}</b> Year are released officially on the NEDUET website. 
<br><br>
Regards, <br>
NEDUET Results Bot
"""
    attachments = None
    if attachment_urls:
        attachments = [
            {
                'path' : 'https://www.neduet.edu.pk' + url,
                'filename': str(n+1) + '.' + url.split('.')[-1]
            }
            for n, url in enumerate(attachment_urls)
        ]

    params: resend.Emails.SendParams = {
        "from": email_from,
        "to": [email_to],
        "subject": subject,
        "html": body,
        "attachments": attachments if attachments else None
    }
    await asyncio.to_thread(resend.Emails.send, params)