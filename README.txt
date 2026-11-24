CivicPulse (Python server + SQLite database)

CHALANE KA TAREEKA
  1. Python 3 install karein (python.org) - koi pip install nahi chahiye
  2. start.bat double-click karein  (Mac/Linux: ./start.sh ya  python3 server.py)
  3. Terminal mein dikhega:  Server connected / Database connected / Tables list
  4. Browser mein http://localhost:3000 kholein - upar bhi Server: Connected / Database: Connected dikhega

DATABASE (civicpulse.db, SQLite) - tables schema.sql se apne aap ban jaati hain:
  users, admins, departments, categories, staff, complaints, complaint_history

LOGIN
  Citizen: koi bhi 10-digit mobile number, OTP nahi (demo: 9876543210)
  Admin:   ID admin / Password ROHIT   (admins table mein hashed save hota hai)
  Staff:   staff-login.html - ramesh / sunita / anil / vikram / deepak, Password: STAFF123 (staff table mein hashed)
           Staff login ke baad sirf apni assigned jobs dikhti hain.

Bina server sirf login.html khologe to browser storage use hota hai aur status 'Server: Offline' dikhata hai.
