from email.message import EmailMessage
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pymongo, os, dotenv, smtplib
import requests as r
import pandas as pd
dotenv.load_dotenv()

client = pymongo.MongoClient(os.getenv("MONGODB_URL"))
db = client["users"]
col = db["users"]

class User(BaseModel):
    email : str
    department: str
    year: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://neduet-result-notifier.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/add")
def store_details(data : User):
    client = pymongo.MongoClient(os.getenv("MONGODB_URL"))
    db = client["users"]
    col = db["users"]
    if col.find_one({"email": data.email}): 
        raise HTTPException(409, "The following email already exists in the database.")
    else: 
        col.insert_one({"email": data.email, "department": data.department, "year": data.year, "notify": True})
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login("ned.resultnotifier@gmail.com", os.getenv("PASSWORD"))
            send_email(data.email, server, welcome=True)
        return Response(status_code=200)

@app.get("/check_results")
def check_results():
    webpage = r.get('https://www.neduet.edu.pk/examination_results').content
    df = pd.read_html(webpage)[1]
    df_ = df.astype(str).apply(lambda col: col.str.fullmatch("-", case=False, na=False)).any(axis=1)
    if (len(df[df_])): return Response(status_code=200, content="All results are already released.")
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login("ned.resultnotifier@gmail.com", os.getenv("PASSWORD"))
        for user in col.find({"notify": True}):
            status = df.iloc[int(user['department'])].iloc[int(user['year'])]
            if 'View' in status:
                try:
                    send_email(user['email'], server)
                    col.update_one(
                        {"_id": user["_id"]},
                        {"$set": {"notify": False}}
                    )
                except Exception as e:
                    print("Exception occurred: ", e)

    return Response(status_code=200)

def send_email(to_email: str, server, welcome: bool = False):
    msg = EmailMessage()
    msg["Subject"] = "NEDUET Results Notification"
    msg["From"] = "ned.resultnotifier@gmail.com"
    msg["To"] = to_email

    if not welcome: 
        msg.set_content("""
Hello,

The NEDUET results you were waiting for are now officially released.  
You can view your results from here (https://www.neduet.edu.pk/examination_results).

Congratulations and best of luck for your next steps!

Regards,  
NEDUET Results Bot
""")
    else:
        msg.set_content("""
Hello, 

You will be notified as soon as NEDUET results are released. 

Regards, 
NEDUET Results Bot
""")

    server.send_message(msg)