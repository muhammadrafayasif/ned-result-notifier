from email.message import EmailMessage
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pymongo, os, dotenv, smtplib
import requests as r
import pandas as pd
dotenv.load_dotenv()

# CONSTANT
DEPTS = {'0': 'Architecture', '1': 'Physics', '2': 'Artificial Intelligence', '3': 'Computational Finance', '4': 'Computer Science', '5': 'Computer Science (TIEST)', '6': 'Cyber Security', '7': 'Data Science', '8': 'Development Studies', '9': 'Economics & Finance', '10': 'English Linguistics', '11': 'Gaming and Animation', '12': 'Chemistry', '13': 'Management Sciences', '14': 'Textile Sciences', '15': 'Automotive Engg.', '16': 'Bio-Medical Engg.', '17': 'Chemical Engg.', '18': 'Civil Engg.', '19': 'Civil Engg. (TIEST)', '20': 'Computer Systems Engg.', '21': 'Construction Engg.', '22': 'Electrical Engg.', '23': 'Electronics Engg.', '24': 'Food Engg.', '25': 'Industrial & Manufacturing Engg.', '26': 'Materials Engg.', '27': 'Mechanical Engg.', '28': 'Metallurgical Engg.', '29': 'Petroleum Engg.', '30': 'Polymer & Petrochemical Engg.', '31': 'Software Engg.', '32': 'Telecommunications Engg.', '33': 'Textile Engg.', '34': 'Urban Engg.'}
YEARS = {'1': '1st', '2': '2nd', '3': '3rd', '4': '4th', '5': '5th'}

# DB INITIALIZATION
client = pymongo.MongoClient(os.getenv("MONGODB_URL"))
db = client["users"]
col = db["users"]

# FASTAPI CODE
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
            send_email(data.email, server, data.department, data.year, welcome=True)
        return Response(status_code=200)
    
@app.get("/get_details")
def get_details():
    webpage = r.get('https://www.neduet.edu.pk/examination_results').content
    df = pd.read_html(webpage)[1]

    EXAM = list(df.columns)[0][0].split('(')[1][:-1]
    df_ = df.astype(str).apply(lambda col: col.str.fullmatch("-", case=False, na=False)).any(axis=1)
    return {'all_results_released' : len(df[df_]) <= 1, 'exam': EXAM}

@app.get("/check_results")
def check_results():
    webpage = r.get('https://www.neduet.edu.pk/examination_results').content
    df = pd.read_html(webpage)[1]
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login("ned.resultnotifier@gmail.com", os.getenv("PASSWORD"))
        for user in col.find({"notify": True}):
            status = df.iloc[int(user['department'])].iloc[int(user['year'])]
            if 'View' in status:
                try:
                    send_email(user['email'], server, user['department'], user['year'])
                    col.delete_one(
                        {"_id": user["_id"]}
                    )
                except Exception as e:
                    print("Exception occurred: ", e)

    return Response(status_code=200)

def send_email(to_email, server, department, year, welcome = False):
    msg = EmailMessage()
    msg["Subject"] = "NEDUET Results Notification"
    msg["From"] = "ned.resultnotifier@gmail.com"
    msg["To"] = to_email

    department = DEPTS[department]
    year = YEARS[year]

    if not welcome:
        msg.set_content(f"""
Hello,

The results for the Department of {department}, {year} Year have been officially released on the NEDUET website.
You can view your results from here (https://www.neduet.edu.pk/examination_results).

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

    server.send_message(msg)