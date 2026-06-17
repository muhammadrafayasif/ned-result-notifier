![Cron job status](https://api.cron-job.org/jobs/7053319/27d31be07bcfed44/status-7.svg)
[![Vercel](https://vercelbadge.vercel.app/api/muhammadrafayasif/ned-result-notifier)](https://neduet-result-notifier.vercel.app)

# NEDUET Result Notifier
This is a website that sends you an email whenever your respective department results are released officially.

## Tech Stack

### Frontend
![React](https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)

### Backend
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?logo=pandas&logoColor=white)
![SMTP](https://img.shields.io/badge/SMTP-0A66C2?logo=gmail&logoColor=white)

### Database
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?logo=mongodb&logoColor=white)

### Deployment
![Vercel](https://img.shields.io/badge/Vercel-000000?logo=vercel&logoColor=white)

## How does it work?
* Through the frontend, the user enters their details
* Those details are stored in the MongoDB database through a FastAPI endpoint (Sample entry: `{"email": EMAIL, "department": "DEPT", notify: true}`)
* Using `cron-jobs.org`, the FastAPI endpoint `/check_results` is called every minute
* When results are found, users are sent an email

## License
This project is released under the [MIT License](LICENSE).

Feel free to modify and adapt it for your institution or personal use.
