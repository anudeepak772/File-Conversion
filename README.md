# File-Conversion

Conversion of one format file to another is facilitated with the help of multiple workers co-ordinated with the help of the main server through a TCP
connection which uses SSL for further authentication.

---
## Functionality

1. Text-to-PDF Conversion.
2. PDF-to-Text Conversion.
## Components
[`client.py`](client.py) - User code that needs file to be converted.

[`server.py`](server.py) - Dispatcher that verifies itself and allocates workers.

[`scheduler.py`](scheduler.py) - Stores all the available workers.

[`worker_pdf_to_txt.py`](worker_pdf_To_txt.py) - Converts received pdf file to text

[`worker_txt_to_pdf.py`](worker_txt_To_pdf.py) - Converts received txt file to pdf
