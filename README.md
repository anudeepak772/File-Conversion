# File-Conversion

Conversion of one format file to another is facilitated with the help of multiple workers coordinated with the help of the main server through a TCP connection which uses SSL for further authentication.

---

## Functionality

1. Text-to-PDF Conversion
2. PDF-to-Text Conversion

---

## Components

1. **client.py** – User code that needs file to be converted
2. **server.py** – Dispatcher that verifies itself and allocates workers
3. **scheduler.py** – Stores all the available workers
4. **worker_pdf_to_txt.py** – Converts received PDF file to text
5. **worker_txt_to_pdf.py** – Converts received TXT file to PDF

---

## ⚙️ Setup Steps

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/File-Conversion.git
cd File-Conversion

#Install required libraries
pip install reportlab PyPDF2

#Generate SSL Certificate and Key
openssl req -new -x509 -days 365 -nodes -out server.crt -keyout server.key

# Start the server
python server.py

# Start the scheduler
python scheduler.py

# Run the client
python client.py

usage
Run the server and scheduler first
Run the client
Enter:
File path (e.g., test.txt)
Target format (pdf or txt)
The converted file will be returned to the client
