from email.message import EmailMessage
import httpx, asyncio, os, dotenv, aiosmtplib, uuid
import json
from fastapi import FastAPI, HTTPException, Response, Header
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from lxml import html
from redis import asyncio as redis
dotenv.load_dotenv()

# CONSTANTS
DEPTS = {0: 'Architecture', 1: 'Physics', 2: 'Artificial Intelligence', 3: 'Computational Finance', 4: 'Computer Science', 5: 'Computer Science (TIEST)', 6: 'Cyber Security', 7: 'Data Science', 8: 'Development Studies', 9: 'Economics & Finance', 10: 'English Linguistics', 11: 'Gaming and Animation', 12: 'Chemistry', 13: 'Management Sciences', 14: 'Textile Sciences', 15: 'Automotive Engg.', 16: 'Bio-Medical Engg.', 17: 'Chemical Engg.', 18: 'Civil Engg.', 19: 'Civil Engg. (TIEST)', 20: 'Computer Systems Engg.', 21: 'Construction Engg.', 22: 'Electrical Engg.', 23: 'Electronics Engg.', 24: 'Food Engg.', 25: 'Industrial & Manufacturing Engg.', 26: 'Materials Engg.', 27: 'Mechanical Engg.', 28: 'Metallurgical Engg.', 29: 'Petroleum Engg.', 30: 'Polymer & Petrochemical Engg.', 31: 'Software Engg.', 32: 'Telecommunications Engg.', 33: 'Textile Engg.', 34: 'Urban Engg.'}
YEARS = {1: '1st', 2: '2nd', 3: '3rd', 4: '4th', 5: '5th'}

# DB INITIALIZATION
mongo_client = None
db = None
col = None
redis_client = None
GET_DETAILS_CACHE_KEY = "get_details:latest"
GET_DETAILS_CACHE_TTL = 60 * 60 * 24 * 2

async def get_mongo_collection():
    global mongo_client, db, col
    if mongo_client is None:
        mongo_client = AsyncIOMotorClient(os.getenv('MONGODB_URL'))
        db = mongo_client['users']
        col = db['users']
    return col

async def get_redis_client():
    global redis_client
    if redis_client is not None:
        return redis_client

    redis_url = os.getenv("REDIS_URL")
    redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    return redis_client

# FASTAPI CODE
class User(BaseModel):
    email : str
    department: int
    year: int
    examName: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://neduet-result-notifier.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/insert_user")
async def store_details(data : User, x_app_key: str | None = Header(default=None, alias="X-App-Key")):
    print(os.getenv("APP_KEY"))
    
    if x_app_key != os.getenv("SERVER_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden :(")

    col = await get_mongo_collection()
    if await col.find_one({"email": data.email}): 
        raise HTTPException(409, "The following email already exists in the database.")
    else: 
        uniqueID = str(uuid.uuid4())
        await col.insert_one({"email": data.email, "department": int(data.department), "year": int(data.year), "examName": data.examName, "uniqueID": uniqueID, "notify": True})
        await send_email(data.email, data.department, data.year, uniqueID, data.examName, first_time=True)
        return Response(status_code=200)
    
@app.get("/remove_user")
async def remove_user(id : str, x_app_key: str | None = Header(default=None, alias="X-App-Key")):
    if x_app_key != os.getenv("SERVER_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden :(")

    col = await get_mongo_collection()
    user = await col.delete_one({"uniqueID": id})
    if user.deleted_count == 1:
        return Response(status_code=200, content="User successfully deleted.")
    else:
        raise HTTPException(status_code=500, detail="Failed to delete user.")
    
    
@app.get("/get_details")
async def get_details(x_app_key: str | None = Header(default=None, alias="X-App-Key")):
    if x_app_key != os.getenv("SERVER_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden :(")

    cache = await get_redis_client()
    if cache is not None:
        try:
            cached_value = await cache.get(GET_DETAILS_CACHE_KEY)
            if cached_value:
                return json.loads(cached_value)
        except Exception:
            cache = None

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get('https://www.neduet.edu.pk/examination_results')
        webpage = resp.content
    
    doc = html.fromstring(webpage)
    text = doc.xpath('//a[@id="Bachelors"]/parent::th')[0].text_content()
    table = doc.xpath('//table')[1]
    results_released = table.xpath(".//td[text() = '-'] | .//th[text() = '-']")
    EXAM = text.split('(')[1].split(')')[0].strip()

    payload = {'all_results_released' : len(results_released) <= 1, 'exam_name': EXAM.title()}

    if cache is not None:
        try:
            await cache.setex(GET_DETAILS_CACHE_KEY, GET_DETAILS_CACHE_TTL, json.dumps(payload))
        except Exception:
            pass

    return payload

@app.post("/check_results")
async def check_results(x_app_key: str | None = Header(default=None, alias="X-App-Key")):
    if x_app_key != os.getenv("SERVER_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden :(")

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
        if row != []: images.append(row)
    
    tasks = []
    users_to_update = []
    users = col.find({'notify': True})
    async for user in users:
        results = images[user['department']][user['year']]
        if results:
            tasks.append(send_email(user['email'], user['department'], user['year'], user['uniqueID'], user['examName'], attachment_urls = results))
            users_to_update.append(user['_id'])

    for i in range(0, len(tasks), 10):
        await asyncio.gather(*tasks[i:i+10])
        if i + 10 < len(tasks):
            await asyncio.sleep(1)

    if users_to_update:
        await col.update_many({'_id': {'$in': users_to_update}}, {'$set': {'notify': False}})
    return Response(status_code=200)

async def send_email(to_email, department, year, uniqueID, examName, attachment_urls = None, first_time = False):
    department = DEPTS[department]
    year = YEARS[year]

    msg = EmailMessage()
    msg['Subject'] = "NEDUET Results Confirmation" if first_time else f"{year} Year Results are Released!"
    msg['From'] = "ResultsBot <ned.resultnotifier@gmail.com>"
    msg['To'] = to_email

    if not first_time:
        msg.set_content(f"""
Hello, <br><br>

The results for the <b>Department of {department}, {year} Year</b> for the <b>{examName.title()}</b> have been officially released on the NEDUET website.
You can view your results from here (https://www.neduet.edu.pk/examination_results) or from the attachments provided.
<br><br>
If this tool was helpful for you, please feel free to star the repository over here (https://github.com/muhammadrafayasif/ned-result-notifier).<br>
Contributions of any kind are welcome and encouraged!
<br>
Congratulations and best of luck for your next steps!
<br><br>
Regards, <br>
ResultsBot
""", subtype="html")
    else:
        msg.set_content(f"""
Hello, <br><br>

You will be notified as soon as the results for the <b>Department of {department}, {year}</b> Year for the <b>{examName.title()}</b> are released officially on the NEDUET website. 
<br><br>
Feel free to star the repository over here (https://github.com/muhammadrafayasif/ned-result-notifier), all contributions are welcome! <br><br>
Accidentally chose the wrong details? Click <a href="https://neduet-result-notifier.vercel.app/user?id={uniqueID}">here</a> to remove yourself from the database <br><br>
Regards, <br>
ResultsBot
""", subtype="html")
    if attachment_urls:
        async with httpx.AsyncClient() as client:
            for n, url in enumerate(attachment_urls):
                full_url = "https://www.neduet.edu.pk" + url
                resp = await client.get(full_url)
                resp.raise_for_status()
                filename = f"{n+1}.{url.split('.')[-1]}"
                msg.add_attachment(
                    resp.content,
                    maintype="image",
                    subtype="jpeg",
                    filename=filename
                )

    await aiosmtplib.send(
        msg,
        hostname="smtp.gmail.com",
        port=587,
        start_tls=True,
        username="ned.resultnotifier@gmail.com",
        password=os.getenv("APP_KEY")
    )