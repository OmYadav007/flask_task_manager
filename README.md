# 📝 Flask Task Manager App 🚀

A simple **Task Manager** web application built using **Flask**, designed to help users **create, update, and delete tasks** efficiently. This app is **Dockerized** and ready for deployment on **AWS EC2**.

## 🌟 Features
- ✅ Add, update, and delete tasks
- ✅ Secure JWT-based authentication for login
- ✅ RESTful API for task management
- ✅ Dockerized for easy deployment

Instructions for Running the Application
# install requirements inside a python environment
pip install -r requirements.txt
# to run the application 
python app.py

#🐳 Running with Docker

docker build -t task_manager_web:latest 
docker run -p 8002:8002 task_manager_web:latest

#2️⃣ Pull and Run from Docker Hub
docker pull omyadav007/task_manager_app:latest
docker run -d -p 8002:8002 --name task_manager omyadav007/task_manager_app:latest





