# Quiz Master - V1 🎓

## 📌 Project Overview

**Quiz Master** is a multi-user quiz application built for exam preparation across multiple courses. It supports two primary roles — **Admin (Quiz Master)** and **Users (Students)** — and is developed as part of the **Modern Application Development - I** course using the Flask framework.

## 💠 Tech Stack

* **Backend:** Flask (Python)
* **Frontend:** HTML, CSS, Bootstrap, Jinja2 Templates
* **Database:** SQLite
* **Others:** Chart.js (optional), JavaScript (for form validation)

## 👥 Roles and Functionalities

### 👑 Admin (Quiz Master)

* No registration required; predefined in the database.
* Manage Users.
* Create, Edit, Delete:

  * Subjects
  * Chapters under each Subject
  * Quizzes under each Chapter
  * MCQ Questions under each Quiz
* Set quiz duration and date.
* Search for users, quizzes, subjects.
* View user attempt summaries and dashboard charts.

### 🧑‍🏫 Users (Students)

* Register and login.
* View available quizzes by subject and chapter.
* Attempt quizzes (optional timer supported).
* View score history and performance charts.

## 🧱 Database Models

* **User:** `id`, `email`, `password`, `full_name`, `qualification`, `dob`
* **Subject:** `id`, `name`, `description`
* **Chapter:** `id`, `subject_id`, `name`, `description`
* **Quiz:** `id`, `chapter_id`, `date_of_quiz`, `time_duration`, `remarks`
* **Question:** `id`, `quiz_id`, `question_text`, `option1`..`option4`, `correct_option`
* **Score:** `id`, `quiz_id`, `user_id`, `time_stamp`, `total_score`

> Note: All database tables are created programmatically using model definitions in Python.

## 📦 Folder Structure (Recommended)

```
/Quiz Master
├── main.py
├── quiz.sqlite3
├── req.txt
├── static/
│   └── css/
│       └── style.css
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── user_login.html
│   ├── user_register.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   ├── add_subject.html
│   ├── add_chapter.html
│   ├── add_quiz.html
│   ├── add_question.html
│   ├── take_quiz.html
│   ├── quiz_results.html
│   ├── user_dashboard.html
│   └── ... (others)
└── README.md
```

## 🚀 Getting Started

### Prerequisites

* Python 3.8+
* pip

### Installation

1. Clone the repository:

```bash
git clone https://github.com/21f3002527/Modern-Application-Development-1.git
cd quiz-master
```

2. Create a virtual environment and activate:

```bash
python -m venv venv
venv\Scripts\activate     # Windows
# or
source venv/bin/activate  # Mac/Linux
```

3. Install dependencies:

```bash
pip install -r req.txt
```

4. Run the app:

```bash
python main.py
```

## 📊 Optional Features Implemented

* Front-end enhancements using Bootstrap.
* Summary charts using Chart.js (or alternative JS libraries).
* Front-end form validation.
* Backend form validation.

## ✍️ Author

**Name:** Rajeev Kumar
**Email:** [21f3001527@ds.study.iitm.ac.in](mailto:21f3001527@ds.study.iitm.ac.in)
**GitHub:** [21f3002527](https://github.com/21f3002527)
**LinkedIn:** [rajeev245](https://www.linkedin.com/in/rajeev245/)

> 🔒 *This project was developed for academic purposes as part of the Modern Application Development I course.*
